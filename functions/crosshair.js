export async function onRequest(context){
  if(!context.env.CREATOR_ASSETS)return new Response('Unavailable',{status:503});
  const key='public/CCBCM准星-最终版-win-x64.zip';
  try{
    const object=await context.env.CREATOR_ASSETS.get(key);
    if(!object)return new Response('Not found',{status:404,headers:{'Cache-Control':'no-store'}});
    const headers=new Headers(object.httpMetadata||{});
    headers.set('Content-Type','application/zip');
    headers.set('Content-Disposition','attachment; filename="CCBCM-Crosshair-win-x64.zip"');
    headers.set('Cache-Control','public, max-age=3600');
    return new Response(object.body,{headers});
  }catch{return new Response('Unavailable',{status:503,headers:{'Cache-Control':'no-store'}});}
}
