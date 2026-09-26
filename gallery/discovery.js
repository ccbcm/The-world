// A stable random tail for this page visit. Ranking is supplied by the server, never by the client.
const randomKeys=new Map();
function randomKey(id){if(!randomKeys.has(id))randomKeys.set(id,Math.random());return randomKeys.get(id);}
export function discoveryOrder(works,ranking){
 const scores=new Map(ranking.map(x=>[x.id,x.clicks]));
 const popular=works.filter(w=>(scores.get(w.id)||0)>0).sort((a,b)=>scores.get(b.id)-scores.get(a.id)||a.id.localeCompare(b.id)).slice(0,10);
 const top=new Set(popular.map(w=>w.id));
 const rest=works.filter(w=>!top.has(w.id));rest.forEach(w=>randomKey(w.id));rest.sort((a,b)=>randomKey(a.id)-randomKey(b.id));
 return [...popular,...rest];
}
export function startHero(host,works,ranking,{image,escape}){
 const list=discoveryOrder(works.filter(w=>w.video),ranking);if(!host)return ()=>{};if(!list.length){host.innerHTML='<div class="hero-empty"><span aria-hidden="true">✦</span><p>为这块屏幕，留一片风景。</p><a href="#studio" class="pill secondary">分享竖屏壁纸</a></div>';return ()=>{};}
 host.classList.toggle('portrait-hero',list[0].height>list[0].width);
 const open=host.querySelector('.hero-open'),controls=host.querySelector('.hero-controls'),toggle=controls.querySelector('[data-hero-pause]'),counter=controls.querySelector('.hero-position');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');let index=0,paused=reduced.matches,visible=true,hover=false,focused=false,timer=null,video=null,dead=false;
 const canPlay=()=>!dead&&!paused&&!document.hidden&&visible&&!document.querySelector('dialog[open]');
 function release(){if(video){video.pause();video.removeAttribute('src');video.load();video=null;}}
 function schedule(){clearTimeout(timer);if(canPlay()&&!hover&&!focused&&list.length>1)timer=setTimeout(()=>show(index+1),12000);}
 function sync(){if(canPlay()){video?.play().catch(()=>{});}else video?.pause();schedule();}
 function show(next){release();index=(next+list.length)%list.length;const w=list[index];open.dataset.work=w.id;open.setAttribute('aria-label','查看 '+w.name);
  open.innerHTML=`<img src="${image(w)}" alt="${escape(w.name)}" width="1400" height="850"><div class="hero-label"><div><strong title="${escape(w.name)}">${escape(w.name)}</strong><small>${escape(w.ownerLogin||'CCBCM')} · 动态壁纸</small></div></div>`;
  counter.textContent=`${index+1} / ${list.length}`;video=document.createElement('video');video.className='hero-video';video.muted=true;video.defaultMuted=true;video.playsInline=true;video.loop=true;video.preload='none';video.setAttribute('aria-hidden','true');video.poster=image(w);video.src=w.video;open.prepend(video);
  const current=video;video.addEventListener('playing',()=>{if(current===video)open.classList.add('is-playing');});video.addEventListener('error',()=>{if(current===video)open.classList.remove('is-playing');});open.classList.remove('is-playing');sync();
 }
 const prev=()=>show(index-1),next=()=>show(index+1),pause=()=>{paused=!paused;sync();};
 const enter=()=>{hover=true;schedule();},leave=()=>{hover=false;schedule();},focus=()=>{focused=true;schedule();},blur=e=>{if(!host.contains(e.relatedTarget)){focused=false;schedule();}};
 const preference=()=>{paused=reduced.matches;sync();};
 controls.querySelector('[data-hero-prev]').onclick=prev;controls.querySelector('[data-hero-next]').onclick=next;if(toggle)toggle.onclick=pause;
 controls.querySelector('[data-hero-prev]').disabled=list.length<2;controls.querySelector('[data-hero-next]').disabled=list.length<2;
 host.addEventListener('pointerenter',enter);host.addEventListener('pointerleave',leave);host.addEventListener('focusin',focus);host.addEventListener('focusout',blur);document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',preference);
 const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();},{threshold:0.1});observer.observe(host);
 const modalObserver=new MutationObserver(sync);modalObserver.observe(document.querySelector('#detail'),{attributes:true,attributeFilter:['open']});
 show(0);
 return ()=>{dead=true;clearTimeout(timer);release();observer.disconnect();modalObserver.disconnect();document.removeEventListener('visibilitychange',sync);reduced.removeEventListener('change',preference);host.removeEventListener('pointerenter',enter);host.removeEventListener('pointerleave',leave);host.removeEventListener('focusin',focus);host.removeEventListener('focusout',blur);};
}
