from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'网页漫游/main.js';s=p.read_text(encoding='utf8')
s="import {loadCharacter} from './character.js';\n"+s
s=s.replace("let mode='orbit'", "let avatar,followDistance=4.2;\nlet mode='orbit'")
s=s.replace("camera.position.set(-180,2.6,148);camera.lookAt(-5,80,0);upVelocity=0;", "if(avatar){avatar.root.position.set(-180,.8,148);avatar.root.rotation.y=Math.PI;}yaw=0;pitch=-.18;upVelocity=0;followCamera(1);")
s=s.replace("}syncLook();", "}if(mode!=='walk')syncLook();")
s=s.replace("拖动环顾 · W A S D 行走 · Shift 快走 · 空格跳跃", "W A S D 行走 · Shift 跑步 · 空格跳跃 · 拖动转镜头 · 滚轮调距离")
start=s.index("$('river').onclick=");end=s.index("\n",start)
s=s[:start]+"$('river').onclick=()=>{setMode('walk');toast('第三人称 · Vita')};"+s[end:]
s=s.replace("pitch=THREE.MathUtils.clamp(pitch,-1.48,1.48);", "pitch=THREE.MathUtils.clamp(pitch,mode==='walk'?-.8:-1.48,mode==='walk'?.25:1.48);")
s=s.replace("camera.position.y<2.62", "avatar&&avatar.root.position.y<.82")
s=s.replace("  loaded=true;renderer", "  avatar=await loadCharacter(scene);\n  loaded=true;renderer")
s=s.replace("if(mode==='orbit')orbit.update();else if(loaded){", "if(avatar&&mode!=='walk')avatar.update(dt,0,false);\n if(mode==='walk'&&loaded){updatePlayer(dt);}else if(mode==='orbit')orbit.update();else if(loaded){")
s=s.replace("window.__cityTest={setMode", "window.__cityTest={getAvatar:()=>avatar?{name:avatar.name,height:avatar.height,position:avatar.root.position.toArray(),rotation:avatar.root.rotation.y}:null,setMode")
where=s.index("const map=$('map')")
s=s[:where]+'''canvas.addEventListener('wheel',e=>{if(mode==='walk'){e.preventDefault();followDistance=THREE.MathUtils.clamp(followDistance+e.deltaY*.003,2.2,8);}},{passive:false});
function followCamera(dt){
 if(!avatar)return;
 const target=avatar.root.position.clone().add(new THREE.Vector3(0,1.25,0));
 const offset=new THREE.Vector3(Math.sin(yaw)*Math.cos(pitch),-Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)).multiplyScalar(followDistance);
 // Pull the camera forward when its segment enters a building collider.
 let fraction=1;for(let t=.15;t<=1;t+=.05){const q=target.clone().addScaledVector(offset,t);if(blocked(q.x,q.z,q.y)){fraction=Math.max(.12,t-.08);break;}}
 const desired=target.clone().addScaledVector(offset,fraction);desired.y=Math.max(1.05,desired.y);
 camera.position.lerp(desired,1-Math.exp(-12*dt));camera.lookAt(target);
}
function updatePlayer(dt){
 if(!avatar)return;
 const p=avatar.root.position,forward=new THREE.Vector3(-Math.sin(yaw),0,-Math.cos(yaw)),side=new THREE.Vector3(Math.cos(yaw),0,-Math.sin(yaw)),move=new THREE.Vector3();
 if(keys.has('KeyW')||keys.has('ArrowUp'))move.add(forward);if(keys.has('KeyS')||keys.has('ArrowDown'))move.sub(forward);
 if(keys.has('KeyD'))move.add(side);if(keys.has('KeyA'))move.sub(side);
 const speed=keys.has('ShiftLeft')||keys.has('ShiftRight')?4.4:1.45,before=p.clone();
 if(move.lengthSq()){
  move.normalize();const heading=Math.atan2(move.x,move.z);
  avatar.root.rotation.y+=Math.atan2(Math.sin(heading-avatar.root.rotation.y),Math.cos(heading-avatar.root.rotation.y))*(1-Math.exp(-12*dt));
  if(!blocked(p.x+move.x*speed*dt,p.z,p.y+1.5))p.x+=move.x*speed*dt;else collisionHits++;
  if(!blocked(p.x,p.z+move.z*speed*dt,p.y+1.5))p.z+=move.z*speed*dt;else collisionHits++;
 }
 upVelocity-=12*dt;p.y=Math.max(.8,p.y+upVelocity*dt);if(p.y===.8)upVelocity=0;
 avatar.update(dt,Math.hypot(p.x-before.x,p.z-before.z)/Math.max(dt,.001),p.y>.81);followCamera(dt);
}
''' +s[where:]
p.write_text(s,encoding='utf8')
p=R/'网页漫游/index.html';s=p.read_text(encoding='utf8').replace('>地面行走<','>第三人称<');p.write_text(s,encoding='utf8')
print('character connected')
