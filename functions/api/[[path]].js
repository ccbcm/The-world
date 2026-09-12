const ORIGIN = 'https://ccbcm.net';
const ids = new Set(['blue','waves','clouds','net','cat','lines','caffeine','tux']);
const json = (body,status=200) => new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const random = () => Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
const hash = async value => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),b=>b.toString(16).padStart(2,'0')).join('');
const cookie = (name,value,age) => `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${age}`;
function cookies(request) { return Object.fromEntries((request.headers.get('Cookie')||'').split(';').map(s=>s.trim().split('='))); }
function redirect(url, values=[]) { const headers=new Headers({'Location':url,'Cache-Control':'no-store','Referrer-Policy':'no-referrer'}); for(const value of values)headers.append('Set-Cookie',value);return new Response(null,{status:302,headers}); }
async function current(request,db) { const token=cookies(request)['__Host-ccbcm-session'];if(!token||!/^[a-f0-9]{64}$/.test(token))return null;return db.prepare('SELECT users.id, users.login, users.name FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>?').bind(await hash(token),Date.now()).first(); }
async function spaces(db) {
  await db.prepare('CREATE TABLE IF NOT EXISTS profiles (user_id TEXT PRIMARY KEY REFERENCES users(id), nickname TEXT NOT NULL, bio TEXT NOT NULL DEFAULT "", avatar TEXT NOT NULL DEFAULT "github")').bind().run();
  await db.prepare('CREATE TABLE IF NOT EXISTS favorites (user_id TEXT NOT NULL REFERENCES users(id), work_id TEXT NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(user_id,work_id))').bind().run();
}
async function avatarTable(db){await db.prepare('CREATE TABLE IF NOT EXISTS avatars (user_id TEXT PRIMARY KEY REFERENCES users(id), image TEXT NOT NULL)').bind().run();}
async function profileFor(db,user) {
  await avatarTable(db);const custom=await db.prepare('SELECT image FROM avatars WHERE user_id=?').bind(user.id).first();
  const p=await db.prepare('SELECT nickname,bio,avatar FROM profiles WHERE user_id=?').bind(user.id).first();
  return {login:user.login,name:p?.nickname||user.name,bio:p?.bio||'',avatar:p?.avatar||'github',avatarUrl:custom?.image||(/^[0-9]+$/.test(user.id)?'https://avatars.githubusercontent.com/u/'+user.id+'?s=160':null),customAvatar:!!custom};
}
async function bodyJSON(request) {
  if(!request.headers.get('Content-Type')?.startsWith('application/json'))return null;
  const text=await request.text();if(text.length>4096)return null;
  try{const value=JSON.parse(text);return value&&typeof value==='object'&&!Array.isArray(value)?value:null}catch{return null}
}
const VIDEO_MAX=25*1024*1024, USER_VIDEO_MAX=250*1024*1024, SITE_VIDEO_MAX=8*1024*1024*1024;
async function isPublished(db,id){if(typeof id!=='string'||!/^[a-f0-9]{64}$/.test(id))return false;await videoTable(db);return !!await db.prepare("SELECT id FROM creator_videos WHERE id=? AND state='published'").bind(id).first();}
const isReviewer=(env,user)=>!!user&&!!env.ADMIN_GITHUB_ID&&String(user.id)===String(env.ADMIN_GITHUB_ID);
async function reviewTable(db){await db.prepare("CREATE TABLE IF NOT EXISTS video_reviews (video_id TEXT PRIMARY KEY, decision TEXT NOT NULL, reason TEXT NOT NULL, reviewer_id TEXT NOT NULL, reviewed_at INTEGER NOT NULL)").bind().run();}
async function moderation(request,env,user,path){
 if(!isReviewer(env,user))return json({error:'只有网站管理员可以审核作品。'},403);
 await videoTable(env.DB);await reviewTable(env.DB);const db=env.DB;
 if(path==='/api/moderation'&&request.method==='GET')return json({items:(await db.prepare("SELECT v.id,v.title,v.description,v.poster,v.size,v.state,v.updated_at,u.login,r.reason,r.decision FROM creator_videos v JOIN users u ON u.id=v.user_id LEFT JOIN video_reviews r ON r.video_id=v.id WHERE v.state IN ('review','approved','ready','published','unlisted') AND (v.state!='ready' OR r.video_id IS NOT NULL) ORDER BY CASE WHEN v.state='review' THEN 0 ELSE 1 END,v.updated_at DESC").bind().all()).results});
 const m=path.match(/^\/api\/moderation\/([a-f0-9]{64})(\/content)?$/);if(!m)return json({error:'找不到这件作品。'},404);
 const row=await db.prepare('SELECT * FROM creator_videos WHERE id=?').bind(m[1]).first();if(!row)return json({error:'找不到这件作品。'},404);
 if(m[2]&&request.method==='GET')return handleVideos(request,env,{id:row.user_id},'/api/videos/'+row.id+'/content');
 if(!m[2]&&request.method==='POST'){
 const b=await bodyJSON(request);if(!b||!['approve','reject','unlist'].includes(b.decision)||typeof b.reason!=='string'||b.reason.length>500||(b.decision!=='approve'&&!b.reason.trim()))return json({error:'退回或下架时请填写原因，最多 500 字。'},400);
 const state=b.decision==='approve'?'approved':b.decision==='unlist'?'unlisted':'ready',from=b.decision==='unlist'?'published':'review',now=Date.now();
 // One transaction keeps the decision and state together; a competing review cannot overwrite it.
 const result=await db.batch([
 db.prepare("INSERT INTO video_reviews(video_id,decision,reason,reviewer_id,reviewed_at) SELECT id,?,?,?,? FROM creator_videos WHERE id=? AND state=? ON CONFLICT(video_id) DO UPDATE SET decision=excluded.decision,reason=excluded.reason,reviewer_id=excluded.reviewer_id,reviewed_at=excluded.reviewed_at").bind(b.decision,b.reason.trim(),user.id,now,row.id,from),
 db.prepare("UPDATE creator_videos SET state=?,updated_at=? WHERE id=? AND state=?").bind(state,now,row.id,from)]);
 if(!changed(result[1]))return json({error:'作品状态已改变，请刷新后再审核。'},409);
 return json({ok:true,state});
 }
 return json({error:'不支持这个操作。'},405);
}
async function videoTable(db){await db.prepare(`CREATE TABLE IF NOT EXISTS creator_videos (
 id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',
 size INTEGER NOT NULL,sha256 TEXT NOT NULL,poster TEXT NOT NULL DEFAULT '',state TEXT NOT NULL,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL
)`).bind().run();await db.prepare('CREATE INDEX IF NOT EXISTS creator_videos_owner ON creator_videos(user_id)').bind().run();
 await db.prepare('CREATE TABLE IF NOT EXISTS video_upload_daily (user_id TEXT NOT NULL, day INTEGER NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(user_id,day))').bind().run();
 await db.prepare(`CREATE TRIGGER IF NOT EXISTS count_video_upload AFTER INSERT ON creator_videos BEGIN
 INSERT INTO video_upload_daily(user_id,day,n) VALUES(NEW.user_id,CAST(NEW.created_at/86400000 AS INTEGER),1)
 ON CONFLICT(user_id,day) DO UPDATE SET n=n+1; END`).bind().run();}

