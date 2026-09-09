const {chromium}=require('C:/Users/27035/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__cityReady||window.__cityError,{timeout:180000});
 if(await page.evaluate(()=>window.__cityError))throw Error(await page.evaluate(()=>window.__cityError));
 await page.waitForTimeout(3000);await page.screenshot({path:'C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/预览/网页漫游.png'});
 const initial=await page.evaluate(()=>window.__cityStats);
 await page.click('#fly');const start=await page.evaluate(()=>window.__cityTest.getCamera());await page.keyboard.down('KeyW');await page.waitForTimeout(1200);await page.keyboard.up('KeyW');const end=await page.evaluate(()=>window.__cityTest.getCamera());
 if(Math.hypot(...end.map((v,i)=>v-start[i]))<2)throw Error('flight did not move');
 await page.click('#walk');await page.waitForTimeout(700);const eye=await page.evaluate(()=>window.__cityTest.getCamera()[1]);const avatar=await page.evaluate(()=>window.__cityTest.getAvatar());if(Math.abs(avatar.position[1]-avatar.floor)>.02)throw Error('character not on ground');
 const collision=await page.evaluate(()=>window.__cityTest.blocked(0,0,2.6));if(!collision)throw Error('Pearl base collision missing');
 await page.click('#trio');await page.waitForTimeout(1200);await page.click('#time');await page.screenshot({path:'C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/预览/网页黄昏.png'});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(1000);await page.screenshot({path:'C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/预览/网页手机.png'});
 const result={errors,initial,flight_distance:Math.hypot(...end.map((v,i)=>v-start[i])),walk_eye:eye,collision,mobileViewport:{width:390,height:844},final:await page.evaluate(()=>window.__cityStats)};
 fs.writeFileSync('C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/网页验证.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
