import re,json,hashlib,html,base64
from pathlib import Path
from datetime import datetime,timezone,timedelta
root=Path(__file__).parent
articles=[]
def add(section,category,title,summary,url,date=None,status='',**extra):
    key=hashlib.sha256((section+'|'+url+'|'+title).encode()).hexdigest()[:16]
    articles.append(dict(id=key,section=section,category=category,title=title,summary=summary,url=url,date=date,status=status,**extra))
notes='https://help.openai.com/en/articles/6825453-chatgpt-release-notes'
for date,title,summary in [
('2026-10-16','ChatGPT 支持协作制作幻灯片','可以从对话、文件或提纲制作演示，并在 Space 中协作修改和导出。'),
('2026-10-16','GPT-6 Pro 更新工具使用与并行能力','官方公布响应速度、工具调用与多代理任务能力的更新。'),
('2026-10-15','语音上线 GPT-Live-1.1 与新声音','语音模型和多语言声音选项更新，具体可用项因账户与地区而异。'),
('2026-10-15','Sites 取消固定创建数量上限','使用量和存储限制仍然适用。'),
('2026-10-07','GPT-6 与交互式回答界面','回答可组合文字、图像和可交互工具，并在继续思考时逐步展示结果。'),
('2026-10-06','ChatGPT 支持音频文件上传','上传录音后可转写、总结和提问；转写结果仍需核对。'),
('2026-10-01','手机相机支持连续扫描文档','iOS 逐步开放多页扫描并自动合并 PDF。'),
('2026-09-29','Codex Cloud 跨设备继续编码任务','使用隔离云端工作区，可在本机休眠时继续执行任务。')]:
    add('codex' if 'Codex' in title else 'chatgpt','功能更新',title,summary,notes,date,'官方已宣布；账户、套餐、客户端和灰度范围以原文为准。')
add('codex','功能更新','输入框预测：Tab 接受下一条提示建议','测试版可在输入框建议后续消息，接受后仍需自行发送。',notes,'2026-10-09','Beta；符合条件的成年个人 Pro 用户，需最新桌面版和受支持模型。')
releases=json.loads((root/'data/codex-releases.json').read_text(encoding='utf-8-sig'))
stable=next(r for r in releases if not r['prerelease'])
for title,summary in [
('使用 /config 搜索并修改偏好','支持跨分类搜索设置，并区分立即生效和需要重启的修改。'),
('任务执行中发送跟进指令','运行期间可继续发送要求来调整方向；中断也会停止活动代码单元与嵌套工具。'),
('自定义 /keymap 前导键','可配置快捷键前导键，默认 Ctrl+X；语音静音使用 F9。'),
('通过 /daemon 重启后台服务','重启前提示可能受影响的工作，完成后自动重新连接。'),
('独立只读工具并行执行','查询技能、记忆和会话历史等独立只读调用可以并行。')]:
    add('codex','功能更新','Codex CLI '+stable['name']+'：'+title,summary,stable['html_url'],stable['published_at'][:10],'这是 CLI 发布说明；桌面版是否包含同项能力需单独核对。')
for r in releases:
    if r['prerelease'] and r!=releases[0]:continue
    add('codex','功能更新','Codex CLI '+r['name']+(' 测试版发布' if r['prerelease'] else ' 发布'), '官方已发布该版本，修复和详细变化见原始发布说明。',r['html_url'],r['published_at'][:10],'预发布版本不代表稳定版已普及。' if r['prerelease'] else 'CLI 稳定版本。')
