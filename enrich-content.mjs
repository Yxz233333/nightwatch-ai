import {readFileSync,writeFileSync,existsSync,renameSync} from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),file=path.join(root,'public/content.json'),cacheFile=path.join(root,'data/enrichment.json');
const cache=existsSync(cacheFile)?JSON.parse(readFileSync(cacheFile,'utf8')):{};const content=JSON.parse(readFileSync(file,'utf8'));
const key=readFileSync('C:/Users/Ye_xz/.codex/credentials/deepseek/api-key.txt','utf8').trim();
const pending=content.articles.filter(a=>!cache[a.id]);const batches=[];for(let i=0;i<pending.length;i+=4)batches.push(pending.slice(i,i+4));
let cursor=0,done=0,errors=0;
async function worker(){while(cursor<batches.length){const batch=batches[cursor++];let ok=false;for(let attempt=0;attempt<3&&!ok;attempt++){try{
const response=await fetch('https://api.deepseek.com/chat/completions',{method:'POST',signal:AbortSignal.timeout(110000),headers:{'content-type':'application/json',authorization:'Bearer '+key},body:JSON.stringify({model:'deepseek-flash',thinking:{type:'disabled'},temperature:0.15,max_tokens:6500,response_format:{type:'json_object'},messages:[{role:'system',content:'你是严谨的中文科技编辑。只依据提供的原题、摘要和已有简介，不能引入外部事实或把论文结论说成已获独立验证。对每个id输出titleZh：专业准确的中文译题，保留人名/数学符号；overview：120至220字中文通俗介绍，说明具体研究对象、作者声称结果和研究意义，若材料不足则80字且明确不足；keyPoints：2至3个具体中文要点，每项20至60字，仅从原文提炼；field：最合适的既有类别，确需新领域才新增。新闻已是中文时保留原题，不编造数字、价格、推出范围、研究证明细节、同行审查或个人使用结论。论文使用“稿件提出/作者声称/摘要表示”描述。返回JSON对象 {"items":[{"id":"...","titleZh":"...","overview":"...","keyPoints":["..."],"field":"..."}]}，覆盖每个输入id。'}, {role:'user',content:JSON.stringify(batch.map(a=>({id:a.id,title:a.title,abstract:a.abstractEnglish||'',summary:a.summary,status:a.status,category:a.category,section:a.section}))) }]})});
if(!response.ok)throw Error('HTTP '+response.status);const result=await response.json();const rows=JSON.parse(result.choices[0].message.content).items;
if(!Array.isArray(rows)||rows.length!==batch.length)throw Error('条目数不符');
for(const a of batch){const r=rows.find(r=>r.id===a.id);if(!r||!/[\u3400-\u9fff]/.test(r.titleZh)||r.overview.length<45||!Array.isArray(r.keyPoints)||r.keyPoints.length<2)throw Error('内容校验失败');}
for(const r of rows)cache[r.id]=r;writeFileSync(cacheFile,JSON.stringify(cache,null,2));done+=batch.length;ok=true;console.log('已整理 '+done+'/'+pending.length);
}catch(e){if(attempt===2){errors+=batch.length;console.log('批次失败 '+batch.map(a=>a.id).join(',')+' '+e.message);}}}}}
await Promise.all(Array.from({length:6},worker));
const current=JSON.parse(readFileSync(file,'utf8'));for(const a of current.articles){const r=cache[a.id];if(!r)continue;if(a.section==='papers'){a.titleEn=a.titleEn||a.title;a.titleZh=r.titleZh;a.category=r.field||a.category;}a.details={overview:r.overview,keyPoints:r.keyPoints,editorialNote:'根据所链接原始材料整理，中文为辅助阅读，请以原文为准。'};}
current.updatedAt=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Shanghai'}).replace(' ','T')+'+08:00';writeFileSync(file+'.tmp',JSON.stringify(current,null,2)+'\n');renameSync(file+'.tmp',file);console.log(JSON.stringify({completed:done,errors,total:current.articles.length}));if(errors)process.exitCode=1;

