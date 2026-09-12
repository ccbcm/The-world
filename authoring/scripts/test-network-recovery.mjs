import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync('gallery/app.js','utf8');
const fn=source.slice(source.indexOf('async function api('),source.indexOf('\nfunction account()'));
async function check(responses,options,expected){let calls=0;const ctx={location:{hostname:'ccbcm.net'},AbortController,setTimeout,clearTimeout,TypeError,Error,fetch:async()=>{calls++;const r=responses.shift();if(r instanceof Error)throw r;return r;}};vm.createContext(ctx);vm.runInContext(fn,ctx);let error;try{await ctx.api('test',options)}catch(e){error=e}assert.equal(calls,expected);return error;}
const ok={ok:true,json:async()=>({ok:true})};
assert.equal(await check([new TypeError('network'),ok],{},2),undefined);
assert.ok(await check([new TypeError('network')],{method:'POST'},1));
assert.equal(await check([{status:503,body:{cancel:async()=>{}}},ok],{},2),undefined);
assert.ok(await check([{status:401,ok:false,json:async()=>({error:'login'})}],{},1));
console.log('PASS: GET recovers network/503; mutations and 401 never replayed');
