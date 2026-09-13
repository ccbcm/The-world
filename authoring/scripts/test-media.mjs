import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
export async function testMedia({env,req,sql,digest,A,B,onRequest}) {
 crypto.DigestStream=class extends WritableStream{constructor(){const hash=createHash('sha256');let resolve;const result=new Promise(r=>resolve=r);super({write:chunk=>hash.update(chunk),close:()=>resolve(hash.digest())});this.digest=result;}};
 sql.prepare('UPDATE video_upload_daily SET n=0').run();
 const objects=new Map(),uploads=new Map();let largest=0;
 const resume=(key,id)=>({uploadId:id,uploadPart:async(n,bytes)=>{assert.ok(uploads.has(id));largest=Math.max(largest,bytes.length);uploads.get(id).set(n,Buffer.from(bytes));return {partNumber:n,etag:digest(bytes)};},complete:async parts=>{objects.set(key,Buffer.concat(parts.map(p=>uploads.get(id).get(p.partNumber))));uploads.delete(id);},abort:async()=>uploads.delete(id)});
 env.CREATOR_ASSETS={createMultipartUpload:async key=>{const id=String(Math.random());uploads.set(id,new Map());return resume(key,id);},resumeMultipartUpload:resume,get:async(key,options={})=>{let bytes=objects.get(key);if(!bytes)return null;if(options.range)bytes=bytes.subarray(options.range.offset,options.range.offset+options.range.length);let offset=0;return {body:new ReadableStream({pull(c){if(offset===bytes.length){c.close();return;}const end=Math.min(offset+65536,bytes.length);c.enqueue(bytes.subarray(offset,end));offset=end;}})};},delete:async key=>objects.delete(key)};
 const part=(id,n,uploadId,bytes,token=A)=>onRequest({env,request:new Request('https://ccbcm.net/api/videos/'+id+'/part?n='+n,{method:'PUT',headers:{Origin:'https://ccbcm.net',Cookie:'__Host-ccbcm-session='+token,'X-Upload-Id':uploadId},body:bytes})});
 async function reserve(bytes,mime,sha=digest(bytes)){const r=await req('videos','POST',A,{title:'文件边界测试',size:bytes.length,mime,sha256:sha});assert.equal(r.status,200);return (await r.json()).id;}
 async function transfer(id,bytes){const r=await req('videos/'+id+'/begin','POST',A);assert.equal(r.status,200);const session=await r.json();for(let offset=0,n=1;offset<bytes.length;offset+=session.partSize,n++){const r=await part(id,n,session.uploadId,bytes.subarray(offset,offset+session.partSize));assert.equal(r.status,200,await r.text());}return req('videos/'+id+'/complete','POST',A);}
 // The full 200 MiB boundary traverses 25 bounded requests and streaming verification.
 const large=Buffer.alloc(200*1024*1024);large.writeUInt32BE(16,0);large.write('ftyp',4);large.write('isom',8);large.writeUInt32BE(8,16);large.write('moov',20);large.writeUInt32BE(large.length-24,24);large.write('mdat',28);
 const id=await reserve(large,'video/mp4');assert.equal((await req('videos/'+id+'/begin','POST',B)).status,404);
 const session=await (await req('videos/'+id+'/begin','POST',A)).json();assert.equal((await req('videos/'+id+'/complete','POST',A)).status,409);assert.equal((await part(id,1,'wrong',large.subarray(0,session.partSize))).status,400);assert.equal((await part(id,1,session.uploadId,large.subarray(0,5))).status,400);
 const complete=await transfer(id,large);assert.equal(complete.status,200,await complete.text());assert.equal(largest,8*1024*1024);assert.equal((await req('videos/'+id+'/begin','POST',A)).status,200);
 assert.equal((await req('videos','POST',A,{title:'超限',mime:'video/mp4',size:large.length+1,sha256:digest(large)})).status,400);
 // There is no cumulative account or site capacity check.
 for(let i=0;i<2;i++)assert.equal((await req('videos','POST',A,{title:'存量不设上限',mime:'video/mp4',size:large.length,sha256:digest(large)})).status,200);
 const limits=(await (await req('videos','GET',A)).json()).limits;assert.equal(limits.file,large.length);assert.equal(limits.account,undefined);
 for(const [file,mime] of [['gallery/media/cat.png','image/png'],['gallery/media/blue.jpg','image/jpeg']]){
  const bytes=readFileSync(file),id=await reserve(bytes,mime);const result=await transfer(id,bytes);assert.equal(result.status,200,await result.text());
  assert.equal((await req('published-videos/'+id+'/content')).status,404);
  assert.equal((await req('videos/'+id+'/submit','POST',A)).status,200);
  assert.equal((await req('moderation/'+id,'POST',B,{decision:'approve',reason:''})).status,200);
  assert.equal((await req('videos/'+id+'/publish','POST',A)).status,200);
  const manifest=await (await req('published-videos/'+id+'/manifest')).json();assert.equal(manifest.mime,mime);assert.equal(manifest.sha256,digest(bytes));
  const response=await req('published-videos/'+id+'/content');assert.equal(response.headers.get('Content-Type'),mime);assert.equal(digest(Buffer.from(await response.arrayBuffer())),manifest.sha256);
  assert.equal((await req('downloads','POST',B,{id})).status,200);
 }
 const png=readFileSync('gallery/media/cat.png');const mismatch=await reserve(png,'image/png','0'.repeat(64));assert.equal((await transfer(mismatch,png)).status,400);
 const disguised=await reserve(png,'video/mp4');assert.equal((await transfer(disguised,png)).status,400);
 const abandoned=await reserve(png,'image/png');const first=await (await req('videos/'+abandoned+'/begin','POST',A)).json();
 assert.equal((await req('videos/'+abandoned,'DELETE',A)).status,409);
 assert.equal((await (await req('videos/'+abandoned+'/begin','POST',A)).json()).uploadId,first.uploadId);
 sql.prepare('UPDATE creator_videos SET updated_at=? WHERE id=?').run(Date.now()-16*60000,abandoned);
 const restarted=await (await req('videos/'+abandoned+'/begin','POST',A)).json();assert.notEqual(restarted.uploadId,first.uploadId);assert.equal(uploads.has(first.uploadId),false);
 sql.prepare('UPDATE creator_videos SET updated_at=? WHERE id=?').run(Date.now()-16*60000,abandoned);
 assert.equal((await req('videos/'+abandoned,'DELETE',A)).status,200);assert.equal(uploads.has(restarted.uploadId),false);assert.equal(sql.prepare('SELECT id FROM wallpaper_media WHERE id=?').get(abandoned),undefined);
 console.log('PASS: 200 MiB multipart boundary, 8 MiB maximum part, no account capacity, PNG/JPEG review/publish/manifest/content/download, cross-account denial, incomplete and corrupt uploads');
}
