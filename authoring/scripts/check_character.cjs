const {chromium}=require('C:/Users/27035/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),R='C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--ignore-gpu-blocklist']});const page=await browser.newPage({viewport:{width:1440,height:960}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/');await page.waitForFunction(()=>window.__cityReady||window.__cityError,{timeout:120000});
 const err=await page.evaluate(()=>window.__cityError);if(err)throw Error(err);
 if(await page.locator('[data-key]').count())throw Error('Arrow pad remains');
 await page.click('#walk');await page.waitForTimeout(1000);const before=await page.evaluate(()=>window.__cityTest.getAvatar());
 await page.screenshot({path:R+'/预览/第三人称待机.png'});
 await page.keyboard.down('KeyW');await page.waitForTimeout(1500);await page.screenshot({path:R+'/预览/第三人称行走.png'});await page.keyboard.up('KeyW');
 const after=await page.evaluate(()=>window.__cityTest.getAvatar());
 await page.keyboard.press('Space');await page.waitForTimeout(160);const jumping=await page.evaluate(()=>window.__cityTest.getAvatar());await page.waitForFunction(()=>{const a=window.__cityTest.getAvatar();return Math.abs(a.position[1]-a.floor)<.015;},{timeout:7000});
 const landed=await page.evaluate(()=>window.__cityTest.getAvatar());
 const result={errors,before,after,jumping,landed,arrowPadRemoved:true};fs.writeFileSync(R+'/第三人称验证.json',JSON.stringify(result,null,2));console.log(result);
 if(errors.length||Math.hypot(after.position[0]-before.position[0],after.position[2]-before.position[2])<.2||jumping.position[1]<=jumping.floor||Math.abs(landed.position[1]-landed.floor)>.01)throw Error('Movement verification failed');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
