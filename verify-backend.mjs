import {mkdtempSync,copyFileSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';import path from 'node:path';import {spawn} from 'node:child_process';import assert from 'node:assert/strict';
const temp=mkdtempSync(path.join(tmpdir(),'nightwatch-test-'));copyFileSync(new URL('./server.mjs',import.meta.url),path.join(temp,'server.mjs'));mkdirSync(path.join(temp,'public'));writeFileSync(path.join(temp,'public','content.json'),JSON.stringify({articles:[{id:'test'}]}));
const child=spawn(process.execPath,[path.join(temp,'server.mjs')],{env:{...process.env,PORT:'18791'},stdio:'ignore',windowsHide:true});const base='http://127.0.0.1:18791';let cookie='';
async function req(url,body,origin){const r=await fetch(base+url,{method:body?'POST':'GET',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{}),...(origin?{Origin:origin}:{})},...(body?{body:JSON.stringify(body)}:{})});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];return {status:r.status,data:await r.json()};}
try{for(let i=0;i<40;i++){try{await fetch(base+'/api/health');break;}catch{await new Promise(r=>setTimeout(r,100));}}
assert.equal((await req('/api/marks')).status,401);
const credentials={name:'test-user',password:'test-only-long-password'};
assert.equal((await req('/api/setup',credentials)).status,201);
assert.equal((await req('/api/setup',credentials)).status,409);
assert.equal((await req('/api/login',{...credentials,password:'wrong'})).status,401);
assert.equal((await req('/api/login',credentials)).status,200);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true},'https://evil.example')).status,403);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,1);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:true})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,1);
assert.equal((await req('/api/marks',{article:'test',kind:'learn',enabled:false})).status,200);
assert.equal((await req('/api/marks')).data.marks.length,0);
await req('/api/logout',{});assert.equal((await req('/api/marks')).status,401);
console.log('通过：账号创建、重复创建保护、登录验证、来源检查、收藏保存与取消、退出后的权限检查。');
}finally{child.kill();await new Promise(r=>child.once('exit',r));rmSync(temp,{recursive:true});}
