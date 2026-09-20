import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
export async function testCovers({env,req,sql,digest,A,B,onRequest}){
 sql.prepare('UPDATE video_upload_daily SET n=0').run();
 const objects=new Map();env.CREATOR_ASSETS={put:async(k,b)=>objects.set(k,Buffer.from(b)),get:async k=>objects.has(k)?{body:new Blob([objects.get(k)]).stream()}:null};
 const bytes=readFileSync('gallery/media/blue.jpg');
 const id=(await (await req('videos','POST',A,{title:'高清封面验证',size:bytes.length,mime:'image/jpeg',sha256:digest(bytes)})).json()).id;
 const put=(action,token=A,body=bytes)=>onRequest({env,request:new Request('https://ccbcm.net/api/videos/'+id+'/'+action,{method:'PUT',headers:{Origin:'https://ccbcm.net',Cookie:'__Host-ccbcm-session='+token,'Content-Type':'image/jpeg','X-Media-Width':'1280','X-Media-Height':'720'},body})});
 assert.equal((await put('content')).status,200);
 assert.equal((await put('cover',B)).status,404);
 assert.equal((await put('cover',A,Buffer.alloc(64))).status,400);
 assert.equal((await put('cover')).status,200);
 assert.equal((await req('published-videos/'+id+'/cover')).status,404);
 assert.equal((await req('videos/'+id+'/cover','GET',B)).status,404);
 assert.equal((await req('videos/'+id+'/cover','GET',A)).status,200);
 assert.equal((await req('videos/'+id+'/submit','POST',A)).status,200);
 assert.equal((await put('cover')).status,409);
 assert.equal((await req('moderation/'+id+'/cover','GET',B)).status,200);
 assert.equal((await req('moderation/'+id,'POST',B,{decision:'approve',reason:''})).status,200);
 assert.equal((await req('videos/'+id+'/publish','POST',A)).status,200);
 const catalog=await (await req('published-videos')).json(),work=catalog.items.find(v=>v.id===id);assert.equal(work.width,1280);assert.equal(work.height,720);assert.ok(work.poster.startsWith('/api/published-videos/'));
 assert.equal(digest(Buffer.from(await (await req('published-videos/'+id+'/cover')).arrayBuffer())),digest(bytes));
 assert.equal((await req('videos/'+id+'/unlist','POST',A)).status,200);
 assert.equal((await req('published-videos/'+id+'/cover')).status,404);
 console.log('PASS: HD cover isolation, binary validation, review lock, publication metadata and unlisting');
}
