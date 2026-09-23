export async function onRequest(context){
  if(!context.env.CREATOR_ASSETS)return new Response('Unavailable',{status:503});
  const key='public/CCBCM-Crosshair-0.3.0-Setup.exe';
  try{
    const object=await context.env.CREATOR_ASSETS.get(key);
    if(!object)return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});
    const headers=new Headers(object.httpMetadata||{});
    headers.set('Content-Type','application/vnd.microsoft.portable-executable');
    headers.set('Content-Disposition','attachment; filename="CCBCM-Crosshair-Setup.exe"');
    headers.set('Cache-Control','public, max-age=3600');
    return new Response(object.body,{headers});
  }catch{return new Response('Unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}
}
