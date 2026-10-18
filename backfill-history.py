# -*- coding: utf-8 -*-
"""Merge dated primary-source archives without changing existing article IDs or user data.

Raw source snapshots stay in ignored data/. Run collectors before this script.
"""
import json,re,hashlib,html,gzip,glob
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT=Path(__file__).parent
D=ROOT/'data'
FILE=ROOT/'public/content.json'
content=json.loads(FILE.read_text(encoding='utf8'))
original={a['id'] for a in content['articles']}
(D/'content-before-history.json').write_text(json.dumps(content,ensure_ascii=False),encoding='utf8') if not (D/'content-before-history.json').exists() else None
articles=content['articles']; seen={(a['section'],a.get('sourceRecordKey')or a['url'].rstrip('/')) for a in articles if a['section']=='news'}
source_counts={}; rejected=[]
START='2025-09-01'; END='2026-10-19'; TZ=timezone(timedelta(hours=8))
def clean(s):return re.sub(r'\s+',' ',BeautifulSoup(s or '', 'html.parser').get_text(' ',strip=True)).strip()
def date_info(value):
    if not value:return None,None
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:
        try:d=parsedate_to_datetime(value)
        except Exception:
            for fmt in ['%B %d, %Y','%b %d, %Y']:
                try:return datetime.strptime(value.strip(),fmt).strftime('%Y-%m-%d'),None
                except ValueError:pass
            return None,None
    if not d.tzinfo:return d.strftime('%Y-%m-%d'),None
    return d.astimezone(TZ).strftime('%Y-%m-%d'),d.isoformat()
def add(section,title,summary,url,published,source,category=None,status='',body='',extra=None):
    date,stamp=date_info(published)
    if not date or not START<=date<=END:return
    title=clean(title); summary=clean(summary)
    if not title:return
    record_key=url.rstrip('/')+'|'+title+'|'+date if source=='Gemini 官方发布说明' else url.rstrip('/')
    if section=='news' and (section,record_key) in seen:
        for a in articles:
            if a['section']==section and a['url'].rstrip('/')==url.rstrip('/') and not a.get('date'):
                a['date']=date
                if stamp:a['publishedAt']=stamp
        return
    key=hashlib.sha256((section+'|'+url+'|'+title).encode()).hexdigest()[:16]
    if any(a['id']==key for a in articles):return
    if not category:
        category='工具动态' if re.search(r'\b(app|sdk|tool|cli|code|coding|agent|studio|library|inference)\b',title,re.I) else ('模型动态' if re.search(r'\b(model|gemini|claude|gpt|llama|qwen|deepseek)\b',title,re.I) else '行业新闻')
    a=dict(id=key,section=section,category=category,title=title,summary=summary or title,url=url,date=date,status=status or '依据官方原始发布记录整理；当时的推出范围和限制请以原文为准。',source=source)
    if stamp:a['publishedAt']=stamp
    if body:a['sourceText']=clean(body)[:7000]
    if extra:a.update(extra)
    if source=='Gemini 官方发布说明':a['sourceRecordKey']=record_key
    if section=='codex' and extra and len(a.get('sourceText',''))<100:
        channel='测试版' if extra.get('releaseChannel')=='prerelease' else '稳定版'
        a['titleZh']=title
        a['summary']='Codex CLI '+channel+'版本发布；官方记录未列出详细的功能变更。'
        a['details']={'overview':title+'。该条官方 GitHub 发布记录只给出版本标识，没有列出可供核实的具体新增功能或修复。这里保留其发布时间和原始发布链接，方便追溯版本历史；不能据此推断桌面端已经具备某项能力。','keyPoints':['发布渠道：'+channel,'该条发布记录未提供详细变更清单'],'editorialNote':'仅整理该版本实际发布记录，不根据版本号推测功能。'}
        a.pop('sourceText',None)
    articles.append(a);seen.add((section,record_key));source_counts[source]=source_counts.get(source,0)+1

# ChatGPT help-center DOM: dated H1 groups, individual H2 updates, and nested headings.
nodes=json.loads((D/'chatgpt-dom.json').read_text(encoding='utf8'))
current_date=None;entry=None;paragraphs=[]
def flush():
    if not entry or not current_date or not paragraphs:return
    title=entry['text'];section='codex' if re.search(r'\bcodex\b',title,re.I) else 'chatgpt'
    # A release note announces the update, even when it is a beta or a rollout.
    add(section,title,' '.join(paragraphs)[:700],'https://help.openai.com/en/articles/6825453-chatgpt-release-notes#'+entry['id'],current_date,'ChatGPT 官方发布说明','功能更新',body=' '.join(paragraphs))