const changed=r=>Number(r.meta?.changes??r.changes??0);
async function limitedBody(request,max){const reader=request.body?.getReader();if(!reader)throw Error('文件为空。');const parts=[];let size=0;try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max)throw Error('文件超过大小限制。');parts.push(value);}}catch(e){await reader.cancel().catch(()=>{});throw e;}const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}return bytes;}
function mp4Container(bytes){if(bytes.length<32)return false;const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let pos=0;const boxes=new Set();while(pos+8<=bytes.length){let size=view.getUint32(pos);const type=String.fromCharCode(...bytes.subarray(pos+4,pos+8));let header=8;if(size===1){if(pos+16>bytes.length||view.getUint32(pos+8)!==0)return false;size=view.getUint32(pos+12);header=16;}if(size===0)size=bytes.length-pos;if(size<header||pos+size>bytes.length)return false;boxes.add(type);pos+=size;}return pos===bytes.length&&boxes.has('ftyp')&&boxes.has('moov')&&boxes.has('mdat');}
async function videoJSON(request){try{return JSON.parse(new TextDecoder().decode(await limitedBody(request,90000)))}catch{return null}}
async function handleVideos(request,env,user,path){
 await videoTable(env.DB);await reviewTable(env.DB);const db=env.DB,bucket=env.CREATOR_ASSETS;
 if(!bucket)return json({error:'文件存储暂时不可用。'},503);
 if(path==='/api/videos'){
  if(request.method==='GET'){const items=(await db.prepare('SELECT id,title,description,size,poster,state,created_at,(SELECT reason FROM video_reviews WHERE video_id=creator_videos.id) AS review_reason FROM creator_videos WHERE user_id=? ORDER BY created_at DESC').bind(user.id).all()).results;return json({items,limits:{file:VIDEO_MAX,account:USER_VIDEO_MAX},used:items.reduce((n,x)=>n+x.size+65536,0)});}
  if(request.method==='POST'){
   const b=await videoJSON(request);if(!b||typeof b.title!=='string'||!b.title.trim()||b.title.length>100||!Number.isSafeInteger(b.size)||b.size<32||b.size>VIDEO_MAX||! /^[a-f0-9]{64}$/.test(b.sha256||''))return json({error:'请选择 25 MB 以内的 MP4，并填写标题。'},400);
   const poster=typeof b.poster==='string'?b.poster:'';if(poster.length>60000||poster&&!/^data:image\/jpeg;base64,\/9j\/[A-Za-z0-9+/=]+$/.test(poster))return json({error:'封面无效。'},400);
   const id=random(),now=Date.now();
   const result=await db.prepare(`INSERT INTO creator_videos(id,user_id,title,size,sha256,poster,state,created_at,updated_at)
    SELECT ?,?,?,?,?,?,'reserved',?,? WHERE
    (SELECT COALESCE(SUM(size+65536),0) FROM creator_videos WHERE user_id=?)+? <= ? AND
    (SELECT COALESCE(SUM(size+65536),0) FROM creator_videos)+? <= ? AND
    COALESCE((SELECT n FROM video_upload_daily WHERE user_id=? AND day=?),0)<20`).bind(id,user.id,b.title.trim(),b.size,b.sha256,poster,now,now,user.id,b.size+65536,USER_VIDEO_MAX,b.size+65536,SITE_VIDEO_MAX,user.id,Math.floor(now/86400000)).run();
   if(!changed(result))return json({error:'当前上传额度不足：每人 250 MB、每天最多 20 次新上传，或全站容量已达上限。'},429);return json({id,state:'reserved'});
  }
 }
 const match=path.match(/^\/api\/videos\/([a-f0-9]{64})(?:\/(content|submit|publish|unlist))?$/);if(!match)return json({error:'找不到这件作品。'},404);
 const row=await db.prepare('SELECT * FROM creator_videos WHERE id=? AND user_id=?').bind(match[1],user.id).first();if(!row)return json({error:'找不到这件作品。'},404);const key='videos/'+row.user_id+'/'+row.id+'.mp4',action=match[2];
 if(action==='content'&&request.method==='PUT'){
  if(['ready','review','approved','published','unlisted'].includes(row.state))return json({ok:true,state:row.state});
  const lock=await db.prepare("UPDATE creator_videos SET state='uploading',updated_at=? WHERE id=? AND (state IN ('reserved','failed') OR (state='uploading' AND updated_at<?))").bind(Date.now(),row.id,Date.now()-15*60000).run();if(!changed(lock))return json({error:'文件正在处理中，请稍后再试。'},409);
  try{
   if(request.headers.get('Content-Type')!=='video/mp4')throw Error('请选择 MP4 视频。');
   const bytes=await limitedBody(request,Math.min(row.size,VIDEO_MAX));if(bytes.length!==row.size)throw Error('文件传输不完整，请重试。');
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');if(digest!==row.sha256)throw Error('文件与上次选择的不一致，请重新选择原文件。');
   if(!mp4Container(bytes))throw Error('无法识别 MP4 文件结构，请重新导出视频。');
   await bucket.put(key,bytes,{httpMetadata:{contentType:'video/mp4'}});
   await db.prepare("UPDATE creator_videos SET state='ready',updated_at=? WHERE id=?").bind(Date.now(),row.id).run();return json({ok:true,state:'ready'});
  }catch(e){await db.prepare("UPDATE creator_videos SET state='failed',updated_at=? WHERE id=?").bind(Date.now(),row.id).run();return json({error:e.message||'上传失败，请重试。'},400);}
 }
 if(action==='content'&&request.method==='GET'){
  if(!['ready','review','approved','published','unlisted'].includes(row.state))return json({error:'视频尚未上传完成。'},409);
  const range=request.headers.get('Range');let options={},start=0,end=row.size-1;
  if(range){const m=range.match(/^bytes=(\d*)-(\d*)$/);if(!m||!m[1]&&!m[2])return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+row.size}});if(m[1]){start=Number(m[1]);end=m[2]?Math.min(Number(m[2]),end):end;}else start=Math.max(0,row.size-Number(m[2]));if(start>end||start>=row.size)return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+row.size}});options={range:{offset:start,length:end-start+1}};}
  const object=await bucket.get(key,options);if(!object)return json({error:'视频暂时无法读取。'},404);
  const headers={'Content-Type':'video/mp4','Content-Length':String(end-start+1),'Accept-Ranges':'bytes','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'};if(range)headers['Content-Range']=`bytes ${start}-${end}/${row.size}`;return new Response(object.body,{status:range?206:200,headers});
 }
 if(['publish','unlist'].includes(action)&&request.method==='POST'){
 const from=action==='publish'?'approved':'published',to=action==='publish'?'published':'unlisted';
 const result=await db.prepare('UPDATE creator_videos SET state=?,updated_at=? WHERE id=? AND user_id=? AND state=?').bind(to,Date.now(),row.id,user.id,from).run();
 return changed(result)?json({ok:true,state:to}):json({error:'作品状态已改变，请刷新后再试。'},409);
 }
 if(action==='submit'&&request.method==='POST'){
  if(!['ready','review','unlisted'].includes(row.state))return json({error:'请先完成视频上传。'},409);
  const update=await db.prepare("UPDATE creator_videos SET state='review',updated_at=? WHERE id=? AND state IN ('ready','review','unlisted')").bind(Date.now(),row.id).run();if(!changed(update))return json({error:'作品状态已改变，请刷新。'},409);return json({ok:true,state:'review'});
 }
 if(!action&&request.method==='PATCH'){
  if(['review','approved','published'].includes(row.state))return json({error:'审核中的作品暂时不能修改。'},409);
  const b=await videoJSON(request);if(!b||typeof b.title!=='string'||!b.title.trim()||b.title.length>100||typeof b.description!=='string'||b.description.length>1500)return json({error:'标题限 100 字，简介限 1500 字。'},400);
  await db.prepare('UPDATE creator_videos SET title=?,description=?,updated_at=? WHERE id=? AND state NOT IN ("review","approved","published","deleting")').bind(b.title.trim(),b.description.trim(),Date.now(),row.id).run();return json({ok:true});
 }
 if(!action&&request.method==='DELETE'){
  if(row.state==='uploading')return json({error:'视频正在上传，请稍后再移除。'},409);
  const lock=await db.prepare("UPDATE creator_videos SET state='deleting' WHERE id=? AND state NOT IN ('uploading','deleting')").bind(row.id).run();if(!changed(lock))return json({error:'文件处理中，请稍后再移除。'},409);
  try{await bucket.delete(key);await db.prepare("DELETE FROM creator_videos WHERE id=? AND user_id=? AND state='deleting'").bind(row.id,user.id).run();return json({ok:true});}catch{await db.prepare("UPDATE creator_videos SET state=? WHERE id=? AND state='deleting'").bind(row.state,row.id).run();return json({error:'移除失败，请重试。'},503);}
 }
 return json({error:'不支持这个操作。'},405);
}
export async function onRequest({request,env}) {
  const url=new URL(request.url),path=url.pathname;
  const ready=!!(env.DB&&env.GITHUB_CLIENT_ID&&env.GITHUB_CLIENT_SECRET);
  if(path==='/api/account'&&request.method==='GET') {
    if(!ready)return json({user:null,ready:false});
    try{const user=await current(request,env.DB);return json({user,ready:true,reviewer:isReviewer(env,user)});}catch{return json({error:'账号服务暂时不可用，请稍后重试。'},503);}
  }
  if(!ready)return json({error:'GitHub 登录正在配置，请稍后再来。'},503);
  if(url.origin!==ORIGIN)return json({error:'请在 ccbcm.net 使用账号功能。'},403);
  if(request.method!=='GET'&&request.headers.get('Origin')!==ORIGIN)return json({error:'请求来源不符。'},403);
  let stage="session";
  try {
    if(path==='/api/auth/github'&&request.method==='GET') {
      const state=random();const auth=new URL('https://github.com/login/oauth/authorize');auth.searchParams.set('client_id',env.GITHUB_CLIENT_ID);auth.searchParams.set('redirect_uri',ORIGIN+'/api/auth/callback');auth.searchParams.set('state',state);
      return redirect(auth.href,[cookie('__Host-ccbcm-state',state,600)]);
    }
    if(path==='/api/auth/callback'&&request.method==='GET') {
      const state=cookies(request)['__Host-ccbcm-state'];
      if(!state||!/^[a-f0-9]{64}$/.test(state)||state!==url.searchParams.get('state')||!url.searchParams.get('code'))return redirect(ORIGIN+'/?login=failed#downloads',[cookie('__Host-ccbcm-state','',0)]);
      stage='token_exchange';
      const response=await fetch('https://github.com/login/oauth/access_token',{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/json'},body:JSON.stringify({client_id:env.GITHUB_CLIENT_ID.trim(),client_secret:env.GITHUB_CLIENT_SECRET.trim(),code:url.searchParams.get('code'),redirect_uri:ORIGIN+'/api/auth/callback'})});
      const token=await response.json();if(!response.ok||!token.access_token)throw Error(['bad_verification_code','incorrect_client_credentials','redirect_uri_mismatch'].includes(token.error)?token.error:'token_exchange_failed');
      stage='profile';
      const profile=await fetch('https://api.github.com/user',{headers:{'Authorization':'Bearer '+token.access_token,'User-Agent':'CCBCM','Accept':'application/vnd.github+json'}});
      const user=await profile.json();if(!profile.ok||!Number.isSafeInteger(user.id)||typeof user.login!=='string')throw Error('Profile failed');
      stage='database';
      const session=random();await env.DB.batch([
        env.DB.prepare('INSERT INTO users(id,login,name,created_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET login=excluded.login,name=excluded.name').bind(String(user.id),user.login,user.name||user.login,Date.now()),
        env.DB.prepare('DELETE FROM sessions WHERE expires_at<?').bind(Date.now()),
        env.DB.prepare('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)').bind(await hash(session),String(user.id),Date.now()+30*86400000)
      ]);
      return redirect(ORIGIN+'/#downloads',[cookie('__Host-ccbcm-state','',0),cookie('__Host-ccbcm-session',session,30*86400)]);
    }
    if(path==='/api/published-videos'&&request.method==='GET'){
      await videoTable(env.DB);return json({items:(await env.DB.prepare("SELECT v.id,v.title,v.description,v.poster,v.size,u.login FROM creator_videos v JOIN users u ON u.id=v.user_id WHERE v.state='published' ORDER BY v.updated_at DESC").bind().all()).results});
    }
    const publicVideo=path.match(/^\/api\/published-videos\/([a-f0-9]{64})\/content$/);
    if(publicVideo&&request.method==='GET'){
      await videoTable(env.DB);const row=await env.DB.prepare("SELECT user_id FROM creator_videos WHERE id=? AND state='published'").bind(publicVideo[1]).first();
      if(!row)return json({error:'作品尚未公开或已下架。'},404);
      return await handleVideos(request,env,{id:row.user_id},'/api/videos/'+publicVideo[1]+'/content');
    }
    if(path.startsWith('/api/people/')&&request.method==='GET') {
      const login=path.slice('/api/people/'.length);
      if(!/^[a-zA-Z0-9-]{1,39}$/.test(login))return json({error:'找不到这位创作者。'},404);
      const person=await env.DB.prepare('SELECT id,login,name FROM users WHERE lower(login)=lower(?)').bind(login).first();
      if(!person)return json({error:'找不到这位创作者。'},404);
      await spaces(env.DB);return json({profile:await profileFor(env.DB,person)});
    }
    const user=await current(request,env.DB);if(!user)return json({error:'请先登录 GitHub。'},401);
    if(path==='/api/reports'||path==='/api/moderation/reports'){
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY,user_id TEXT NOT NULL,work_id TEXT NOT NULL,reason TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'open',created_at INTEGER NOT NULL, UNIQUE(user_id,work_id))").bind().run();
      if(path==='/api/moderation/reports'){
        if(!isReviewer(env,user))return json({error:'只有管理员可以处理举报。'},403);
        if(request.method==='GET')return json({items:(await env.DB.prepare("SELECT r.id,r.work_id,r.reason,r.state,u.login,v.title FROM reports r JOIN users u ON u.id=r.user_id LEFT JOIN creator_videos v ON v.id=r.work_id ORDER BY r.created_at DESC LIMIT 200").bind().all()).results});
        if(request.method==='POST'){const b=await bodyJSON(request);if(!b||typeof b.id!=='string')return json({error:'无效举报。'},400);const result=await env.DB.prepare("UPDATE reports SET state='closed' WHERE id=? AND state='open'").bind(b.id).run();return changed(result)?json({ok:true}):json({error:'举报已处理或不存在。'},409);}
      }else if(request.method==='POST'){
        const b=await bodyJSON(request);if(!b||typeof b.reason!=='string'||!b.reason.trim()||b.reason.length>500||!await isPublished(env.DB,b.id))return json({error:'请填写举报原因，最多 500 字。'},400);
        const result=await env.DB.prepare("INSERT INTO reports(id,user_id,work_id,reason,created_at) SELECT ?,?,?,?,? WHERE (SELECT COUNT(*) FROM reports WHERE user_id=? AND created_at>?)<10 ON CONFLICT(user_id,work_id) DO NOTHING").bind(random(),user.id,b.id,b.reason.trim(),Date.now(),user.id,Date.now()-86400000).run();
        return changed(result)?json({ok:true}):json({error:'你已举报过这件作品，或今天的举报次数已达上限。'},409);
      }
      return json({error:'不支持这个操作。'},405);
    }
    if(path==='/api/moderation'||path.startsWith('/api/moderation/'))return await moderation(request,env,user,path);
    if(path==='/api/videos'||path.startsWith('/api/videos/'))return await handleVideos(request,env,user,path);
    if(path==='/api/storage'&&request.method==='GET') {
      if(!env.CREATOR_ASSETS)return json({ready:false},503);
      try{await env.CREATOR_ASSETS.head('__connection_check__');return json({ready:true});}
      catch{return json({error:'文件存储暂时不可用。'},503);}
    }
    if(path==='/api/drafts') {
      await env.DB.prepare('CREATE TABLE IF NOT EXISTS drafts (id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL,updated_at INTEGER NOT NULL)').bind().run();
      if(request.method==='GET')return json({items:(await env.DB.prepare('SELECT id,title,description,updated_at FROM drafts WHERE user_id=? ORDER BY updated_at DESC').bind(user.id).all()).results});
      if(request.method==='POST') {
        const b=await bodyJSON(request);if(!b||typeof b.title!=='string'||!b.title.trim()||b.title.length>100||typeof b.description!=='string'||b.description.length>1500)return json({error:'请填写标题（100 字内）和简介（1500 字内）。'},400);
        const id=b.id||random();if(b.id){const own=await env.DB.prepare('SELECT id FROM drafts WHERE id=? AND user_id=?').bind(id,user.id).first();if(!own)return json({error:'找不到这份草稿。'},404);}
        else {const count=await env.DB.prepare('SELECT COUNT(*) AS n FROM drafts WHERE user_id=?').bind(user.id).first();if(count.n>=50)return json({error:'最多保留 50 份草稿。'},400);}
        await env.DB.prepare('INSERT INTO drafts(id,user_id,title,description,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,description=excluded.description,updated_at=excluded.updated_at').bind(id,user.id,b.title.trim(),b.description.trim(),Date.now()).run();return json({ok:true,id});
      }
    }
    if(path==='/api/avatar'&&request.method==='PUT') {
      if(!request.headers.get('Content-Type')?.startsWith('application/json'))return json({error:'请选择图片。'},415);
      const raw=await request.text();if(raw.length>100000)return json({error:'头像过大，请选择较小的图片。'},413);
      let image;try{image=JSON.parse(raw).image}catch{return json({error:'无效图片。'},400)}
      if(typeof image!=='string'||!/^data:image\/jpeg;base64,[A-Za-z0-9+/]+={0,2}$/.test(image))return json({error:'请选择有效图片。'},400);
      let bytes;try{bytes=Uint8Array.from(atob(image.split(',')[1]),c=>c.charCodeAt(0))}catch{return json({error:'无效图片。'},400)}
      let valid=false;
      if(bytes[0]===255&&bytes[1]===216&&bytes[bytes.length-2]===255&&bytes[bytes.length-1]===217){
        for(let i=2;i+8<bytes.length;){if(bytes[i]!==255)break;const marker=bytes[i+1],length=(bytes[i+2]<<8)|bytes[i+3];if(length<2||i+2+length>bytes.length)break;
          if([192,193,194].includes(marker)){const h=(bytes[i+5]<<8)|bytes[i+6],w=(bytes[i+7]<<8)|bytes[i+8];valid=w>0&&h>0&&w<=512&&h<=512;break;}i+=length+2;}
      }
      if(!valid)return json({error:'图片无法识别，请重新选择。'},400);
      await avatarTable(env.DB);await env.DB.prepare('INSERT INTO avatars(user_id,image) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET image=excluded.image').bind(user.id,image).run();return json({ok:true});
    }
    if(path==='/api/profile'||path==='/api/favorites') {
      await spaces(env.DB);
      if(path==='/api/profile') {
        if(request.method==='GET')return json({profile:await profileFor(env.DB,user)});
        if(request.method==='PUT') {
          const b=await bodyJSON(request);
          if(!b||typeof b.name!=='string'||!b.name.trim()||b.name.trim().length>40||typeof b.bio!=='string'||b.bio.length>300||!['github','lilac','sea','peach'].includes(b.avatar))return json({error:'昵称请填 1–40 字，简介不超过 300 字，并选择头像。'},400);
          await env.DB.prepare('INSERT INTO profiles(user_id,nickname,bio,avatar) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET nickname=excluded.nickname,bio=excluded.bio,avatar=excluded.avatar').bind(user.id,b.name.trim(),b.bio.trim(),b.avatar).run();
          return json({profile:await profileFor(env.DB,user)});
        }
      } else {
        if(request.method==='GET')return json({items:(await env.DB.prepare('SELECT work_id AS id,created_at AS date FROM favorites WHERE user_id=? ORDER BY created_at DESC').bind(user.id).all()).results});
        if(['POST','DELETE'].includes(request.method)) {
          const b=await bodyJSON(request);
          if(!b||(!ids.has(b.id)&&b.id!=='city'&&!await isPublished(env.DB,b.id)))return json({error:'找不到这件作品。'},400);
          if(request.method==='POST')await env.DB.prepare('INSERT INTO favorites(user_id,work_id,created_at) VALUES(?,?,?) ON CONFLICT(user_id,work_id) DO NOTHING').bind(user.id,b.id,Date.now()).run();
          else await env.DB.prepare('DELETE FROM favorites WHERE user_id=? AND work_id=?').bind(user.id,b.id).run();
          return json({ok:true});
        }
      }
    }
    if(path==='/api/logout'&&request.method==='POST') {
      await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(await hash(cookies(request)['__Host-ccbcm-session'])).run();
      const response=json({ok:true});response.headers.append('Set-Cookie',cookie('__Host-ccbcm-session','',0));return response;
    }
    if(path==='/api/downloads'&&request.method==='GET') {
      const result=await env.DB.prepare('SELECT work_id AS id,created_at AS date FROM downloads WHERE user_id=? ORDER BY created_at DESC').bind(user.id).all();return json({items:result.results});
    }
    if(path==='/api/downloads'&&request.method==='POST') {
      if(!request.headers.get('Content-Type')?.startsWith('application/json'))return json({error:'无效请求。'},415);
      const body=await request.text();if(body.length>256)return json({error:'请求过大。'},413);
      let id;try{id=JSON.parse(body).id;}catch{return json({error:'无效请求。'},400);}
      if(!ids.has(id)&&!await isPublished(env.DB,id))return json({error:'找不到这张壁纸。'},404);
      await env.DB.prepare('INSERT INTO downloads(user_id,work_id,created_at) VALUES(?,?,?) ON CONFLICT(user_id,work_id) DO NOTHING').bind(user.id,id,Date.now()).run();return json({ok:true});
    }
    return json({error:'找不到这个操作。'},404);
  }catch(error){const reason=['bad_verification_code','incorrect_client_credentials','redirect_uri_mismatch','token_exchange_failed'].includes(error.message)?error.message:stage;console.error('CCBCM_AUTH_FAILURE',reason);if(path==='/api/auth/callback')return redirect(ORIGIN+'/?login=failed&reason='+reason+'#downloads',[cookie('__Host-ccbcm-state','',0)]);return json({error:'登录暂时未完成，请从网站重新发起登录。',code:reason},503);}
}
