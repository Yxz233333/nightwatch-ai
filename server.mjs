import http from 'node:http';
import {DatabaseSync} from 'node:sqlite';
import {randomBytes,scryptSync,timingSafeEqual,createHash} from 'node:crypto';
import {readFileSync,existsSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {spawn} from 'node:child_process';
const root=path.dirname(fileURLToPath(import.meta.url));
mkdirSync(path.join(root,'data'),{recursive:true});
const db=new DatabaseSync(path.join(root,'data','nightwatch.sqlite'));
db.exec(`PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT UNIQUE,salt TEXT,hash TEXT);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user INTEGER,expires INTEGER);
CREATE TABLE IF NOT EXISTS marks(user INTEGER,article TEXT,kind TEXT,created TEXT,PRIMARY KEY(user,article,kind));`);
const digest=t=>createHash('sha256').update(t).digest('hex');
const failed=new Map();
let publishing=false,publishAgain=false;
function publishMarks(){if(process.env.NIGHTWATCH_DISABLE_PUBLISH==='1')return;if(publishing){publishAgain=true;return;}publishing=true;const p=spawn(process.execPath,[path.join(root,'publish-public.mjs')],{cwd:root,windowsHide:true,stdio:'ignore'});p.on('error',()=>{publishing=false;});p.on('exit',()=>{publishing=false;if(publishAgain){publishAgain=false;setTimeout(publishMarks,2000).unref();}});}
setTimeout(publishMarks,5000).unref();setInterval(publishMarks,60000).unref();
http.createServer(async(req,res)=>{
 const url=new URL(req.url,'http://localhost');
 const reply=(status,data)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(data));};
 try{
 if(url.pathname==='/api/health')return reply(200,{ok:true,service:'nightwatch-ai',hosting:'local'});
 if(url.pathname==='/api/content-version')return reply(200,{updatedAt:JSON.parse(readFileSync(path.join(root,'public','content.json'),'utf8')).updatedAt});
 if(req.method==='POST'&&req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`&&req.headers.origin!==`https://${req.headers.host}`)return reply(403,{error:'来源不匹配'});
 let body={};if(req.method==='POST'){let text='';for await(const chunk of req){text+=chunk;if(text.length>16000)return reply(413,{error:'请求过大'});}body=JSON.parse(text||'{}');}
 if(url.pathname==='/api/setup'&&req.method==='POST'){
  if(db.prepare('SELECT count(*) AS n FROM users').get().n)return reply(409,{error:'账号已创建'});
  if(!/^[\w\u4e00-\u9fff-]{2,32}$/.test(body.name||'')||typeof body.password!=='string'||body.password.length<8||body.password.length>200)return reply(400,{error:'用户名2至32字，密码至少8位'});
  const salt=randomBytes(16).toString('hex');db.prepare('INSERT INTO users(name,salt,hash) VALUES(?,?,?)').run(body.name,salt,scryptSync(body.password,salt,64).toString('hex'));return reply(201,{ok:true});
 }
 if(url.pathname==='/api/login'&&req.method==='POST'){
  const ip=req.socket.remoteAddress;const attempt=failed.get(ip);if(attempt&&attempt.count>=8&&Date.now()-attempt.at<600000)return reply(429,{error:'尝试过多，请10分钟后重试'});
  const user=db.prepare('SELECT * FROM users WHERE name=?').get(String(body.name||''));
  const hash=scryptSync(String(body.password||'').slice(0,200),user?.salt||'dummy',64);
  if(!user||!timingSafeEqual(hash,Buffer.from(user.hash,'hex'))){failed.set(ip,{count:(attempt?.count||0)+1,at:Date.now()});return reply(401,{error:'账号或密码错误'});}
  failed.delete(ip);const token=randomBytes(32).toString('hex');db.prepare('DELETE FROM sessions WHERE expires<?').run(Date.now());db.prepare('INSERT INTO sessions VALUES(?,?,?)').run(digest(token),user.id,Date.now()+30*86400000);
  res.setHeader('Set-Cookie',`nightwatch=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000${req.headers['x-forwarded-proto']==='https'?'; Secure':''}`);return reply(200,{ok:true,name:user.name});
 }
 const token=(req.headers.cookie||'').match(/(?:^|;\s*)nightwatch=([a-f0-9]{64})/)?.[1];
 const session=token?db.prepare('SELECT user FROM sessions WHERE token=? AND expires>?').get(digest(token),Date.now()):null;
 if(url.pathname==='/api/marks'){
  if(!session)return reply(401,{error:'请先登录'});
  if(req.method==='GET')return reply(200,{marks:db.prepare('SELECT article,kind,created FROM marks WHERE user=? ORDER BY created DESC').all(session.user)});
  if(req.method==='POST'){
   const articles=JSON.parse(readFileSync(path.join(root,'public','content.json'),'utf8')).articles;
   if(!articles.some(a=>a.id===body.article)||!['like','learn'].includes(body.kind))return reply(400,{error:'无效内容或标记'});
   if(body.enabled===false)db.prepare('DELETE FROM marks WHERE user=? AND article=? AND kind=?').run(session.user,body.article,body.kind);
   else db.prepare('INSERT OR IGNORE INTO marks VALUES(?,?,?,?)').run(session.user,body.article,body.kind,new Date().toISOString());publishMarks();return reply(200,{ok:true});
  }
 }
 if(url.pathname==='/api/logout'&&req.method==='POST'){if(token)db.prepare('DELETE FROM sessions WHERE token=?').run(digest(token));res.setHeader('Set-Cookie','nightwatch=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return reply(200,{ok:true});}
 if(url.pathname==='/api/me')return reply(200,{loggedIn:!!session,needsSetup:db.prepare('SELECT count(*) AS n FROM users').get().n===0});
 const files={'/':'index.html','/app.js':'app.js','/view-model.js':'view-model.js','/style.css':'style.css','/content.json':'content.json'};
 const file=files[url.pathname]||(/^\/(chatgpt|codex|news|papers|saved|articles|breakthroughs)(\/[^.]+)?\/?$/.test(url.pathname)?'index.html':null);if(!file||!existsSync(path.join(root,'public',file)))return reply(404,{error:'不存在'});
 res.writeHead(200,{'Cache-Control':'no-store','Content-Type':file.endsWith('.json')?'application/json; charset=utf-8':file.endsWith('.js')?'text/javascript; charset=utf-8':file.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'"});res.end(readFileSync(path.join(root,'public',file)));
 }catch(e){console.error(e.message);reply(500,{error:'服务暂时无法处理请求'});}
}).listen(Number(process.env.PORT||8791),'127.0.0.1',()=>console.log('夜行 AI 服务 http://127.0.0.1:8791'));