for n in nodes:
    if n['tag']=='H1':
        flush();paragraphs=[];current_date=date_info(n['text'])[0]
        entry={'text':'ChatGPT 更新：'+n['text'],'id':n['id']} if current_date else None
    elif n['tag']=='H2':
        flush();entry=n;paragraphs=[]
    elif entry and n['text'] and n['text'] not in paragraphs:
        # Lists include their child paragraphs: keep each textual sentence once.
        if not any(n['text'] in p for p in paragraphs):paragraphs.append(n['text'])
flush()

# The separate desktop/mobile/cloud changelog contains changes absent from Help Center.
changelog=D/'codex-changelog-lines.txt'
if changelog.exists():
    groups=[];group=None
    for line in changelog.read_text(encoding='utf8').splitlines():
        n,_,text=line.partition('\t')
        if not n.isdigit() or int(n)<930:continue
        text=re.sub(r'cite[^†]*†(.*?)',r'\1',text)
        m=re.match(r'\* (202\d-\d\d-\d\d)$',text)
        if m:
            if group:groups.append(group)
            group={'date':m.group(1),'title':None,'body':[]}
        elif group:
            if text.startswith('### ') and not group['title']:group['title']=text[4:]
            elif text and not text.startswith('## '):group['body'].append(text)
    if group:groups.append(group)
    for g in groups:
        if not g['title']:continue
        title=g['title'];body=' '.join(g['body'])
        section='chatgpt' if re.search(r'ChatGPT for iOS|ChatGPT desktop|Appshots|Pets',title,re.I) and not re.search(r'Codex',title,re.I) else 'codex'
        category='功能预告' if re.search(r'will retire|retires .* on|will be retired',body[:700],re.I) and not re.search(r'Effective|deprecated on',body[:200],re.I) else '功能更新'
        add(section,title,body[:700],'https://learn.chatgpt.com/docs/changelog',g['date'],'ChatGPT 与 Codex 官方变更日志',category,body=body)

for name,source,base in [('deepseek-updates.html','DeepSeek 官方更新','https://api-docs.deepseek.com/updates/'),('gemini-notes.html','Gemini 官方发布说明','https://gemini.google/release-notes/')]:
    if not (D/name).exists():continue
    s=BeautifulSoup((D/name).read_text(encoding='utf8'),'html.parser')
    date=None;entry=None;paras=[]
    def flush_vendor():
        if not entry or not date:return
        title=entry.get_text(' ',strip=True).replace('\u200b','');body=' '.join(paras)
        add('news',title,body[:700],base+('#'+entry['id'] if entry.get('id') else ''),date,source,body=body)
    for n in s.select('h2,h3,p,ul,ol'):
        if n.name=='h2':
            flush_vendor();entry=None;paras=[]
            m=re.search(r'(202\d)[.-](\d\d)[.-](\d\d)',n.get_text());date='-'.join(m.groups()) if m else None
        elif n.name=='h3':flush_vendor();entry=n;paras=[]
        elif entry and n.get_text(' ',strip=True):
            txt=n.get_text(' ',strip=True)
            if not any(txt in p for p in paras):paras.append(txt)
    flush_vendor()

# GitHub release archives, retaining both stable and prerelease chronology.
for p in sorted(D.glob('codex-history-*.json')):
    rows=json.loads(p.read_text(encoding='utf-8-sig'))
    for r in rows:
        pre=r.get('prerelease',False); name=r.get('name') or r['tag_name'];body=r.get('body') or ''
        add('codex','Codex CLI '+name+(' 测试版发布' if pre else ' 发布'),clean(body)[:700] or '官方发布该版本；此版本没有提供详细变更摘要。',r['html_url'],r['published_at'],'Codex GitHub Releases','功能更新','已发布的测试版本，不代表稳定版已开放。' if pre else 'CLI 稳定版本；桌面端功能另以对应公告为准。',body=body,extra={'releaseChannel':'prerelease' if pre else 'stable'})