news=[
('模型动态','Gemini 4 Argon 开始向 Pro 与 Ultra 推送','Google 在 10 月 13 日发布说明中宣布新模型，面向复杂任务。','https://gemini.google/release-notes/','2026-10-13',True),
('工具动态','Gemini macOS 集成 Antigravity 编程代理','可从聊天发起代码与原型任务，代理在后台构建和测试。','https://gemini.google/release-notes/','2026-10-13',False),
('工具动态','Gemini 自定义入口整合技能与应用连接','集中管理响应方式、技能和应用连接；可用地区与语言有所不同。','https://gemini.google/release-notes/','2026-10-13',False),
('工具动态','Gemini Skills 逐步替代 Gems','支持保存和组合任务指令，迁移方式以官方说明为准。','https://gemini.google/release-notes/','2026-09-30',False),
('行业新闻','Anthropic 更新 2026 使用政策','官方解释政策调整及模型能力变化带来的使用边界。','https://www.anthropic.com/news/2026-usage-policy-update',None,False),
('行业新闻','Claude 参与新型酶系统发现','Anthropic 发布生命科学研究进展，介绍通用 AI 辅助发现的实验。','https://www.anthropic.com/news/claude-discovers-novel-enzyme-system',None,True),
('行业新闻','OpenAI 公开数学成果与验证材料','官方数学仓库公开手稿、部分 Lean 证明及相关说明。','https://openai.com/index/sharing-ai-progress-in-mathematics/','2026-10-06',True),
('行业新闻','OpenAI 支持数学界审查与理解 AI 成果','10 月 15 日更新宣布向 Simons Foundation 相关计划投入资金，支持研究与交流。','https://openai.com/index/sharing-ai-progress-in-mathematics/','2026-10-15',False)]
for category,title,summary,url,date,recommended in news:add('news',category,title,summary,url,date,'官方来源；研究成果的审查状态请继续关注原始材料。' if '数学' in title else '',recommended=recommended,recommendedOn='2026-10-18' if recommended else None)
text=(root/'data/math-contents.md').read_text(encoding='utf-8')
seen=set()
for match in re.finditer(r'&emsp;\[([^\]]+)\]\((preprints/[^)]+\.pdf)\)\s*\n(.*?)(?=</td>)',text,re.S):
    title,relative,abstract=match.groups()
    if relative in seen:continue
    seen.add(relative)
    abstract=html.unescape(re.sub('<[^>]+>','',abstract)).strip()
    category='数学论文'
    for pattern,label in [(r'Selmer|elliptic|Birch|arithmetic|prime|number|Diophant|L-function','数论与算术几何'),(r'Navier|fluid|PDE|differential|wave|heat','偏微分方程'),(r'graph|combinat|Ramsey|color|chromatic|distance','组合数学与图论'),(r'algebra|Hodge|variet|cohomolog|motive|scheme','代数几何'),(r'probab|random|stochastic|percolat','概率论'),(r'topolog|manifold|knot|homotop','几何与拓扑'),(r'comput|complexity|algorithm|circuit','理论计算机科学')]:
        if re.search(pattern,title,re.I):category=label;break
    date=None
    dm=re.search(r'(October|September|August)-(\d+)-2026',relative)
    if dm:date='2026-%02d-%02d'%({'October':10,'September':9,'August':8}[dm.group(1)],int(dm.group(2)))
    add('papers',category,html.unescape(title),'OpenAI 数学仓库收录的研究手稿。展开查看英文摘要，或标记后让我进一步解释。','https://github.com/openai/math/blob/main/'+relative,date,'AI 产生的研究手稿；收录不表示已完成独立审查或同行评议。',abstractEnglish=abstract,sourceRepository='https://github.com/openai/math',license='Apache-2.0')
articles.sort(key=lambda a:(a['date'] or '',a['id']),reverse=True)
payload=dict(updatedAt=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),coverage='首轮：官方近期功能更新、精选行业资讯，以及 OpenAI 数学仓库全部可解析 PDF 手稿目录。论文保留英文原题与摘要；后续持续补充中文解读。',articles=articles)
(root/'public/content.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(root/'THIRD_PARTY_NOTICES.md').write_text('# 第三方资料\n\n数学论文目录、英文原题和摘要来自 OpenAI math 仓库，依据 Apache-2.0 转载；中文分类及页面展示由本项目整理。原始资料及更新：https://github.com/openai/math 。所有成果状态以原始论文与独立审阅为准。\n',encoding='utf8')
(root/'OPENAI_MATH_LICENSE.txt').write_bytes(base64.b64decode((root/'data/math-license.b64').read_text(encoding='utf-8-sig')))
from collections import Counter
print(json.dumps(dict(total=len(articles),sections=dict(Counter(a['section'] for a in articles))),ensure_ascii=True))
