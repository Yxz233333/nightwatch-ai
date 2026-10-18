import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
import {filterArticles,paginate,beijingToday} from './public/view-model.js';
const file=process.argv[2]||'public/content.json';
const content=JSON.parse(readFileSync(file,'utf8')),articles=content.articles;
assert.equal(new Set(articles.map(a=>a.id)).size,articles.length,'重复编号');
const baseline='data/content-before-history.json';
if(existsSync(baseline)){
 for(const old of JSON.parse(readFileSync(baseline,'utf8')).articles){
  const current=articles.find(a=>a.id===old.id);assert(current,'丢失旧编号 '+old.id);
  assert.equal(current.url,old.url,'原文链接被改写 '+old.id);
  if(old.date)assert.equal(current.date,old.date,'原发布日期被覆盖 '+old.id);
 }
}
for(const a of articles){
 assert(/^[a-f0-9]{16}$/.test(a.id));assert(['chatgpt','codex','news','papers'].includes(a.section));
 assert(a.date&&/^\d{4}-\d{2}-\d{2}$/.test(a.date),'缺少真实日期 '+a.id);
 assert(a.date>='2025-09-01'&&a.date<=content.coverage.requestedThrough,'超出归档日期 '+a.id);
 assert.equal(new URL(a.url).protocol,'https:');
 assert(a.details?.overview&&a.details.keyPoints?.length>=2,'缺少详情 '+a.id);
 assert(!a.sourceText,'不应发布采集原文 '+a.id);
 if(a.section==='papers')assert(/[\u3400-\u9fff]/.test(a.titleZh)&&a.titleEn,'论文中英标题不全 '+a.id);
 if(a.publishedAt)assert.equal(beijingToday(new Date(a.publishedAt)),a.date,'源时区转换错误 '+a.id);
}
const months=[];for(let y=2025,m=9;y<2026||m<=10;){months.push(`${y}-${String(m).padStart(2,'0')}`);if(++m===13){m=1;y++;}}
const bySection={};for(const section of ['chatgpt','codex','news','papers'])bySection[section]=articles.filter(a=>a.section===section).length;
for(const section of ['chatgpt','codex','news'])for(const month of months){
 const view={section,filter:section==='news'?'全部':'功能更新',category:'all',month,q:'',saved:false};
 const items=filterArticles(articles,view,[],'2026-10-18');assert(items.length,'月份缺口 '+section+' '+month);
 assert(paginate(items,1).items.length<=10);assert(items.every(a=>a.date.startsWith(month)));
}
assert.equal(content.coverage.requestedFrom,'2025-09-01');
console.log(JSON.stringify({total:articles.length,bySection,continuousMonths:months.length,oldIDsRetained:true,detailsComplete:true},null,2));