def feed(text,source):
    try:r=ET.fromstring(text)
    except Exception:return
    for item in r.findall('.//item'):
        title=item.findtext('title');url=item.findtext('link');published=item.findtext('pubDate');desc=item.findtext('description')or''
        if not url:continue
        if source=='NVIDIA 官方博客' and re.search(r'GeForce NOW',str(title),re.I) and not re.search(r'\bAI\b|artificial intelligence|neural|generative|machine learning',str(title),re.I):continue
        # NVIDIA's official blog includes some non-AI material; retain AI / GPU ecosystem news.
        if source=='NVIDIA 官方博客' and not re.search(r'ai|nvidia|gpu|robot|cuda|rtx|data center',str(title)+' '+clean(desc),re.I):continue
        add('news',title,clean(desc)[:700],url,published,source,body=clean(desc)[:5000])
for name,source in [('source-2.txt','OpenAI 官方新闻'),('source-4.txt','Google DeepMind'),('source-5.txt','Hugging Face 官方博客'),('source-6.txt','NVIDIA 官方博客'),('google-ai.txt','Google AI 官方博客')]:
    if (D/name).exists():feed((D/name).read_text(encoding='utf8'),source)

# Each archived page supplies its own original publication time, never sitemap lastmod.
url_map={}
for name in ['anthropic-map.txt','deepmind-map.txt']:
    b=(D/name).read_bytes();b=gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b
    for n in ET.fromstring(b).iter():
        if n.tag.endswith('loc'):url_map[hashlib.sha256(n.text.encode()).hexdigest()]=n.text
for i in range(2,161):
    u='https://blogs.nvidia.com/feed/?paged='+str(i);url_map[hashlib.sha256(u.encode()).hexdigest()]=u
for p in (D/'archive-pages').glob('*.html'):
    u=url_map.get(p.stem)
    if not u:continue
    text=p.read_text(encoding='utf8')
    if '/feed/' in u:feed(text,'NVIDIA 官方博客');continue
    s=BeautifulSoup(text,'html.parser')
    def meta(k):
        n=s.find('meta',attrs={'property':k})or s.find('meta',attrs={'name':k});return n.get('content') if n else None
    title=s.find('h1');title=title.get_text(' ',strip=True) if title else meta('og:title')
    published=meta('article:published_time') or meta('datePublished')
    if not published:
        t=s.find('time');published=(t.get('datetime')or t.get_text(' ',strip=True)) if t else None
    if not published:
        for script in s.find_all('script',type='application/ld+json'):
            m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',script.text)
            if m:published=m.group(1);break
    date,_=date_info(published)
    if not date or not START<=date<=END:continue
    main=s.find('article')or s.find('main')or s
    body=' '.join(x.get_text(' ',strip=True) for x in main.find_all('p'))
    summary=meta('description')or meta('og:description')or body[:700]
    add('news',title,summary,u,published,'Anthropic 官方新闻与研究' if 'anthropic.com' in u else 'Google DeepMind',body=body)

# Resolve the original importer's parenthesis-in-path omission, without changing old IDs.
math=(D/'math-contents.md').read_text(encoding='utf8')
for m in re.finditer(r'&emsp;\[(.*?)\]\((preprints/.*?\.pdf)\)\s*\n(.*?)(?=</td>)',math,re.S):
    title,url,abstract=m.groups();url='https://github.com/openai/math/blob/main/'+url
    if any(a['url']==url for a in articles):continue
    dt=re.search(r'([A-Za-z]+)-(\d{1,2})-(202\d)',url)
    if not dt:continue
    pub=' '.join(dt.groups()[:2])+', '+dt.group(3)
    add('papers',html.unescape(title),clean(abstract),url,pub,'OpenAI 数学仓库','其他数学','AI 产生的研究手稿；收录不表示已完成独立审查或同行评议。',extra={'titleEn':html.unescape(title),'abstractEnglish':clean(abstract)})

add('papers','Early science acceleration experiments with GPT-5','OpenAI 与多所高校及实验室合作的案例研究，涵盖组合数学、数论、优化、物理及生物学。报告记录专家如何利用 GPT-5 提出思路、检索文献与验证猜想，也记录错误和归因问题。','https://openai.com/index/accelerating-science-gpt-5/','2025-11-20','OpenAI 官方研究','AI 辅助数学研究','这是跨学科案例研究，不是对模型科研成功率的系统抽样；数学结果仍需逐项检查。',extra={'titleEn':'Early science acceleration experiments with GPT-5'})
add('papers','First Proof?','OpenAI 公布针对十道研究级数学问题的证明尝试。稿件涵盖分析、数论、组合、拓扑与数值计算等方向，模型产生的证明不能直接视为全部正确。官方后续说明问题 2 的尝试不正确，其他尝试的审核状态需结合后续专家评论。','https://cdn.openai.com/pdf/a430f16e-08c6-49c7-9ed0-ce5368b71d3c/1stproof_oai.pdf','2026-02-13','OpenAI 官方研究','AI 辅助数学研究','日期采用 PDF 首页的 2026-02-13；证明尝试的正确性以专家核验及后续修订为准。',extra={'titleEn':'First Proof?'})

