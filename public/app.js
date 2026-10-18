import {CHOICES,LABELS,readView,viewUrl,filterArticles,paginate,beijingToday,monthAgo} from './view-model.js?v=20261018-3';
const $=s=>document.querySelector(s);let view=readView(location.href),loggedIn=false,needsSetup=false,marks=[],content={articles:[]};
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};const notice=t=>$('#notice').textContent=t;
const controls=node('div',null,'browse-controls'),monthSelect=node('select'),categorySelect=node('select'),search=node('input'),pagination=node('nav',null,'pagination');
monthSelect.id='month';categorySelect.id='category';search.type='search';search.placeholder='搜索标题、摘要、论文或关键词';search.setAttribute('aria-label','搜索内容');
function labelled(text,input){const label=node('label',text);label.append(input);return label;}
const categoryLabel=labelled('内容类别',categorySelect);controls.append(labelled('发布时间',monthSelect),categoryLabel,labelled('搜索',search));$('#filters').after(controls);$('#articles').after(pagination);pagination.setAttribute('aria-label','内容分页');
async function api(url,body){const r=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const data=await r.json();if(!r.ok)throw Error(data.error||'请求失败');return data;}
function navigate(next,replace=false){view=next;history[replace?'replaceState':'pushState']({},'',viewUrl(view));render();window.scrollTo({top:Math.max(0,$('#sections').offsetTop-12),behavior:'instant'});}
window.addEventListener('popstate',()=>{view=readView(location.href);render();});
monthSelect.onchange=()=>navigate({...view,month:monthSelect.value,page:1});categorySelect.onchange=()=>navigate({...view,category:categorySelect.value,page:1});
search.oninput=()=>{view={...view,q:search.value,page:1};history.replaceState({},'',viewUrl(view));renderList();};
function options(select,entries,value){select.replaceChildren();for(const [key,label] of entries){const o=node('option',label);o.value=key;select.append(o);}select.value=value;}
function marked(id,kind){return marks.some(m=>m.article===id&&m.kind===kind);}
function actions(a){const wrap=node('div',null,'actions');for(const [kind,text] of [['like','喜欢'],['learn','想深入了解']]){const button=node('button',(marked(a.id,kind)?'已标记 · ':'')+text,marked(a.id,kind)?'active':'');button.onclick=async()=>{if(!loggedIn){$('#account').showModal();return;}button.disabled=true;try{await api('/api/marks',{article:a.id,kind,enabled:!marked(a.id,kind)});marks=(await api('/api/marks')).marks;notice('标记已保存，公开阅读站会在发布后同步。');render();}catch(e){notice(e.message);button.disabled=false;}};wrap.append(button);}return wrap;}
function detailLink(a){const link=node('a',a.titleZh||a.title);link.href=viewUrl({detail:a.id,from:viewUrl(view)});link.onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();navigate({...view,detail:a.id,from:viewUrl(view)});};return link;}
function render(){
 document.body.classList.toggle('reading-detail',!!view.detail);
 document.title=view.detail?'内容详情 · 夜行':'夜行 · AI 观察站';$('#sections').querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.section===(view.detail?content.articles.find(a=>a.id===view.detail)?.section:view.section)));$('#saved').classList.toggle('active',view.saved);
 $('#filters').replaceChildren();controls.hidden=!!view.detail;pagination.hidden=!!view.detail;
 if(view.detail){renderDetail();return;}
 if(view.section!=='papers')for(const label of CHOICES[view.section]){const b=node('button',label,label===view.filter?'active':'');b.onclick=()=>navigate({...view,filter:label,page:1});$('#filters').append(b);}
 const all=content.articles.filter(a=>a.section===view.section);const months=[...new Set(all.map(a=>a.date?.slice(0,7)).filter(Boolean))].sort().reverse();
 options(monthSelect,[['latest','最新（最近一个月）'],['all','全部月份'],...months.map(m=>[m,m.replace('-','年')+'月']),...(all.some(a=>!a.date)?[['undated','日期待核实']]:[])],view.month);
 if(!monthSelect.value){view.month='latest';monthSelect.value='latest';history.replaceState({},'',viewUrl(view));}
 categoryLabel.hidden=!['papers','news'].includes(view.section);categoryLabel.firstChild.textContent=view.section==='papers'?'论文领域':'资讯类别';
 options(categorySelect,[['all','全部'],...[...new Set(all.map(a=>a.category))].sort((a,b)=>a.localeCompare(b,'zh-CN')).map(c=>[c,c])],view.category);
 if(!categorySelect.value){view.category='all';categorySelect.value='all';}
 search.value=view.q;renderList();
}
function renderList(){
 $('#articles').replaceChildren();pagination.replaceChildren();const result=paginate(filterArticles(content.articles,view,marks),view.page);if(result.page!==view.page){view.page=result.page;history.replaceState({},'',viewUrl(view));}
 const range=view.month==='latest'?`${monthAgo(beijingToday())} 至 ${beijingToday()}`:view.month==='all'?'全部月份':view.month==='undated'?'日期待核实':view.month;
 pagination.append(node('span',`${range} · 共 ${result.total} 条 · 第 ${result.page} / ${result.pages} 页`));
 for(const [text,page,disabled] of [['上一页',result.page-1,result.page===1],['下一页',result.page+1,result.page===result.pages]]){const b=node('button',text);b.disabled=disabled;b.onclick=()=>navigate({...view,page});pagination.append(b);}
 for(const a of result.items){const card=node('article',null,'content-card');card.append(node('small',`${a.category} · ${a.date||'日期待核实'}`));const title=node('h2');title.append(detailLink(a));card.append(title);
  if(a.section==='papers')card.append(node('p',a.titleEn||a.title,'subtitle'));else card.append(node('p',a.summary));
  const detail=node('a','查看详情 →');detail.href=viewUrl({detail:a.id,from:viewUrl(view)});detail.onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();navigate({...view,detail:a.id,from:viewUrl(view)});};card.append(detail,actions(a));$('#articles').append(card);
 }
 if(!result.total)$('#articles').append(node('div',view.saved?'当前筛选下没有你的标记。可切换月份或类别。':'当前月份与分类暂无内容，可选择其他月份或全部。','empty'));
}
function paragraph(parent,title,text){if(!text)return;parent.append(node('h2',title),node('p',text));}
function renderDetail(){
 $('#articles').replaceChildren();pagination.replaceChildren();const a=content.articles.find(a=>a.id===view.detail);if(!a){$('#articles').append(node('div','内容不存在或已归档。','empty'));return;}
 document.title=(a.titleZh||a.title)+' · 夜行';const article=node('article',null,'detail-view');const back=node('a','← 返回列表');const validFrom=view.from.startsWith('/')&&!view.from.startsWith('//')&&!view.from.startsWith('/articles/');back.href=validFrom?view.from:'/'+a.section+'/';back.onclick=e=>{e.preventDefault();navigate(readView(back.href));};article.append(back,node('small',`${LABELS[a.section]} / ${a.category} · ${a.date||'日期待核实'}`),node('h1',a.titleZh||a.title));
 if(a.section==='papers')article.append(node('p',a.titleEn||a.title,'subtitle'));
 article.append(actions(a));paragraph(article,a.section==='papers'?'这篇论文研究什么':'具体内容',a.details?.overview||a.summary);
 if(a.details?.keyPoints?.length){article.append(node('h2',a.section==='papers'?'主要研究要点':'主要变化'));const ul=node('ul');for(const point of a.details.keyPoints)ul.append(node('li',point));article.append(ul);}
 if(a.section==='papers'){paragraph(article,'收录与审阅状态',a.summary+'\n'+a.status);paragraph(article,'英文原始摘要',a.abstractEnglish);}
 else paragraph(article,'开放范围与状态',a.status);
 paragraph(article,'阅读说明',a.details?.editorialNote);article.append(node('h2','原始来源'));const source=node('a','打开原始论文或发布说明 ↗');source.href=a.url;source.target='_blank';source.rel='noopener noreferrer';article.append(source,node('p','固定编号：'+a.id,'article-id'));$('#articles').append(article);
}
$('#sections').onclick=e=>{const section=e.target.dataset.section;if(section)navigate({...readView('/'+section+'/'),saved:view.saved});};
$('#saved').onclick=()=>{if(!loggedIn){$('#account').showModal();return;}navigate({...readView('/'+view.section+'/'),saved:!view.saved});};
$('#login').onclick=async()=>{if(loggedIn){try{await api('/api/logout',{});loggedIn=false;marks=[];$('#login').textContent='登录';render();}catch(e){notice(e.message);}}else $('#account').showModal();};$('#cancel').onclick=()=>$('#account').close();
$('#auth').onsubmit=async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));const submit=e.target.querySelector('[type=submit]');submit.disabled=true;try{if(needsSetup){await api('/api/setup',data);needsSetup=false;}await api('/api/login',data);loggedIn=true;marks=(await api('/api/marks')).marks;$('#login').textContent='退出登录';e.target.reset();$('#account').close();render();}catch(e){$('#auth-error').textContent=e.message;}finally{submit.disabled=false;}};
async function init(){content=await(await fetch('/content.json')).json();$('#updated').textContent=content.updatedAt?'最近整理：'+content.updatedAt:'';try{const me=await api('/api/me');loggedIn=me.loggedIn;needsSetup=me.needsSetup;if(loggedIn){marks=(await api('/api/marks')).marks;$('#login').textContent='退出登录';}if(needsSetup){$('#auth-title').textContent='创建你的网站账号';$('#auth-note').textContent='密码至少8位，创建后可在手机和电脑上登录、同步标记。';}}catch{notice('后端暂不可用，仍可浏览内容。');}render();history.replaceState({},'',viewUrl(view));}
init().catch(e=>notice('加载失败：'+e.message));
