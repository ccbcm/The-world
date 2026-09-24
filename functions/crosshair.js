export async function onRequest(context){
  if(!context.env.CREATOR_ASSETS)return new Response('Unavailable',{status:503});
  const key='public/CCBCM准星-1.0.0-Setup.exe';
  try{
    const object=await context.env.CREATOR_ASSETS.get(key);
    if(!object)return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});
    const headers=new Headers(object.httpMetadata||{});
    headers.set('Content-Type','application/vnd.microsoft.portable-executable');
    headers.set('Content-Disposition',"attachment; filename=\"CCBCM-Crosshair-1.0.0-Setup.exe\"; filename*=UTF-8''CCBCM%E5%87%86%E6%98%9F-1.0.0-Setup.exe");
    headers.set('Content-Length',String(object.size));
    headers.set('Cache-Control','public, max-age=3600');
    return new Response(object.body,{headers});
  }catch{return new Response('Unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}
}