add('news','Introducing Agent Skills','Claude 推出由说明、脚本及资源组成的 Skills，可按需载入并用于 Claude 应用、Claude Code 与 API。原公告发表于 2025-10-16；页面还包含 2025-12-18 的后续更新，不能把后加内容当成首发时已有。','https://claude.com/resources/articles/skills','2025-10-16','Anthropic 官方迁移归档','工具动态')
add('news','Anthropic Education Report: The AI Fluency Index','研究用 2026 年 1 月一周内的 9,830 段多轮 Claude 对话，观察 11 项 AI 协作行为。结果体现迭代与评估行为之间的相关性，不代表因果关系，也不能直接外推所有 AI 用户。','https://academy.claude.com/tutorials/the-ai-fluency-index','2026-02-23','Anthropic 官方迁移归档','行业新闻')

for a in articles:
    if not a.get('date'):
        m=re.search(r'/(?:[^/]*-)?(202\d-\d\d-\d\d)/paper.pdf$',a['url'])
        if m:a['date']=m.group(1)
    if a.get('releaseChannel') and not re.search(r'CLI (?:\d|rust-v)',a['title']):
        a['title']=a['title'].replace('Codex CLI ','Codex 仓库组件：',1)
        if a.get('titleZh'):a['titleZh']=a['titleZh'].replace('Codex CLI ','Codex 仓库组件：',1)

# Explicit editorial research selection. Product releases and funding news are not automatically breakthroughs.
selected={'/alphagenome-atlas-':'AI 生命科学','/accelerating-mathematical-and-scientific-discovery-':'AI 数学研究','/first-proof-submissions':'AI 数学研究','/accelerating-science-gpt-5':'AI 科研协作','/model-disproves-discrete-geometry-conjecture':'AI 数学研究','/ten-advances-in-mathematics':'AI 数学研究','/riemann-zeta':'AI 数学研究'}
for a in articles:
    if a['section']=='news':
        for part,field in selected.items():
            if part in a['url']:a['breakthrough']=True;a['breakthroughField']=field

assert original.issubset({a['id'] for a in articles})
assert len({a['id'] for a in articles})==len(articles)
articles.sort(key=lambda a:(a.get('date')or'',a['id']),reverse=True)
content['updatedAt']=datetime.now(TZ).isoformat(timespec='seconds')
content['coverage']={'requestedFrom':START,'requestedThrough':END,'scope':'已核实官方发布说明、GitHub Releases、官方 RSS 与新闻研究归档；不是全网穷尽清单。','historyAddedBySource':source_counts}
content['coverage']['sourceCounts']={}
for a in articles:
    source=a.get('source','此前已核实内容');content['coverage']['sourceCounts'][source]=content['coverage']['sourceCounts'].get(source,0)+1
fetch_report=D/'archive-fetch-report.json'
if fetch_report.exists():
    failed=[r['url'] for r in json.loads(fetch_report.read_text(encoding='utf8')) if not r['ok']]
    content['coverage']['retrievalNotes']={'httpFetchFailures':failed,'resolvedViaOfficialRedirects':['https://www.anthropic.com/news/skills','https://www.anthropic.com/research/AI-fluency-index'],'outsideRequestedPeriod':['https://www.anthropic.com/news/fine-tune-claude-3-haiku'],'notExhaustivelyArchived':['Microsoft','Meta','国内厂商除 DeepSeek 及已收录的 Hugging Face 官方文章外的完整自有归档']}
candidate=D/'history-candidate.json'
tmp=candidate.with_suffix('.tmp');tmp.write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(candidate)
report={'total':len(articles),'originalIDsRetained':len(original),'added':len(articles)-len(original),'bySource':source_counts,'byMonth':{}}
for a in articles:
    month=(a.get('date')or'undated')[:7];report['byMonth'].setdefault(month,{});sec=a['section'];report['byMonth'][month][sec]=report['byMonth'][month].get(sec,0)+1
(D/'history-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
