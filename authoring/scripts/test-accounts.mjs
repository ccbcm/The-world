import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const source=readFileSync(new URL('../../functions/api/[[path]].js',import.meta.url),'utf8');
const {onRequest}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const sql=new DatabaseSync(':memory:');sql.exec(readFileSync(new URL('./account-schema.sql',import.meta.url),'utf8'));
const DB={prepare(query){return {bind(...args){const q=sql.prepare(query);return {first:async()=>q.get(...args),all:async()=>({results:q.all(...args)}),run:async()=>q.run(...args)};}};}};
const env={DB,GITHUB_CLIENT_ID:'test',GITHUB_CLIENT_SECRET:'test'};
const digest=s=>createHash('sha256').update(s).digest('hex');
for(const [id,token] of [['alice','a'.repeat(64)],['bob','b'.repeat(64)]]){sql.prepare('INSERT INTO users VALUES(?,?,?,?)').run(id,id,id,Date.now());sql.prepare('INSERT INTO sessions VALUES(?,?,?)').run(digest(token),id,Date.now()+60000);}
async function req(path,method='GET',token='',body,origin='https://ccbcm.net'){const headers={Origin:origin,'Content-Type':'application/json'};if(token)headers.Cookie='__Host-ccbcm-session='+token;return onRequest({env,request:new Request('https://ccbcm.net/api/'+path,{method,headers,...(body?{body:JSON.stringify(body)}:{})})});}
assert.equal((await req('downloads')).status,401);
assert.equal((await req('downloads','POST','a'.repeat(64),{id:'blue'},'https://evil.example')).status,403);
assert.equal((await req('downloads','POST','a'.repeat(64),{id:'invalid'})).status,404);
assert.equal((await req('downloads','POST','a'.repeat(64),{id:'blue',user_id:'bob'})).status,200);
assert.equal((await req('downloads','POST','a'.repeat(64),{id:'blue'})).status,200);
assert.deepEqual((await (await req('downloads','GET','a'.repeat(64))).json()).items.map(x=>x.id),['blue']);
assert.equal((await (await req('downloads','GET','b'.repeat(64))).json()).items.length,0);
assert.equal((await req('logout','POST','a'.repeat(64))).status,200);
assert.equal((await req('downloads','GET','a'.repeat(64))).status,401);
const login=await req('auth/github');assert.equal(login.status,302);const auth=new URL(login.headers.get('Location'));assert.equal(auth.origin,'https://github.com');assert.equal(auth.searchParams.has('scope'),false);assert.ok(login.headers.get('Set-Cookie').includes('HttpOnly; Secure; SameSite=Lax'));
assert.equal((await req('auth/callback?code=x&state=wrong')).headers.get('Location'),'https://ccbcm.net/?login=failed#downloads');
sql.prepare('UPDATE sessions SET expires_at=0').run();assert.equal((await req('downloads','GET','b'.repeat(64))).status,401);
assert.equal((await (await onRequest({env:{},request:new Request('https://ccbcm.net/api/account')})).json()).ready,false);
console.log('PASS: unauthenticated requests, CSRF, invalid assets, user isolation, duplicate downloads, logout, expiry, OAuth state and unconfigured service');
