import fs from 'node:fs';import assert from 'node:assert/strict';
const source=fs.readFileSync('functions/_middleware.js','utf8').replace("import { current } from './api/[[path]].js';",'const current=async(request,db)=>db.user;');
const {onRequest}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
for(const path of ['/city','/city.html','/city/'])for(const user of [null,{id:'999'},{id:'325610429'}]){const r=await onRequest({request:new Request('https://ccbcm.net'+path),env:{DB:{user}},next:async()=>new Response('scene')});assert.equal(r.status,user?.id==='325610429'?200:404);assert.match(r.headers.get('Cache-Control'),/no-store/);}
console.log('PASS: city routes deny anonymous/other accounts, allow owner, never cache');
