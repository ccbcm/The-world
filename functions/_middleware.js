import { current } from './api/[[path]].js';
export async function onRequest(context){
 const path=new URL(context.request.url).pathname.replace(/\/+$/,'');
 const cover=path.match(/^\/gallery\/media\/hd\/([a-f0-9]{64})\.jpg$/);
 if(cover){try{const row=await context.env.DB.prepare("SELECT id FROM creator_videos WHERE id=? AND state='published'").bind(cover[1]).first();if(!row)return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});const response=await context.next();const headers=new Headers(response.headers);headers.set('Cache-Control','private, no-store');return new Response(response.body,{status:response.status,headers});}catch{return new Response('Unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}}
 if(path!=='/city'&&path!=='/city.html')return context.next();
 try{
  const user=context.env.DB?await current(context.request,context.env.DB):null;
  if(!user||String(user.id)!=='325610429')return new Response('此作品不公开。',{status:404,headers:{'Cache-Control':'no-store','Content-Type':'text/plain; charset=utf-8'}});
  const response=await context.next();const headers=new Headers(response.headers);headers.set('Cache-Control','private, no-store');headers.set('X-Robots-Tag','noindex, nofollow');return new Response(response.body,{status:response.status,headers});
 }catch{return new Response('暂时无法读取作品，请稍后重试。',{status:503,headers:{'Cache-Control':'no-store'}});}
}
