// Covers are separate from originals: never enlarge a low-resolution thumbnail.
export async function coverFrom(source,width,height){
 const scale=Math.min(1920/Math.max(width,height),1),canvas=document.createElement('canvas');
 canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
 canvas.getContext('2d').drawImage(source,0,0,canvas.width,canvas.height);
 const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.92));
 if(!blob||blob.size>3*1024*1024)throw Error('封面生成失败，请选择另一张图片。');
 return {blob,width,height};
}
export async function extractCover(file){
 if(file.type.startsWith('image/')||/\.(png|jpe?g)$/i.test(file.name)){
  const bitmap=await createImageBitmap(file);try{return await coverFrom(bitmap,bitmap.width,bitmap.height);}finally{bitmap.close();}
 }
 const url=URL.createObjectURL(file),video=document.createElement('video');video.muted=true;video.playsInline=true;video.preload='auto';
 try{
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('浏览器无法读取视频封面。原视频仍可上传，保存后可补充封面。')),20000);video.onloadeddata=()=>{clearTimeout(timer);resolve();};video.onerror=()=>{clearTimeout(timer);reject(Error('此浏览器无法预览这个编码。原视频仍可上传，保存后可补充封面。'));};video.src=url;});
  if(!video.videoWidth||!video.videoHeight)throw Error('视频尺寸无法读取。');
  if(video.duration>0.5)await new Promise(resolve=>{const timer=setTimeout(resolve,2000);video.onseeked=()=>{clearTimeout(timer);resolve();};video.currentTime=Math.min(1,video.duration/3);});
  return await coverFrom(video,video.videoWidth,video.videoHeight);
 }finally{video.removeAttribute('src');video.load();URL.revokeObjectURL(url);}
}
export const mobileDevice=()=>/Android|iPhone|iPad|iPod|HarmonyOS/i.test(navigator.userAgent)||(navigator.maxTouchPoints>1&&/Macintosh/.test(navigator.userAgent));
export const mobileLayout=()=>mobileDevice()||matchMedia('(max-width:700px)').matches;
export const portraitWork=w=>Number(w.height)>Number(w.width)&&Number(w.width)>0;
export function mobileUse(w,dialog,escape){
 if(/Android/i.test(navigator.userAgent)&&!/HarmonyOS/i.test(navigator.userAgent)){
  dialog.querySelector('#detail-body').innerHTML=`<div class="detail-copy mobile-use"><p class="eyebrow">安卓壁纸</p><h2>${escape(w.name)}</h2><p>插件会自动准备壁纸，再打开系统预览。是否同时用于锁屏，由手机系统提供选项。</p><div class="detail-actions"><a class="pill" href="intent://apply/${w.id}#Intent;scheme=ccbcm-mobile;package=net.ccbcm.wallpaper.preview;S.browser_fallback_url=https%3A%2F%2Fccbcm.net%2F%23plugin;end">打开安卓插件</a><a class="pill secondary" href="/downloads/CCBCM-Android-preview.apk?v=preview-3" download>安装安卓预览版</a></div><p class="subtitle">Android 8 及以上。首次使用请安装插件；预览版尚待不同品牌真机验证。</p></div>`;dialog.showModal();return;
 }
 const isApple=/iPhone|iPad|iPod/.test(navigator.userAgent)||(navigator.maxTouchPoints>1&&/Macintosh/.test(navigator.userAgent));
 const still=w.type==='静态壁纸',url=w.content||`/gallery/media/${w.id}.${still?'png':'mp4'}`;
 dialog.querySelector('#detail-body').innerHTML=`<div class="detail-copy mobile-use"><p class="eyebrow">手机壁纸</p><h2>${escape(w.name)}</h2><p>${still?'保存图片后，在系统壁纸设置中选择桌面或锁屏。':isApple?'iPhone 动态锁屏需要 Live Photo。普通视频不能直接设为动态锁屏；目前可以保存封面作为静态壁纸。':'动态壁纸需要手机的壁纸服务支持。当前先提供原视频与高清封面，系统支持视频壁纸时可从相册设置。'}</p><div class="detail-actions"><a class="pill" href="${still?url:escape(w.poster||'/gallery/media/blue.jpg')}" target="_blank" rel="noopener">打开高清图片</a>${!still&&!isApple?`<a class="pill secondary" href="${url}" target="_blank" rel="noopener">打开原视频</a>`:''}</div><p class="subtitle">打开图片后，长按保存到相册。账号中的收藏与下载会在电脑和手机同步。</p><p class="subtitle">手机原生插件尚未发布，此入口不会自动更改系统壁纸。</p></div>`;dialog.showModal();
}
