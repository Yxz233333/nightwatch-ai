import {mkdtempSync,copyFileSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';import path from 'node:path';import {spawn,execFileSync} from 'node:child_process';import assert from 'node:assert/strict';
const temp=mkdtempSync(path.join(tmpdir(),'nightwatch-test-'));copyFileSync(new URL('./server.mjs',import.meta.url),path.join(temp,'server.mjs'));copyFileSync(new URL('./publish-public.mjs',import.meta.url),path.join(temp,'publish-public.mjs'));mkdirSync(path.join(temp,'public'));writeFileSync(path.join(temp,'public','content.json'),JSON.stringify({updatedAt:'2026-10-18',articles:[{id:'test',title:'A',section:'news',url:'https://example.com/a'},{id:'unmarked',title:'B',section:'papers',url:'https://example.com/b'}]}));
const child=spawn(process.execPath,[path.join(temp,'server.mjs')],{env:{...process.env,PORT:'18791',NIGHTWATCH_DISABLE_PUBLISH:'1'},stdio:'ignore',windowsHide:true});const base='http://127.0.0.1:18791';let cookie='';
async function req(url,body,origin){const r=await fetch(base+url,{method:body?'POST':'GET',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{}),...(origin?{Origin:origin}:{})},...(body?{body:JSON.stringify(body)}:{})});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];return {status:r.status,data:await r.json()};}
try{for(let i=0;i<40;i++){try{await fetch(base+'/api/health');break;}catch{await new Promise(r=>setTimeout(r,100));}}
assert.equal((await req('/api/marks')).status,401);
const credentials={name:'test-user',password:'12345678'};
assert.equal((await req('/api/setup',{...credentials,password:'1234567'})).status,400);
assert.equal((await req('/api/setup',credentials)).status,201);
assert.equal((await req('/api/setup',credentials)).status,409);
assert.equal((await req('/api/login',{...credentials,password:'wrong'})).status,401);
assert.equal((await req('/api/login',credentials)).status,200);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true},'https://evil.example')).status,403);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,1);
execFileSync(process.execPath,[path.join(temp,'publish-public.mjs')],{stdio:'ignore'});
const {readFileSync}=await import('node:fs');const exported=JSON.parse(readFileSync(path.join(temp,'docs','content.json'),'utf8'));
assert.equal(exported.articles.length,2);assert.equal(exported.articles.find(a=>a.id==='test').interest[0].kind,'learn');assert.equal(exported.articles.find(a=>a.id==='unmarked').interest.length,0);assert.equal(JSON.parse(readFileSync(path.join(temp,'docs','interests.json'),'utf8')).articles.length,1);assert(!JSON.stringify(exported).includes('12345678'));assert(!JSON.stringify(exported).includes('test-user'));
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,1);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:false})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,0);
await req('/api/logout',{});assert.equal((await req('/api/marks')).status,401);
console.log('通过：8位密码、7位拒绝、账号保护、登录验证、来源检查、收藏保存与取消、完整库及兴趣导出、凭据隔离、退出权限检查。');
}finally{child.kill();await new Promise(r=>child.once('exit',r));rmSync(temp,{recursive:true,maxRetries:15,retryDelay:200});}

