const {chromium}=require('C:/Users/27035/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:960}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/');await page.waitForFunction(()=>window.__cityReady,{timeout:120000});
 if(await page.locator('header.top').count())throw Error('Decorative header still exists');
 await page.waitForTimeout(2000);await page.screenshot({path:'C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/预览/网页材质更新.png'});
 const result={errors,decorative_header_removed:true,visual_loaded:true};fs.writeFileSync('C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴/网页外观验证.json',JSON.stringify(result,null,2));console.log(result);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
