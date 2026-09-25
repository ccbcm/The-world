const ORIGIN = 'https://ccbcm.net';
const ids = new Set(['blue','cat','lines','caffeine','tux']);
const json = (body,status=200) => new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const random = () => Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
const hash = async value => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),b=>b.toString(16).padStart(2,'0')).join('');
const cookie = (name,value,age) => `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${age}`;
function cookies(request) { return Object.fromEntries((request.headers.get('Cookie')||'').split(';').map(s=>s.trim().split('='))); }
function redirect(url, values=[]) { const headers=new Headers({'Location':url,'Cache-Control':'no-store','Referrer-Policy':'no-referrer'}); for(const value of values)headers.append('Set-Cookie',value);return new Response(null,{status:302,headers}); }
export async function current(request,db) { const token=cookies(request)['__Host-ccbcm-session'];if(!token||!/^[a-f0-9]{64}$/.test(token))return null;return db.prepare('SELECT users.id, users.login, users.name FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>?').bind(await hash(token),Date.now()).first(); }
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
const VIDEO_MAX=200*1024*1024, PART_SIZE=8*1024*1024;
async function isPublished(db,id){if(typeof id!=='string'||!/^[a-f0-9]{64}$/.test(id))return false;await videoTable(db);return !!await db.prepare("SELECT id FROM creator_videos WHERE id=? AND state='published'").bind(id).first();}
const isReviewer=(env,user)=>!!user&&!!env.ADMIN_GITHUB_ID&&String(user.id)===String(env.ADMIN_GITHUB_ID);
async function creatorTable(db){await db.prepare("CREATE TABLE IF NOT EXISTS creator_access (user_id TEXT PRIMARY KEY REFERENCES users(id), status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL DEFAULT '', updated_at INTEGER NOT NULL)").bind().run();}
async function creatorAccess(env,user){if(!user)return {status:'none'};if(isReviewer(env,user))return {status:'approved'};await creatorTable(env.DB);return await env.DB.prepare('SELECT status,note,reason FROM creator_access WHERE user_id=?').bind(user.id).first()||{status:'none'};}
async function creatorPermissions(request,env,user,path){
 await creatorTable(env.DB);
 if(path==='/api/creator-application'){
  if(request.method==='GET')return json(await creatorAccess(env,user));
  if(request.method!=='POST')return json({error:'不支持这个操作。'},405);
  const b=await bodyJSON(request);if(!b||typeof b.note!=='string'||!b.note.trim()||b.note.length>500)return json({error:'请简单介绍想分享的作品，最多500字。'},400);
  if(isReviewer(env,user))return json({error:'你已经是创作者。'},409);
  const result=await env.DB.prepare("INSERT INTO creator_access(user_id,status,note,reason,updated_at) VALUES(?,'pending',?,'',?) ON CONFLICT(user_id) DO UPDATE SET status='pending',note=excluded.note,reason='',updated_at=excluded.updated_at WHERE creator_access.status='rejected'").bind(user.id,b.note.trim(),Date.now()).run();
  return changed(result)?json({ok:true,status:'pending'}):json({error:'申请已提交或已经通过。'},409);
 }
 if(!isReviewer(env,user))return json({error:'只有 CCBCM 可以审核创作者。'},403);
 if(path==='/api/creator-applications'&&request.method==='GET')return json({items:(await env.DB.prepare("SELECT a.user_id,a.status,a.note,a.reason,u.login,u.name FROM creator_access a JOIN users u ON u.id=a.user_id ORDER BY CASE WHEN a.status='pending' THEN 0 ELSE 1 END,a.updated_at DESC LIMIT 200").bind().all()).results});
 const match=path.match(/^\/api\/creator-applications\/([^/]+)$/);if(!match||request.method!=='POST')return json({error:'找不到申请。'},404);
 const b=await bodyJSON(request);if(!b||!['approved','rejected'].includes(b.status)||typeof b.reason!=='string'||b.reason.length>500||(b.status==='rejected'&&!b.reason.trim()))return json({error:'退回时请填写原因，最多500字。'},400);
 const result=await env.DB.prepare("UPDATE creator_access SET status=?,reason=?,updated_at=? WHERE user_id=? AND status='pending'").bind(b.status,b.reason.trim(),Date.now(),decodeURIComponent(match[1])).run();return changed(result)?json({ok:true}):json({error:'申请已处理，请刷新。'},409);
}
async function reviewTable(db){await db.prepare("CREATE TABLE IF NOT EXISTS video_reviews (video_id TEXT PRIMARY KEY, decision TEXT NOT NULL, reason TEXT NOT NULL, reviewer_id TEXT NOT NULL, reviewed_at INTEGER NOT NULL)").bind().run();}
async function moderation(request,env,user,path){
 if(!isReviewer(env,user))return json({error:'只有网站管理员可以审核作品。'},403);
 await videoTable(env.DB);await reviewTable(env.DB);const db=env.DB;
 if(path==='/api/moderation'&&request.method==='GET')return json({items:(await db.prepare("SELECT v.id,v.title,v.description,v.poster,v.size,COALESCE((SELECT mime FROM wallpaper_media WHERE id=v.id),'video/mp4') AS mime,v.state,v.updated_at,u.login,r.reason,r.decision FROM creator_videos v JOIN users u ON u.id=v.user_id LEFT JOIN video_reviews r ON r.video_id=v.id WHERE v.state IN ('review','approved','ready','published','unlisted') AND (v.state!='ready' OR r.video_id IS NOT NULL) ORDER BY CASE WHEN v.state='review' THEN 0 ELSE 1 END,v.updated_at DESC").bind().all()).results});
 const m=path.match(/^\/api\/moderation\/([a-f0-9]{64})(\/(?:content|cover))?$/);if(!m)return json({error:'找不到这件作品。'},404);
 const row=await db.prepare('SELECT * FROM creator_videos WHERE id=?').bind(m[1]).first();if(!row)return json({error:'找不到这件作品。'},404);
 if(m[2]&&request.method==='GET')return handleVideos(request,env,{id:row.user_id},'/api/videos/'+row.id+m[2]);
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
async function videoTable(db){await db.prepare("CREATE TABLE IF NOT EXISTS wallpaper_covers (id TEXT PRIMARY KEY,width INTEGER NOT NULL,height INTEGER NOT NULL,version TEXT NOT NULL)").bind().run();await db.prepare("CREATE TABLE IF NOT EXISTS wallpaper_media (id TEXT PRIMARY KEY,mime TEXT NOT NULL,upload_id TEXT,parts TEXT NOT NULL DEFAULT '{}')").bind().run();await db.prepare(`CREATE TABLE IF NOT EXISTS creator_videos (
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
function imageHeader(b,mime){
 if(mime==='image/png')return b.length>=33&&[137,80,78,71,13,10,26,10].every((v,i)=>b[i]===v)&&String.fromCharCode(...b.slice(12,16))==='IHDR'&&new DataView(b.buffer,b.byteOffset).getUint32(16)>0&&new DataView(b.buffer,b.byteOffset).getUint32(20)>0;
 return mime==='image/jpeg'&&b.length>=32&&b[0]===255&&b[1]===216&&b[2]===255;
}
// Scan top-level MP4 boxes while hashing the R2 stream. Memory is bounded by a stream chunk.
async function verifyWallpaper(object,row){
 const digest=new crypto.DigestStream('SHA-256'),writer=digest.getWriter(),reader=object.body.getReader();digest.digest.catch(()=>{});
 let total=0,skip=0,header=[],first=[],tail=new Uint8Array(),boxCount=0;const boxes=new Set();
 try{while(true){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>row.size)throw Error('文件大小不符。');
  if(first.length<40)first.push(...value.slice(0,40-first.length));
  if(!['video/mp4','video/quicktime'].includes(row.mime)){const end=new Uint8Array(tail.length+Math.min(value.length,12));end.set(tail);end.set(value.slice(-12),tail.length);tail=end.slice(-12);}
  await writer.write(value);
  if(['video/mp4','video/quicktime'].includes(row.mime)){let i=0;while(i<value.length){if(skip){const n=Math.min(skip,value.length-i);skip-=n;i+=n;continue;}header.push(value[i++]);if(header.length===8||header.length===16){const b=new Uint8Array(header),v=new DataView(b.buffer);let size=v.getUint32(0);if(size===1&&header.length===8)continue;if(size===1){if(v.getUint32(8)!==0)throw Error('MP4 结构无效。');size=v.getUint32(12);}if(size===0)size=row.size-(total-value.length+i-header.length);if(size<header.length||size>row.size||++boxCount>10000)throw Error('MP4 结构无效。');boxes.add(String.fromCharCode(...b.slice(4,8)));skip=size-header.length;header=[];}}}
 }
 await writer.close();const sha=Array.from(new Uint8Array(await digest.digest),b=>b.toString(16).padStart(2,'0')).join('');
 if(total!==row.size||sha!==row.sha256)throw Error('文件校验未通过，请重新选择原文件。');
 if(['video/mp4','video/quicktime'].includes(row.mime)?(skip!==0||header.length!==0||!(row.mime==='video/quicktime'?['moov','mdat']:['ftyp','moov','mdat']).every(x=>boxes.has(x))):row.mime.startsWith('video/')?![26,69,223,163].every((v,i)=>first[i]===v):!imageHeader(new Uint8Array(first),row.mime)||!(row.mime==='image/jpeg'?tail.at(-2)===255&&tail.at(-1)===217:tail.length===12&&String.fromCharCode(...tail.slice(4,8))==='IEND'))throw Error('文件格式无效，请重新导出。');
 }catch(e){await reader.cancel().catch(()=>{});await writer.abort().catch(()=>{});throw e;}
}
async function multipartWallpaper(request,db,bucket,row,meta,key,action){
 const method=request.method;
 if(action==='begin'&&method==='POST'){
  if(['ready','review','approved','published','unlisted'].includes(row.state))return json({ready:true});
  if(row.state==='uploading'&&meta?.upload_id&&row.updated_at>Date.now()-15*60000)return json({partSize:PART_SIZE,parts:JSON.parse(meta.parts),uploadId:meta.upload_id});
  const lock=await db.prepare("UPDATE creator_videos SET state='uploading',updated_at=? WHERE id=? AND (state IN ('reserved','failed') OR (state IN ('uploading','verifying') AND updated_at<?))").bind(Date.now(),row.id,Date.now()-15*60000).run();if(!changed(lock))return json({error:'正在保存，请稍后重试。'},409);
  try{if(meta?.upload_id)await bucket.resumeMultipartUpload(key,meta.upload_id).abort().catch(()=>{});
   const upload=await bucket.createMultipartUpload(key,{httpMetadata:{contentType:row.mime}});
   await db.prepare("INSERT INTO wallpaper_media(id,mime,upload_id,parts) VALUES(?,?,?,'{}') ON CONFLICT(id) DO UPDATE SET upload_id=excluded.upload_id,parts='{}'").bind(row.id,row.mime,upload.uploadId).run();return json({partSize:PART_SIZE,parts:{},uploadId:upload.uploadId});
  }catch(e){await db.prepare("UPDATE creator_videos SET state='failed' WHERE id=?").bind(row.id).run();return json({error:'无法开始上传，请重试。'},503);}
 }
 if(!meta?.upload_id||row.state!=='uploading')return json({error:'请重新开始上传。'},409);
 const upload=bucket.resumeMultipartUpload(key,meta.upload_id);
 if(action==='part'&&method==='PUT'){
  const n=Number(new URL(request.url).searchParams.get('n')),count=Math.ceil(row.size/PART_SIZE);
  if(!Number.isInteger(n)||n<1||n>count||request.headers.get('X-Upload-Id')!==meta.upload_id)return json({error:'上传分块无效。'},400);
  const size=Math.min(PART_SIZE,row.size-(n-1)*PART_SIZE);
  try{const bytes=await limitedBody(request,size);if(bytes.length!==size)throw Error('分块不完整。');
   const part=await upload.uploadPart(n,bytes);
   // JSON patch preserves other parts when requests finish concurrently.
   const saved=await db.prepare("UPDATE wallpaper_media SET parts=json_set(parts,?,json(?)) WHERE id=? AND upload_id=? AND EXISTS(SELECT 1 FROM creator_videos WHERE id=? AND state='uploading')").bind('$."'+n+'"',JSON.stringify(part),row.id,meta.upload_id,row.id).run();if(!changed(saved))return json({error:'上传状态已改变，请重试。'},409);
   await db.prepare("UPDATE creator_videos SET updated_at=? WHERE id=? AND state='uploading'").bind(Date.now(),row.id).run();return json({ok:true});
  }catch(e){return json({error:e.message||'分块上传失败，请重试。'},400);}
 }
 if(action==='complete'&&method==='POST'){
  const parts=JSON.parse(meta.parts),count=Math.ceil(row.size/PART_SIZE);if(row.state==='uploading'&&Object.keys(parts).length!==count)return json({error:'尚有分块未完成，请重试。'},409);
  const retrying=row.state==='verifying';
  if(!['uploading','verifying'].includes(row.state))return json({error:'文件状态已改变，请刷新后再试。'},409);
  const lock=await db.prepare("UPDATE creator_videos SET state='verifying',updated_at=? WHERE id=? AND state IN ('uploading','verifying')").bind(Date.now(),row.id).run();if(!changed(lock))return json({error:'正在校验，请稍后刷新。'},409);
  try{if(!retrying)await upload.complete(Array.from({length:count},(_,i)=>parts[i+1]));const object=await bucket.get(key);if(!object)throw Error('文件暂时无法读取。');await verifyWallpaper(object,row);
   await db.prepare("UPDATE creator_videos SET state='ready',updated_at=? WHERE id=? AND state='verifying'").bind(Date.now(),row.id).run();return json({ok:true,state:'ready'});
  }catch(e){await bucket.delete(key).catch(()=>{});await upload.abort().catch(()=>{});await db.prepare("UPDATE creator_videos SET state='failed',updated_at=? WHERE id=? AND state='verifying'").bind(Date.now(),row.id).run();return json({error:e.message||'校验失败，请重试。'},400);}
 }
 return json({error:'不支持这个操作。'},405);
}
async function handleVideos(request,env,user,path){
 await videoTable(env.DB);await reviewTable(env.DB);const db=env.DB,bucket=env.CREATOR_ASSETS;
 if(!bucket)return json({error:'文件存储暂时不可用。'},503);
 if(path==='/api/videos'){
  if(request.method==='GET'){const items=(await db.prepare('SELECT id,title,description,size,sha256,poster,state,created_at,COALESCE((SELECT mime FROM wallpaper_media WHERE id=creator_videos.id),\'video/mp4\') AS mime,(SELECT reason FROM video_reviews WHERE video_id=creator_videos.id) AS review_reason FROM creator_videos WHERE user_id=? ORDER BY created_at DESC').bind(user.id).all()).results;return json({items,limits:{file:VIDEO_MAX}});}
  if(request.method==='POST'){
   const b=await videoJSON(request);if(!b||typeof b.title!=='string'||!b.title.trim()||b.title.length>100||!Number.isSafeInteger(b.size)||b.size<32||b.size>VIDEO_MAX||!['video/mp4','video/quicktime','video/webm','video/x-matroska','image/png','image/jpeg'].includes(b.mime||'video/mp4')||! /^[a-f0-9]{64}$/.test(b.sha256||''))return json({error:'请选择 200 MB 以内的 MP4、MOV、WebM、MKV、PNG 或 JPG，并填写标题。'},400);
   const poster=typeof b.poster==='string'?b.poster:'';if(poster.length>60000||poster&&!/^data:image\/jpeg;base64,\/9j\/[A-Za-z0-9+/=]+$/.test(poster))return json({error:'封面无效。'},400);
   const id=random(),now=Date.now();
   const [result]=await db.batch([db.prepare(`INSERT INTO creator_videos(id,user_id,title,size,sha256,poster,state,created_at,updated_at)
    SELECT ?,?,?,?,?,?,'reserved',?,? WHERE COALESCE((SELECT n FROM video_upload_daily WHERE user_id=? AND day=?),0)<20`).bind(id,user.id,b.title.trim(),b.size,b.sha256,poster,now,now,user.id,Math.floor(now/86400000)),db.prepare('INSERT INTO wallpaper_media(id,mime) SELECT ?,? WHERE EXISTS(SELECT 1 FROM creator_videos WHERE id=?)').bind(id,b.mime||'video/mp4',id)]);
   if(!changed(result))return json({error:'今天的新上传较多，请明天再试（每天最多 20 次）。'},429);
   return json({id,state:'reserved'});
  }
 }
 const match=path.match(/^\/api\/videos\/([a-f0-9]{64})(?:\/(content|cover|submit|publish|unlist|begin|part|complete))?$/);if(!match)return json({error:'找不到这件作品。'},404);
 const row=await db.prepare('SELECT * FROM creator_videos WHERE id=? AND user_id=?').bind(match[1],user.id).first();if(!row)return json({error:'找不到这件作品。'},404);const metadata=await db.prepare('SELECT * FROM wallpaper_media WHERE id=?').bind(row.id).first();row.mime=metadata?.mime||'video/mp4';const key='videos/'+row.user_id+'/'+row.id+'.mp4',action=match[2];
 if(['begin','part','complete'].includes(action))return multipartWallpaper(request,db,bucket,row,metadata,key,action);
 if(action==='cover'&&request.method==='PUT'){
  if(!['reserved','ready','unlisted','failed'].includes(row.state))return json({error:'请先下架作品，再修改封面并重新提交审核。'},409);
  const width=Number(request.headers.get('X-Media-Width')),height=Number(request.headers.get('X-Media-Height'));
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>16384||height>16384||request.headers.get('Content-Type')!=='image/jpeg')return json({error:'封面尺寸或格式无效。'},400);
  let bytes;try{bytes=await limitedBody(request,3*1024*1024);}catch{return json({error:'封面最多 3 MB。'},400);}
  if(!imageHeader(bytes,'image/jpeg')||bytes.at(-2)!==255||bytes.at(-1)!==217)return json({error:'封面格式无效。'},400);
  const version=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
  await bucket.put('covers/'+row.id+'/'+version+'.jpg',bytes,{httpMetadata:{contentType:'image/jpeg'}});
  const [,updated]=await db.batch([db.prepare("INSERT INTO wallpaper_covers(id,width,height,version) SELECT ?,?,?,? WHERE EXISTS(SELECT 1 FROM creator_videos WHERE id=? AND state IN ('reserved','ready','unlisted','failed')) ON CONFLICT(id) DO UPDATE SET width=excluded.width,height=excluded.height,version=excluded.version").bind(row.id,width,height,version,row.id),db.prepare("UPDATE creator_videos SET poster=?,updated_at=? WHERE id=? AND state IN ('reserved','ready','unlisted','failed')").bind('/api/published-videos/'+row.id+'/cover?v='+version,Date.now(),row.id)]);return changed(updated)?json({ok:true}):json({error:'作品状态已改变，请刷新。'},409);
 }
 if(action==='cover'&&request.method==='GET'){
  const cover=await db.prepare('SELECT version FROM wallpaper_covers WHERE id=?').bind(row.id).first();if(!cover)return json({error:'封面暂不可用。'},404);const object=await bucket.get('covers/'+row.id+'/'+cover.version+'.jpg');if(!object)return json({error:'封面暂不可用。'},404);
  return new Response(object.body,{headers:{'Content-Type':'image/jpeg','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
 }
 if(action==='content'&&request.method==='PUT'){
  if(['ready','review','approved','published','unlisted'].includes(row.state))return json({ok:true,state:row.state});
  const lock=await db.prepare("UPDATE creator_videos SET state='uploading',updated_at=? WHERE id=? AND (state IN ('reserved','failed') OR (state='uploading' AND updated_at<?))").bind(Date.now(),row.id,Date.now()-15*60000).run();if(!changed(lock))return json({error:'文件正在处理中，请稍后再试。'},409);
  try{
   if(row.size>PART_SIZE)throw Error('大文件请刷新网页后使用分块上传。');if(request.headers.get('Content-Type')!==row.mime)throw Error('文件类型不符。');
   const bytes=await limitedBody(request,Math.min(row.size,VIDEO_MAX));if(bytes.length!==row.size)throw Error('文件传输不完整，请重试。');
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');if(digest!==row.sha256)throw Error('文件与上次选择的不一致，请重新选择原文件。');
   if(['video/mp4','video/quicktime'].includes(row.mime)?!mp4Container(bytes):row.mime.startsWith('video/')?![26,69,223,163].every((v,i)=>bytes[i]===v):!imageHeader(bytes,row.mime))throw Error('无法识别文件结构，请重新导出。');
   await bucket.put(key,bytes,{httpMetadata:{contentType:row.mime}});
   await db.prepare("UPDATE creator_videos SET state='ready',updated_at=? WHERE id=?").bind(Date.now(),row.id).run();return json({ok:true,state:'ready'});
  }catch(e){await db.prepare("UPDATE creator_videos SET state='failed',updated_at=? WHERE id=?").bind(Date.now(),row.id).run();return json({error:e.message||'上传失败，请重试。'},400);}
 }
 if(action==='content'&&request.method==='GET'){
  if(!['ready','review','approved','published','unlisted'].includes(row.state))return json({error:'壁纸尚未上传完成。'},409);
  const range=request.headers.get('Range');let options={},start=0,end=row.size-1;
  if(range){const m=range.match(/^bytes=(\d*)-(\d*)$/);if(!m||!m[1]&&!m[2])return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+row.size}});if(m[1]){start=Number(m[1]);end=m[2]?Math.min(Number(m[2]),end):end;}else start=Math.max(0,row.size-Number(m[2]));if(start>end||start>=row.size)return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+row.size}});options={range:{offset:start,length:end-start+1}};}
  const object=await bucket.get(key,options);if(!object)return json({error:'壁纸暂时无法读取。'},404);
  const headers={'Content-Type':row.mime,'Content-Length':String(end-start+1),'Accept-Ranges':'bytes','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'};if(range)headers['Content-Range']=`bytes ${start}-${end}/${row.size}`;return new Response(object.body,{status:range?206:200,headers});
 }
 if(['publish','unlist'].includes(action)&&request.method==='POST'){
 const from=action==='publish'?'approved':'published',to=action==='publish'?'published':'unlisted';
 const result=await db.prepare('UPDATE creator_videos SET state=?,updated_at=? WHERE id=? AND user_id=? AND state=?').bind(to,Date.now(),row.id,user.id,from).run();
 return changed(result)?json({ok:true,state:to}):json({error:'作品状态已改变，请刷新后再试。'},409);
 }
 if(action==='submit'&&request.method==='POST'){
  if(!['ready','review','unlisted'].includes(row.state))return json({error:'请先完成壁纸上传。'},409);
  const update=await db.prepare("UPDATE creator_videos SET state='review',updated_at=? WHERE id=? AND state IN ('ready','review','unlisted')").bind(Date.now(),row.id).run();if(!changed(update))return json({error:'作品状态已改变，请刷新。'},409);return json({ok:true,state:'review'});
 }
 if(!action&&request.method==='PATCH'){
  if(['review','approved','published'].includes(row.state))return json({error:'审核中的作品暂时不能修改。'},409);
  const b=await videoJSON(request);if(!b||typeof b.title!=='string'||!b.title.trim()||b.title.length>100||typeof b.description!=='string'||b.description.length>1500)return json({error:'标题限 100 字，简介限 1500 字。'},400);
  await db.prepare('UPDATE creator_videos SET title=?,description=?,updated_at=? WHERE id=? AND state NOT IN ("review","approved","published","deleting")').bind(b.title.trim(),b.description.trim(),Date.now(),row.id).run();return json({ok:true});
 }
 if(!action&&request.method==='DELETE'){
  if(['uploading','verifying'].includes(row.state)&&row.updated_at>Date.now()-15*60000)return json({error:'壁纸正在上传，请稍后再移除。'},409);
  const lock=await db.prepare("UPDATE creator_videos SET state='deleting' WHERE id=? AND state!='deleting' AND (state NOT IN ('uploading','verifying') OR updated_at<?)").bind(row.id,Date.now()-15*60000).run();if(!changed(lock))return json({error:'文件处理中，请稍后再移除。'},409);
  try{if(metadata?.upload_id)await bucket.resumeMultipartUpload(key,metadata.upload_id).abort().catch(()=>{});await bucket.delete(key);await db.batch([db.prepare("DELETE FROM creator_videos WHERE id=? AND user_id=? AND state='deleting'").bind(row.id,user.id),db.prepare('DELETE FROM wallpaper_media WHERE id=?').bind(row.id)]);return json({ok:true});}catch{await db.prepare("UPDATE creator_videos SET state=? WHERE id=? AND state='deleting'").bind(row.state,row.id).run();return json({error:'移除失败，请重试。'},503);}
 }
 return json({error:'不支持这个操作。'},405);
}
async function discoveryClicks(request,env){
 const db=env.DB,day=Math.floor((Date.now()+8*3600000)/86400000);
 await videoTable(db);
 await db.prepare('CREATE TABLE IF NOT EXISTS discovery_clicks (day INTEGER NOT NULL,work_id TEXT NOT NULL,visitor TEXT NOT NULL,PRIMARY KEY(day,work_id,visitor))').bind().run();
 if(request.method==='GET'){
  const items=(await db.prepare("SELECT work_id AS id,COUNT(*) AS clicks FROM discovery_clicks WHERE day=? AND (work_id IN ('blue','cat','lines','caffeine','tux') OR EXISTS(SELECT 1 FROM creator_videos WHERE id=work_id AND state='published')) GROUP BY work_id ORDER BY clicks DESC,work_id LIMIT 2000").bind(day).all()).results;
  return json({day,items});
 }
 if(request.method!=='POST')return json({error:'不支持这个操作。'},405);
 const b=await bodyJSON(request);if(!b||typeof b.id!=='string'||!ids.has(b.id)&&!await isPublished(db,b.id))return json({error:'作品未公开。'},404);
 // Count intentional detail opens, never autoplay/impressions. Only a daily salted digest is stored.
 const ip=request.headers.get('CF-Connecting-IP');if(!ip)return json({ok:true});
 const visitor=await hash(day+'|'+env.GITHUB_CLIENT_SECRET+'|'+ip+'|'+(request.headers.get('User-Agent')||'').slice(0,256));
 await db.prepare('INSERT OR IGNORE INTO discovery_clicks(day,work_id,visitor) VALUES(?,?,?)').bind(day,b.id,visitor).run();
 if(Math.random()<0.02)await db.prepare('DELETE FROM discovery_clicks WHERE day<?').bind(day-7).run();
 return json({ok:true});
}
async function emailTables(db){
 await db.prepare('CREATE TABLE IF NOT EXISTS email_accounts (email TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),created_at INTEGER NOT NULL)').bind().run();
 await db.prepare('CREATE TABLE IF NOT EXISTS email_codes (id TEXT PRIMARY KEY,email TEXT NOT NULL,code_hash TEXT NOT NULL,expires_at INTEGER NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,used_at INTEGER,created_at INTEGER NOT NULL)').bind().run();
 await db.prepare('CREATE INDEX IF NOT EXISTS email_codes_lookup ON email_codes(email,created_at)').bind().run();
 await db.prepare('CREATE TABLE IF NOT EXISTS auth_identities (provider TEXT NOT NULL,provider_id TEXT NOT NULL,user_id TEXT NOT NULL REFERENCES users(id),email TEXT NOT NULL DEFAULT "",created_at INTEGER NOT NULL,PRIMARY KEY(provider,provider_id))').bind().run();
 await db.prepare('CREATE INDEX IF NOT EXISTS auth_identities_email ON auth_identities(email)').bind().run();
}
function normalizeEmail(value){return typeof value==='string'?value.trim().toLowerCase():'';}
function supportedEmail(email){return /^[^\s@]{1,80}@(gmail\.com|googlemail\.com|qq\.com|foxmail\.com)$/i.test(email);}
async function sendEmailCode(env,email,code){
 if(!env.RESEND_API_KEY||!env.EMAIL_FROM)throw Error('邮箱登录服务尚未配置发信地址。');
 const response=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:'Bearer '+env.RESEND_API_KEY,'Content-Type':'application/json'},body:JSON.stringify({from:env.EMAIL_FROM,to:[email],subject:'CCBCM 登录验证码',text:`你的 CCBCM 登录验证码是 ${code}，10 分钟内有效。如非本人操作，请忽略此邮件。`})});
 if(!response.ok)throw Error('验证码邮件发送失败，请稍后重试。');
}
async function emailAuth(request,env,path){
 await emailTables(env.DB);
 if(request.method!=='POST')return json({error:'不支持这个操作。'},405);
 const body=await bodyJSON(request),email=normalizeEmail(body?.email);
 if(!supportedEmail(email))return json({error:'请输入 Gmail 或 QQ 邮箱地址。'},400);
 if(path==='/api/auth/email/request'){
  const recent=await env.DB.prepare('SELECT id FROM email_codes WHERE email=? AND created_at>? AND used_at IS NULL ORDER BY created_at DESC LIMIT 1').bind(email,Date.now()-60000).first();
  if(recent)return json({error:'验证码已发送，请稍后再试。'},429);
  const code=String(Math.floor(100000+Math.random()*900000)),id=random();
  try{await sendEmailCode(env,email,code);await env.DB.prepare('INSERT INTO email_codes(id,email,code_hash,expires_at,created_at) VALUES(?,?,?,?,?)').bind(id,email,await hash(code),Date.now()+10*60000,Date.now()).run();return json({ok:true});}catch(error){return json({error:error.message||'验证码发送失败。'},503);}
 }
 if(path==='/api/auth/email/verify'){
  const code=typeof body?.code==='string'?body.code.trim():'';if(!/^\d{6}$/.test(code))return json({error:'请输入 6 位验证码。'},400);
  const row=await env.DB.prepare('SELECT * FROM email_codes WHERE email=? AND used_at IS NULL ORDER BY created_at DESC LIMIT 1').bind(email).first();
  if(!row||row.expires_at<Date.now()||row.attempts>=5)return json({error:'验证码已失效，请重新获取。'},400);
  if(await hash(code)!==row.code_hash){await env.DB.prepare('UPDATE email_codes SET attempts=attempts+1 WHERE id=?').bind(row.id).run();return json({error:'验证码不正确。'},400);}
  const existing=await env.DB.prepare('SELECT user_id FROM email_accounts WHERE email=?').bind(email).first();
  const identity=await env.DB.prepare('SELECT user_id FROM auth_identities WHERE lower(email)=lower(?) ORDER BY created_at LIMIT 1').bind(email).first();
  const userId=existing?.user_id||identity?.user_id||'email:'+await hash(email),login='email-'+(await hash(email)).slice(0,16),name=email.split('@')[0].slice(0,40);
  await env.DB.batch([env.DB.prepare('INSERT INTO users(id,login,name,created_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=CASE WHEN users.name LIKE "email-%" THEN excluded.name ELSE users.name END').bind(userId,login,name,Date.now()),env.DB.prepare('INSERT INTO email_accounts(email,user_id,created_at) VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET user_id=excluded.user_id').bind(email,userId,Date.now()),env.DB.prepare('UPDATE email_codes SET used_at=? WHERE id=?').bind(Date.now(),row.id)]);
  const session=random();await env.DB.prepare('DELETE FROM sessions WHERE expires_at<?').bind(Date.now()).run();await env.DB.prepare('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)').bind(await hash(session),userId,Date.now()+30*86400000).run();
  return redirect(ORIGIN+'/#downloads',[cookie('__Host-ccbcm-session',session,30*86400)]);
 }
 return json({error:'找不到这个操作。'},404);
}
export async function onRequest({request,env}) {
  const url=new URL(request.url),path=url.pathname;
  const ready=!!(env.DB&&env.GITHUB_CLIENT_ID&&env.GITHUB_CLIENT_SECRET);
  if(path==='/api/account'&&request.method==='GET') {
    if(!ready)return json({user:null,ready:false});
    try{const user=await current(request,env.DB);return json({user,ready:true,reviewer:isReviewer(env,user),creator:await creatorAccess(env,user)});}catch{return json({error:'账号服务暂时不可用，请稍后重试。'},503);}
  }
  if(!ready)return json({error:'GitHub 登录正在配置，请稍后再来。'},503);
  if(url.origin!==ORIGIN)return json({error:'请在 ccbcm.net 使用账号功能。'},403);
  if(request.method!=='GET'&&request.headers.get('Origin')!==ORIGIN)return json({error:'请求来源不符。'},403);
  let stage="session";
  try {
    if(path==='/api/discovery')return await discoveryClicks(request,env);
    if(path==='/api/auth/email/request'||path==='/api/auth/email/verify')return await emailAuth(request,env,path);
    if(path==='/api/auth/github'&&request.method==='GET') {
      const state=random();const auth=new URL('https://github.com/login/oauth/authorize');auth.searchParams.set('client_id',env.GITHUB_CLIENT_ID);auth.searchParams.set('redirect_uri',ORIGIN+'/api/auth/callback');auth.searchParams.set('scope','read:user user:email');auth.searchParams.set('state',state);
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
      const emailResponse=await fetch('https://api.github.com/user/emails',{headers:{'Authorization':'Bearer '+token.access_token,'User-Agent':'CCBCM','Accept':'application/vnd.github+json'}});
      const emails=await emailResponse.json();const verifiedEmail=Array.isArray(emails)?emails.find(x=>x&&x.verified&&x.primary)?.email||emails.find(x=>x&&x.verified)?.email||'':'';
      stage='database';
      await emailTables(env.DB);
      const knownIdentity=await env.DB.prepare('SELECT user_id FROM auth_identities WHERE provider=? AND provider_id=?').bind('github',String(user.id)).first();
      const knownEmail=verifiedEmail?await env.DB.prepare('SELECT user_id FROM email_accounts WHERE lower(email)=lower(?)').bind(verifiedEmail.toLowerCase()).first():null;
      const userId=knownIdentity?.user_id||knownEmail?.user_id||String(user.id);
      const session=random();await env.DB.batch([
        env.DB.prepare('INSERT INTO users(id,login,name,created_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET login=excluded.login,name=excluded.name').bind(userId,user.login,user.name||user.login,Date.now()),
        env.DB.prepare('INSERT INTO auth_identities(provider,provider_id,user_id,email,created_at) VALUES(?,?,?,?,?) ON CONFLICT(provider,provider_id) DO UPDATE SET user_id=excluded.user_id,email=excluded.email').bind('github',String(user.id),userId,(verifiedEmail||'').toLowerCase(),Date.now()),
        ...(verifiedEmail?[env.DB.prepare('INSERT INTO email_accounts(email,user_id,created_at) VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET user_id=excluded.user_id').bind(verifiedEmail.toLowerCase(),userId,Date.now())]:[]),
        env.DB.prepare('DELETE FROM sessions WHERE expires_at<?').bind(Date.now()),
        env.DB.prepare('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)').bind(await hash(session),userId,Date.now()+30*86400000)
      ]);
      return redirect(ORIGIN+'/#downloads',[cookie('__Host-ccbcm-state','',0),cookie('__Host-ccbcm-session',session,30*86400)]);
    }
    if(path==='/api/published-videos'&&request.method==='GET'){
      await videoTable(env.DB);return json({items:(await env.DB.prepare("SELECT v.id,v.title,v.description,v.poster,v.size,c.width,c.height,COALESCE((SELECT mime FROM wallpaper_media WHERE id=v.id),'video/mp4') AS mime,u.login FROM creator_videos v JOIN users u ON u.id=v.user_id LEFT JOIN wallpaper_covers c ON c.id=v.id WHERE v.state='published' ORDER BY v.updated_at DESC").bind().all()).results});
    }
    if(path==='/api/published-videos/blue/manifest'&&request.method==='GET')return json({sha256:'c14abe7d5151c4e4195bdd1c934899952cd594bd4500dafb965a8b131f5c70de',size:382493,mime:'video/mp4'});
    const staticMatch=path.match(/^\/api\/published-videos\/(cat|lines|caffeine|tux)\/manifest$/);
    if(staticMatch&&request.method==='GET')return json(({"cat": {"sha256": "ee71ada72d5e0649274453d926ac229f91a46a92936af0e274346458fccc6137", "size": 204031}, "lines": {"sha256": "4d1d69b3fab9eb3f0779f6f15dfde918c99e2a2b53878d7badc7abae5744523b", "size": 1542233}, "caffeine": {"sha256": "aa4084a66cf240ac336604916d86e62133a87c0c3355717b26fa63dda2c4b20d", "size": 216647}, "tux": {"sha256": "7265a930a86724c4018712ceb7b9d5c475c205b7672a8fbd33f9343b560124dd", "size": 220612}})[staticMatch[1]]);
    const manifest=path.match(/^\/api\/published-videos\/([a-f0-9]{64})\/manifest$/);
    if(manifest&&request.method==='GET'){await videoTable(env.DB);const row=await env.DB.prepare("SELECT sha256,size,COALESCE((SELECT mime FROM wallpaper_media WHERE id=creator_videos.id),'video/mp4') AS mime FROM creator_videos WHERE id=? AND state='published'").bind(manifest[1]).first();return row?json(row):json({error:'壁纸未上架或已下架。'},404);}
    const publicVideo=path.match(/^\/api\/published-videos\/([a-f0-9]{64})\/(content|cover)$/);
    if(publicVideo&&request.method==='GET'){
      await videoTable(env.DB);const row=await env.DB.prepare("SELECT user_id FROM creator_videos WHERE id=? AND state='published'").bind(publicVideo[1]).first();
      if(!row)return json({error:'作品尚未公开或已下架。'},404);
      return await handleVideos(request,env,{id:row.user_id},'/api/videos/'+publicVideo[1]+'/'+publicVideo[2]);
    }
    if(path==='/api/creators'&&request.method==='GET'){
      await creatorTable(env.DB);await spaces(env.DB);await avatarTable(env.DB);await videoTable(env.DB);
      const rows=(await env.DB.prepare("SELECT u.id,u.login,u.name,p.nickname,p.bio,p.avatar,a.image,(SELECT COUNT(*) FROM creator_videos v WHERE v.user_id=u.id AND v.state='published') AS published_count FROM users u LEFT JOIN profiles p ON p.user_id=u.id LEFT JOIN avatars a ON a.user_id=u.id LEFT JOIN creator_access c ON c.user_id=u.id WHERE u.id=? OR c.status='approved' ORDER BY CASE WHEN u.id=? THEN 0 ELSE 1 END,lower(u.login) LIMIT 200").bind(env.ADMIN_GITHUB_ID||'',env.ADMIN_GITHUB_ID||'').all()).results;
      return json({items:rows.map(p=>({login:p.login,name:p.nickname||p.name,bio:p.bio||'',avatar:p.avatar||'github',customAvatar:!!p.image,avatarUrl:p.image||(/^[0-9]+$/.test(p.id)?'https://avatars.githubusercontent.com/u/'+p.id+'?s=160':null),publishedCount:p.published_count+(p.login.toLowerCase()==='ccbcm'?5:0)}))});
    }
    if(path.startsWith('/api/people/')&&request.method==='GET') {
      const login=path.slice('/api/people/'.length);
      if(!/^[a-zA-Z0-9-]{1,39}$/.test(login))return json({error:'找不到这位创作者。'},404);
      const person=await env.DB.prepare('SELECT id,login,name FROM users WHERE lower(login)=lower(?)').bind(login).first();
      if(!person)return json({error:'找不到这位创作者。'},404);
      await spaces(env.DB);return json({profile:await profileFor(env.DB,person)});
    }
    const user=await current(request,env.DB);if(!user)return json({error:'请先登录 GitHub。'},401);
    if(path==='/api/creator-application'||path==='/api/creator-applications'||path.startsWith('/api/creator-applications/'))return await creatorPermissions(request,env,user,path);
    const creatorWrite=(path==='/api/drafts'&&request.method==='POST')||((path==='/api/videos'||path.startsWith('/api/videos/'))&&['POST','PUT','PATCH'].includes(request.method)&&!path.endsWith('/unlist'));
    if(creatorWrite&&(await creatorAccess(env,user)).status!=='approved')return json({error:'请先申请创作者，通过审核后即可上传和发布。'},403);
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
          if(!b||typeof b.id!=='string'||!/^[a-z0-9-]{1,64}$/.test(b.id)||(request.method==='POST'&&!ids.has(b.id)&&!await isPublished(env.DB,b.id)))return json({error:'找不到这件作品。'},400);
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
    if(path==='/api/library'&&request.method==='GET'){
      await spaces(env.DB);
      const items=(await env.DB.prepare(`SELECT work_id AS id,MAX(downloaded) AS downloaded,MAX(favorite) AS favorite,MAX(date) AS date FROM (
       SELECT work_id,1 AS downloaded,0 AS favorite,created_at AS date FROM downloads WHERE user_id=?
       UNION ALL SELECT work_id,0 AS downloaded,1 AS favorite,created_at AS date FROM favorites WHERE user_id=?
      ) GROUP BY work_id ORDER BY favorite DESC,date DESC,work_id`).bind(user.id,user.id).all()).results;
      return json({items:items.filter(x=>!['waves','clouds','net','city'].includes(x.id))});
    }
    if(path==='/api/downloads'&&request.method==='GET') {
      const result=await env.DB.prepare('SELECT work_id AS id,created_at AS date FROM downloads WHERE user_id=? ORDER BY created_at DESC').bind(user.id).all();return json({items:result.results.filter(x=>!['waves','clouds','net','city'].includes(x.id))});
    }
    if(path==='/api/downloads'&&request.method==='DELETE'){
      const b=await bodyJSON(request);if(!b||typeof b.id!=='string'||!/^[a-z0-9-]{1,64}$/.test(b.id))return json({error:'无效作品。'},400);
      await env.DB.prepare('DELETE FROM downloads WHERE user_id=? AND work_id=?').bind(user.id,b.id).run();return json({ok:true});
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
