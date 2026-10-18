# -*- coding: utf-8 -*-
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
p=Path(__file__).parent/'public/content.json';c=json.loads(p.read_text(encoding='utf8'))
selected={'42015c1d1c6e7a6a','b9b12d19fb88be55','b16fa58aaf55a647','ff9438e4483571d5'}
for a in c['articles']:
 if a['id'] in selected:a['breakthrough']=True;a['breakthroughField']='AI 与数学'
 # Previously recommended historical news must not be presented as a new day's news.
 if a['section']=='news' and a.get('recommended') and a.get('date')!='2026-10-18':a['recommended']=False;a.pop('recommendedOn',None)
def add(title,date,url,summary,overview,points,status,field):
 key=hashlib.sha256(('news|'+url+'|'+title).encode()).hexdigest()[:16]
 if any(a['id']==key for a in c['articles']):return
 c['articles'].append(dict(id=key,section='news',category='行业新闻',title=title,date=date,url=url,summary=summary,status=status,recommended=False,breakthrough=True,breakthroughField=field,details=dict(overview=overview,keyPoints=points,editorialNote='依据官方原始材料整理，研究结果的验证程度以原文为准。')))
add('Google Antigravity 辅助发现抗菌肽候选','2026-10-15','https://deepmind.google/blog/accelerating-antimicrobial-discovery/','AI 协助跨数据库筛选与结构分析，找到等待湿实验验证的抗菌肽候选。','Google DeepMind 的技术案例介绍，研究人员借助 Antigravity 编排数据库查询、蛋白质结构分析与文献梳理，识别新的抗菌肽候选。其价值在于把分散的研究工作集中在协作流程中；案例中的候选仍需湿实验验证，不能等同于已证实有效的药物。',['结合数据库、结构和基因组信息提出候选。','研究人员指导科学目标，代理执行跨工具分析。','候选进入湿实验验证阶段，实际效力尚待实验。'],'研究方法与候选发现进展；尚非完成验证的治疗方案。','AI 与生命科学')
add('OpenAI 公布 Navier–Stokes 问题解答研究','2026-09-08','https://openai.com/index/navier-stokes-solution/','官方公布内部模型提出的流体方程证明与 Lean 形式化材料。','OpenAI 发布关于 Navier–Stokes 存在性与光滑性问题的研究，表示内部模型构造了有限时间出现奇点的证明，并提供论文和 Lean 形式化材料。这是重大数学问题的研究报告，应结合原文及独立数学审查理解其范围。',['研究对象是流体方程解的光滑性。','官方提供书面证明与形式化验证材料。','区分模型提出的证明、形式化检查与数学界独立审查。'],'官方研究报告；不将其描述为已获得千禧年大奖或已经完成全部独立审查。','AI 与数学')
c['updatedAt']=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(p)
print('breakthrough entries:',sum(a.get('breakthrough',False) for a in c['articles']))
