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
async function profileFor(db,user) {
  const p=await db.prepare('SELECT nickname,bio,avatar FROM profiles WHERE user_id=?').bind(user.id).first();
  return {login:user.login,name:p?.nickname||user.name,bio:p?.bio||'',avatar:p?.avatar||'github',avatarUrl:/^[0-9]+$/.test(user.id)?'https://avatars.githubusercontent.com/u/'+user.id+'?s=160':null};
}
async function bodyJSON(request) {
  if(!request.headers.get('Content-Type')?.startsWith('application/json'))return null;
  const text=await request.text();if(text.length>4096)return null;
  try{const value=JSON.parse(text);return value&&typeof value==='object'&&!Array.isArray(value)?value:null}catch{return null}
}
export async function onRequest({request,env}) {
  const url=new URL(request.url),path=url.pathname;
  const ready=!!(env.DB&&env.GITHUB_CLIENT_ID&&env.GITHUB_CLIENT_SECRET);
  if(path==='/api/account'&&request.method==='GET') {
    if(!ready)return json({user:null,ready:false});
    try{return json({user:await current(request,env.DB),ready:true});}catch{return json({error:'账号服务暂时不可用，请稍后重试。'},503);}
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
    if(path.startsWith('/api/people/')&&request.method==='GET') {
      const login=path.slice('/api/people/'.length);
      if(!/^[a-zA-Z0-9-]{1,39}$/.test(login))return json({error:'找不到这位创作者。'},404);
      const person=await env.DB.prepare('SELECT id,login,name FROM users WHERE lower(login)=lower(?)').bind(login).first();
      if(!person)return json({error:'找不到这位创作者。'},404);
      await spaces(env.DB);return json({profile:await profileFor(env.DB,person)});
    }
    const user=await current(request,env.DB);if(!user)return json({error:'请先登录 GitHub。'},401);
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
          if(!b||(!ids.has(b.id)&&b.id!=='city'))return json({error:'找不到这件作品。'},400);
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
      if(!ids.has(id))return json({error:'找不到这张壁纸。'},404);
      await env.DB.prepare('INSERT INTO downloads(user_id,work_id,created_at) VALUES(?,?,?) ON CONFLICT(user_id,work_id) DO NOTHING').bind(user.id,id,Date.now()).run();return json({ok:true});
    }
    return json({error:'找不到这个操作。'},404);
  }catch(error){const reason=['bad_verification_code','incorrect_client_credentials','redirect_uri_mismatch','token_exchange_failed'].includes(error.message)?error.message:stage;console.error('CCBCM_AUTH_FAILURE',reason);if(path==='/api/auth/callback')return redirect(ORIGIN+'/?login=failed&reason='+reason+'#downloads',[cookie('__Host-ccbcm-state','',0)]);return json({error:'登录暂时未完成，请从网站重新发起登录。',code:reason},503);}
}
