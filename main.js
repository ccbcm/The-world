import {createArchitectureFinish} from './architecture.js';
import {loadCharacter} from './character.js';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { Water } from 'three/addons/objects/Water.js';
const $=s=>document.getElementById(s),canvas=$('world');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,logarithmicDepthBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,1));renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.8;
const scene=new THREE.Scene();scene.background=new THREE.Color('#b8cbd4');scene.fog=new THREE.FogExp2('#b8cbd4',.000075);
const camera=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.15,16000);camera.position.set(-1250,220,200);
const orbit=new OrbitControls(camera,canvas);orbit.target.set(300,245,330);orbit.enableDamping=true;orbit.maxDistance=3500;orbit.minDistance=3;orbit.maxPolarAngle=Math.PI*.49;
const pmrem=new THREE.PMREMGenerator(renderer),sky=new Sky();sky.scale.setScalar(7000);sky.material.uniforms.turbidity.value=5;sky.material.uniforms.rayleigh.value=1.5;sky.material.uniforms.mieCoefficient.value=.005;sky.material.uniforms.mieDirectionalG.value=.8;sky.material.uniforms.sunPosition.value.set(-1000,1600,-600);const envScene=new THREE.Scene();envScene.add(sky);let env=pmrem.fromScene(envScene,.04);scene.environment=env.texture;scene.environmentIntensity=.07;scene.add(sky);sky.material.depthWrite=false;sky.frustumCulled=false;

const cloudCanvas=document.createElement('canvas');cloudCanvas.width=512;cloudCanvas.height=256;
const cloudContext=cloudCanvas.getContext('2d'),cloudPixels=cloudContext.createImageData(512,256);
for(let y=0;y<256;y++)for(let x=0;x<512;x++){let n=0;for(let k=1;k<=6;k++){n+=Math.sin(x*.012*k+Math.sin(y*.019*k)*2+k)*Math.cos(y*.017*k+k*.8)/k;}const i=(y*512+x)*4;cloudPixels.data[i]=255;cloudPixels.data[i+1]=255;cloudPixels.data[i+2]=255;cloudPixels.data[i+3]=Math.max(0,Math.min(95,(n-.35)*75))*Math.sin(y/256*Math.PI);}
cloudContext.putImageData(cloudPixels,0,0);const cloudTexture=new THREE.CanvasTexture(cloudCanvas);cloudTexture.wrapS=THREE.RepeatWrapping;
const clouds=new THREE.Mesh(new THREE.SphereGeometry(6000,64,32,0,Math.PI*2,0,Math.PI*.49),new THREE.MeshBasicMaterial({map:cloudTexture,transparent:true,side:THREE.BackSide,depthWrite:false,fog:false}));clouds.renderOrder=-1;scene.add(clouds);

const hemi=new THREE.HemisphereLight(0xd1eaff,0x655b42,1.3);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xfff0db,3.2);sun.position.set(-1000,1600,-600);scene.add(sun);sun.target.position.set(250,0,300);scene.add(sun.target);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-1200,right:1200,top:1200,bottom:-1200,near:1,far:4000});sun.shadow.normalBias=1;sun.shadow.bias=-.0002;renderer.shadowMap.enabled=false;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
const ground=new THREE.Mesh(new THREE.PlaneGeometry(20000,20000),new THREE.MeshStandardMaterial({color:0x777c74,roughness:.96}));ground.rotation.x=-Math.PI/2;ground.position.y=-.12;ground.receiveShadow=true;scene.add(ground);
let avatar,followDistance=4.2,playerFloor=.8;const walkSurfaces=[],floorRay=new THREE.Raycaster();
let mode='orbit',day=true,loaded=false,high=false,drag=false,lastX=0,lastY=0,pitch=0,yaw=0,upVelocity=0,keys=new Set(),manifest,tilesLoaded=0,noticeTimer,collisionHits=0;
const loader=new GLTFLoader(),ray=new THREE.Raycaster(),clock=new THREE.Clock(),v=new THREE.Vector3(),right=new THREE.Vector3(),cityTiles=[];
const obstacleGrid=new Map(),gridSize=80;const solidMeshes=[],contactRay=new THREE.Raycaster(),contactDirections=[new THREE.Vector3(1,0,0),new THREE.Vector3(-1,0,0),new THREE.Vector3(0,0,1),new THREE.Vector3(0,0,-1)];
function addCollider(c){
 for(let x=Math.floor(c.min[0]/gridSize);x<=Math.floor(c.max[0]/gridSize);x++)for(let z=Math.floor(c.min[2]/gridSize);z<=Math.floor(c.max[2]/gridSize);z++){let k=x+','+z;if(!obstacleGrid.has(k))obstacleGrid.set(k,[]);obstacleGrid.get(k).push(c)}
}
function blocked(x,z,y){
 const r=.65;for(const c of obstacleGrid.get(Math.floor(x/gridSize)+','+Math.floor(z/gridSize))||[]){
  if(y-1.7>c.max[1]||y<c.min[1])continue;
  const xx=Math.max(c.min[0],Math.min(c.max[0],x)),zz=Math.max(c.min[2],Math.min(c.max[2],z));if((x-xx)**2+(z-zz)**2<r*r)return true;
 }
 for(const entry of solidMeshes){if(x<entry.box.min.x-.38||x>entry.box.max.x+.38||z<entry.box.min.z-.38||z>entry.box.max.z+.38||y<entry.box.min.y||y-1.3>entry.box.max.y)continue;for(const h of [y-1.1,y-.25])for(const d of contactDirections){contactRay.set(new THREE.Vector3(x,h,z),d);contactRay.far=.38;if(contactRay.intersectObject(entry.mesh,false).length)return true;}}return false;
}
function toast(t){$('notice').textContent=t;$('notice').classList.add('show');clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>$('notice').classList.remove('show'),2600)}
function syncLook(){const e=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');pitch=e.x;yaw=e.y}
function setMode(next){
 mode=next;orbit.enabled=mode==='orbit';for(const m of ['orbit','fly','walk'])$(m).classList.toggle('active',m===mode);
 if(mode==='walk'){
  if(avatar){avatar.root.position.set(-180,.8,148);avatar.root.rotation.y=Math.PI;}yaw=0;pitch=-.18;upVelocity=0;followCamera(1);
 }if(mode!=='walk')syncLook();
 $('help').textContent=mode==='orbit'?'拖动旋转视角 · 滚轮缩放 · 右键平移':mode==='fly'?'拖动环顾 · W A S D 飞行 · Q / E 升降 · Shift 加速':'W A S D 行走 · Shift 跑步 · 空格跳跃 · 拖动转镜头 · 滚轮调距离';
 canvas.focus();
}
function preset(pos,target){camera.position.set(...pos);camera.lookAt(...target);orbit.target.set(...target);syncLook();if(mode==='walk'){mode='fly';orbit.enabled=false;for(const m of ['orbit','fly','walk'])$(m).classList.toggle('active',m==='fly');$('help').textContent='拖动环顾 · W A S D 飞行 · Q / E 升降 · Shift 加速'} }
for(const m of ['orbit','fly','walk'])$(m).onclick=()=>setMode(m);
$('pearl').onclick=()=>preset([-430,190,-270],[0,220,0]);
$('trio').onclick=()=>preset([-390,720,-460],[625,280,607]);
$('river').onclick=()=>{setMode('walk');toast('第三人称 · Vita')};
$('time').onclick=()=>{day=!day;architecture.setDusk(day?0:1);document.body.classList.toggle('night',!day);$('time').textContent=day?'☀ 白天':'◐ 黄昏';scene.background.set(day?'#b8cbd4':'#697883');scene.fog.color.copy(scene.background);hemi.intensity=day?1.3:.8;sun.intensity=day?3.2:2.2;sun.color.set(day?0xfff0db:0xffb774);sun.position.set(-1000,day?1600:250,-600);renderer.toneMappingExposure=day?.8:.9;sky.material.uniforms.sunPosition.value.copy(sun.position);scene.environment=photographedEnvironment?.texture||env.texture;scene.environmentIntensity=day?.65:.4;renderer.shadowMap.needsUpdate=true};
$('quality').onclick=()=>{high=!high;renderer.setPixelRatio(Math.min(devicePixelRatio,high?1.5:1));renderer.shadowMap.enabled=high;scene.traverse(o=>{if(o.isMesh)o.castShadow=high});renderer.shadowMap.needsUpdate=true;$('quality').textContent='画质：'+(high?'精细':'标准')};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{toast('当前浏览器不支持全屏')}};
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
canvas.addEventListener('pointerdown',e=>{if(mode==='orbit')return;drag=true;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);canvas.focus()});
canvas.addEventListener('pointermove',e=>{if(!drag||mode==='orbit')return;yaw-=(e.clientX-lastX)*.003;pitch-= (e.clientY-lastY)*.003;pitch=THREE.MathUtils.clamp(pitch,mode==='walk'?-.8:-1.48,mode==='walk'?1.35:1.48);camera.quaternion.setFromEuler(new THREE.Euler(pitch,yaw,0,'YXZ'));lastX=e.clientX;lastY=e.clientY});
canvas.addEventListener('pointerup',()=>drag=false);canvas.addEventListener('contextmenu',e=>e.preventDefault());
window.addEventListener('keydown',e=>{if(['Space','ArrowUp','ArrowDown'].includes(e.code))e.preventDefault();keys.add(e.code);if(e.code==='Space'&&mode==='walk'&&avatar&&avatar.root.position.y<playerFloor+.02)upVelocity=5});window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',()=>{keys.clear();drag=false});
document.querySelectorAll('[data-key]').forEach(b=>{b.onpointerdown=e=>{keys.add(b.dataset.key);b.setPointerCapture(e.pointerId)};b.onpointerup=()=>keys.delete(b.dataset.key);b.onpointercancel=()=>keys.delete(b.dataset.key)});
function waterMaterial(mesh){
 const g=mesh.geometry,pos=g.attributes.position,uv=new Float32Array(pos.count*2);for(let i=0;i<pos.count;i++){uv[i*2]=pos.getX(i)/22;uv[i*2+1]=pos.getZ(i)/22}g.setAttribute('uv',new THREE.BufferAttribute(uv,2));
 const size=256,data=new Uint8Array(size*size*4),waves=[[3,1,.30,.3],[5,-2,.22,1.4],[11,3,.15,2.5],[17,-7,.09,4.1],[23,11,.06,.8],[37,-13,.04,3.8]];
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){let nx=0,ny=0;for(const [a,b,amp,phase] of waves){const c=Math.cos((a*x+b*y)*Math.PI*2/size+phase),len=Math.hypot(a,b);nx+=c*amp*a/len;ny+=c*amp*b/len}const n=new THREE.Vector3(nx,ny,1).normalize(),i=(y*size+x)*4;data[i]=(n.x*.5+.5)*255;data[i+1]=(n.y*.5+.5)*255;data[i+2]=(n.z*.5+.5)*255;data[i+3]=255}
 const normal=new THREE.DataTexture(data,size,size);normal.wrapS=normal.wrapT=THREE.RepeatWrapping;normal.generateMipmaps=true;normal.minFilter=THREE.LinearMipmapLinearFilter;normal.magFilter=THREE.LinearFilter;normal.anisotropy=8;normal.needsUpdate=true;
 mesh.material=new THREE.MeshPhysicalMaterial({color:0x354b43,metalness:0,roughness:.31,normalMap:normal,normalScale:new THREE.Vector2(.24,.24),clearcoat:1,clearcoatRoughness:.16,envMapIntensity:.85,side:THREE.DoubleSide});mesh.castShadow=false;return normal;
}
let waterNormal,riverNormals;const waterBodies=[];
function installRiver(mesh){
 waterNormal=waterMaterial(mesh);return;
 const geometry=mesh.geometry.clone();geometry.applyMatrix4(mesh.matrixWorld);geometry.computeBoundingBox();const level=geometry.boundingBox.min.y;
 geometry.translate(0,-level,0);geometry.rotateX(Math.PI/2);
 const water=new Water(geometry,{textureWidth:512,textureHeight:512,waterNormals:riverNormals,sunDirection:sun.position.clone().normalize(),sunColor:0xffead4,waterColor:0x43554b,distortionScale:.65,alpha:1,fog:true,side:THREE.DoubleSide});
 water.rotation.x=-Math.PI/2;water.position.y=level;water.material.uniforms.size.value=1.2;mesh.visible=false;scene.add(water);waterBodies.push(water);
}
const treeLOD=[];let treeLODClock=0;const treeMatrix=new THREE.Matrix4(),treeRotation=new THREE.Quaternion(),treePosition=new THREE.Vector3(),treeScale=new THREE.Vector3();
function updateTreeLOD(){if(!manifest)return;for(const group of treeLOD){if(camera.position.y>120){group.inst.count=0;continue;}let count=0;for(const t of manifest.trees){const distance2=(camera.position.x-t.p[0])**2+(camera.position.z-t.p[2])**2,close=distance2<(high?100:45)**2;if(distance2>(mode==='orbit'?2000:high?650:380)**2||close!==group.near)continue;treePosition.fromArray(t.p);treeRotation.setFromAxisAngle(THREE.Object3D.DEFAULT_UP,t.ry);treeScale.fromArray(t.s);treeMatrix.compose(treePosition,treeRotation,treeScale);group.inst.setMatrixAt(count++,treeMatrix);}group.inst.count=count;group.inst.instanceMatrix.needsUpdate=true;}}
const architecture=createArchitectureFinish();
const scannedMaterials=new Map();
let photographedEnvironment;
async function loadScannedMaterials(){
 const texLoader=new THREE.TextureLoader();
 await Promise.all([['道路沥青','asphalt_02',.55],['滨江浅灰石材','granite_tile',.35],['人行浅色铺装','concrete_pavement',.35]].map(async([name,asset,strength])=>{
  const [map,normalMap,roughnessMap]=await Promise.all(['diff','nor_gl','rough'].map(async channel=>{
   const t=await texLoader.loadAsync('./assets/textures/'+asset+'_'+channel+'_2k.jpg');t.wrapS=t.wrapT=THREE.RepeatWrapping;t.flipY=false;t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());if(channel==='diff')t.colorSpace=THREE.SRGBColorSpace;return t;
  }));
  scannedMaterials.set(name,new THREE.MeshStandardMaterial({name,map,normalMap,roughnessMap,normalScale:new THREE.Vector2(strength,strength),roughness:1,metalness:0,side:THREE.DoubleSide}));
 }));
}
async function init(){
 try{
  await loadScannedMaterials();
  riverNormals=await new THREE.TextureLoader().loadAsync('./assets/textures/three_waternormals.jpg');riverNormals.wrapS=riverNormals.wrapT=THREE.RepeatWrapping;riverNormals.anisotropy=8;
  const lawnTex=await new THREE.TextureLoader().loadAsync('./assets/textures/eztree_grass.jpg');lawnTex.wrapS=lawnTex.wrapT=THREE.RepeatWrapping;lawnTex.flipY=false;lawnTex.colorSpace=THREE.SRGBColorSpace;lawnTex.anisotropy=8;scannedMaterials.set('v02 草地',new THREE.MeshStandardMaterial({name:'v02 草地',map:lawnTex,roughness:.96,side:THREE.DoubleSide}));
  for(const name of ['步行桥面 · 7m','桥接台阶'])scannedMaterials.set(name,scannedMaterials.get('人行浅色铺装'));
  // Procedural sky environment avoids a 25 MB blocking HDR download on first visit.
  scene.environmentIntensity=.65;
  const bindings=await fetch('./assets/material-bindings.json').then(r=>r.json());
  const textureCache=new Map();
  for(const binding of bindings){
   const textures=await Promise.all(['diff','nor_gl','rough'].map(async channel=>{const key=binding.asset+'_'+channel+'_'+binding.res;if(!textureCache.has(key)){const t=await new THREE.TextureLoader().loadAsync('./assets/textures/'+key+'.jpg');t.wrapS=t.wrapT=THREE.RepeatWrapping;t.flipY=false;t.anisotropy=8;if(channel==='diff')t.colorSpace=THREE.SRGBColorSpace;textureCache.set(key,t);}return textureCache.get(key);}));
   scannedMaterials.set(binding.name,new THREE.MeshStandardMaterial({name:binding.name,map:textures[0],normalMap:textures[1],roughnessMap:textures[2],normalScale:new THREE.Vector2(binding.strength,binding.strength),color:new THREE.Color(...binding.tint),roughness:1,side:THREE.DoubleSide}));
  }
  manifest=await fetch('./assets/manifest.json').then(r=>{if(!r.ok)throw Error('manifest');return r.json()});manifest.colliders.forEach(addCollider);manifest.trees.forEach(t=>{const r=Math.max(.18,.22*Math.max(t.s[0],t.s[2]));addCollider({name:'tree trunk',min:[t.p[0]-r,t.p[1],t.p[2]-r],max:[t.p[0]+r,t.p[1]+4,t.p[2]+r]});});addCollider({min:[-36,0,-36],max:[36,14,36]});
  // Ground arrives first; fixed small concurrency avoids flooding disk/network requests.
  const queue=[...manifest.tiles].sort((a,b)=>a.id==='ground'?-1:b.id==='ground'?1:(Math.hypot(...[a.center[0]-350,a.center[2]-250])-Math.hypot(...[b.center[0]-350,b.center[2]-250])));
  async function worker(){while(queue.length){const tile=queue.shift();const gltf=await loader.loadAsync('./assets/'+tile.file);gltf.scene.name=tile.id;gltf.scene.updateMatrixWorld(true);gltf.scene.traverse(o=>{if(o.isMesh){if(/道路|铺装|城市地表|草地|滨江浅灰|步行桥面|桥接台阶/.test(o.material?.name))walkSurfaces.push(o);o.castShadow=false;o.receiveShadow=true;if(!/道路|铺装|城市地表|草地|滨江浅灰|步行桥面|桥接台阶|黄浦江|标线|踏面/.test(o.material?.name||'') ){const box=new THREE.Box3().setFromObject(o);if(box.max.y-box.min.y>.8 && o.geometry.attributes.position.count<1500)solidMeshes.push({mesh:o,box});}if(scannedMaterials.has(o.material?.name))o.material=scannedMaterials.get(o.material.name);for(const m of Array.isArray(o.material)?o.material:[o.material]){m.side=THREE.DoubleSide;if(/标线/.test(m.name)){m.polygonOffset=true;m.polygonOffsetFactor=-1;m.polygonOffsetUnits=-1;}if(/框|金属|银灰结构/.test(m.name)){m.roughness=Math.max(m.roughness,.48);o.castShadow=false}}if(o.material?.name?.includes('黄浦江'))installRiver(o)}});gltf.scene.traverse(architecture.apply);scene.add(gltf.scene);cityTiles.push({scene:gltf.scene,center:tile.center,landmark:new THREE.Box3().setFromObject(gltf.scene).max.y>180});tilesLoaded++;$('bar').style.width=tilesLoaded/manifest.tiles.length*100+'%';$('percent').textContent=tilesLoaded+' / '+manifest.tiles.length;}}
  await Promise.all(Array.from({length:4},worker));
  const [farTree,nearTree]=await Promise.all(['tree.glb','tree_near.glb'].map(file=>loader.loadAsync('./assets/'+file)));
  for(const [model,near] of [[farTree,false],[nearTree,true]]){model.scene.updateMatrixWorld(true);model.scene.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.name.includes('leaves')){m.transparent=false;m.alphaTest=.45;m.depthWrite=true;m.side=THREE.DoubleSide;m.roughness=.9;}}const geometry=o.geometry.clone();geometry.applyMatrix4(o.matrixWorld);const inst=new THREE.InstancedMesh(geometry,o.material,manifest.trees.length);inst.count=0;inst.frustumCulled=false;inst.receiveShadow=true;scene.add(inst);treeLOD.push({inst,near});});}
  updateTreeLOD();
  avatar=await loadCharacter(scene);
  loaded=true;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;$('loader').classList.add('done');window.__cityReady=true;
 }catch(e){console.error(e);$('loadtext').textContent='加载失败，请通过本地启动器打开，或刷新重试。';$('loadtext').classList.add('error');$('percent').textContent=e.message;window.__cityError=e.message}
}
canvas.addEventListener('wheel',e=>{if(mode==='walk'){e.preventDefault();followDistance=THREE.MathUtils.clamp(followDistance+e.deltaY*.003,2.2,8);}},{passive:false});
function followCamera(dt){
 if(!avatar)return;
 const target=avatar.root.position.clone().add(new THREE.Vector3(0,1.25,0));
 const offset=new THREE.Vector3(Math.sin(yaw)*Math.cos(Math.min(pitch,0)),-Math.sin(Math.min(pitch,0)),Math.cos(yaw)*Math.cos(Math.min(pitch,0))).multiplyScalar(followDistance);
 // Pull the camera forward when its segment enters a building collider.
 let fraction=1;for(let t=.15;t<=1;t+=.05){const q=target.clone().addScaledVector(offset,t);if(blocked(q.x,q.z,q.y)){fraction=Math.max(.12,t-.08);break;}}
 const desired=target.clone().addScaledVector(offset,fraction);desired.y=Math.max(1.05,desired.y);
 camera.position.lerp(desired,1-Math.exp(-12*dt));camera.lookAt(target.clone().add(new THREE.Vector3(-Math.sin(yaw)*Math.sin(Math.max(0,pitch))*2,Math.tan(Math.max(0,pitch))*followDistance,-Math.cos(yaw)*Math.sin(Math.max(0,pitch))*2)));
}
function floorAt(x,z,currentY){
 floorRay.set(new THREE.Vector3(x,currentY+.42,z),new THREE.Vector3(0,-1,0));
 const hit=floorRay.intersectObjects(walkSurfaces,false).find(h=>h.point.y<=currentY+.40);
 return hit?hit.point.y+.015:.35;
}
function updatePlayer(dt){
 if(!avatar)return;
 const p=avatar.root.position;playerFloor=floorAt(p.x,p.z,p.y);const forward=new THREE.Vector3(-Math.sin(yaw),0,-Math.cos(yaw)),side=new THREE.Vector3(Math.cos(yaw),0,-Math.sin(yaw)),move=new THREE.Vector3();
 if(keys.has('KeyW')||keys.has('ArrowUp'))move.add(forward);if(keys.has('KeyS')||keys.has('ArrowDown'))move.sub(forward);
 if(keys.has('KeyD'))move.add(side);if(keys.has('KeyA'))move.sub(side);
 const speed=keys.has('ShiftLeft')||keys.has('ShiftRight')?4.4:1.45,before=p.clone();
 if(move.lengthSq()){
  move.normalize();const heading=Math.atan2(move.x,move.z);
  avatar.root.rotation.y+=Math.atan2(Math.sin(heading-avatar.root.rotation.y),Math.cos(heading-avatar.root.rotation.y))*(1-Math.exp(-12*dt));
  if(!blocked(p.x+move.x*speed*dt,p.z,p.y+1.5))p.x+=move.x*speed*dt;else collisionHits++;
  if(!blocked(p.x,p.z+move.z*speed*dt,p.y+1.5))p.z+=move.z*speed*dt;else collisionHits++;
 }
 playerFloor=floorAt(p.x,p.z,p.y);upVelocity-=12*dt;p.y=Math.max(playerFloor,p.y+upVelocity*dt);if(p.y===playerFloor)upVelocity=0;
 avatar.update(dt,Math.hypot(p.x-before.x,p.z-before.z)/Math.max(dt,.001),p.y>playerFloor+.02);followCamera(dt);
}
const map=$('map').getContext('2d');let frames=0,elapsed=0,fps=0,mapTimer=0;
function drawMap(){
 const ctx=map,w=280;ctx.clearRect(0,0,w,w);ctx.fillStyle='#e3e9df';ctx.fillRect(0,0,w,w);const scale=.067,cx=75,cz=91;
 ctx.fillStyle='#a0bec3';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(38,0);ctx.bezierCurveTo(15,85,45,165,180,215);ctx.lineTo(280,250);ctx.lineTo(280,280);ctx.lineTo(0,280);ctx.fill();
 if(manifest){ctx.fillStyle='#bac6b9';for(const c of manifest.colliders){ctx.fillRect(cx+c.min[0]*scale,cz+c.min[2]*scale,Math.max(1,(c.max[0]-c.min[0])*scale),Math.max(1,(c.max[2]-c.min[2])*scale))}}
 for(const [x,z] of [[0,0],[562,695],[731,588],[577,513]]){ctx.fillStyle='#55776b';ctx.beginPath();ctx.arc(cx+x*scale,cz+z*scale,3.5,0,Math.PI*2);ctx.fill()}
 const px=THREE.MathUtils.clamp(cx+camera.position.x*scale,8,272),py=THREE.MathUtils.clamp(cz+camera.position.z*scale,8,272);camera.getWorldDirection(v);ctx.save();ctx.translate(px,py);ctx.rotate(Math.atan2(v.x,-v.z));ctx.fillStyle='#1c555b';ctx.beginPath();ctx.moveTo(0,-9);ctx.lineTo(6,7);ctx.lineTo(0,4);ctx.lineTo(-6,7);ctx.closePath();ctx.fill();ctx.restore();
}
function tick(){
 const frameDt=Math.min(clock.getDelta(),.25),dt=Math.min(frameDt,.05);treeLODClock+=dt;if(treeLODClock>.5){updateTreeLOD();treeLODClock=0;}
 if(avatar&&mode!=='walk')avatar.update(dt,0,false);
 if(mode==='walk'&&loaded){for(let remaining=frameDt;remaining>0;){const step=Math.min(remaining,1/60);updatePlayer(step);remaining-=step;}}else if(mode==='orbit')orbit.update();else if(loaded){
  camera.getWorldDirection(v);if(mode==='walk')v.y=0;v.normalize();right.crossVectors(v,THREE.Object3D.DEFAULT_UP).normalize();const mv=new THREE.Vector3();
  if(keys.has('KeyW')||keys.has('ArrowUp'))mv.add(v);if(keys.has('KeyS')||keys.has('ArrowDown'))mv.sub(v);if(keys.has('KeyD'))mv.add(right);if(keys.has('KeyA'))mv.sub(right);
  if(mode==='fly'){if(keys.has('KeyE'))mv.y+=1;if(keys.has('KeyQ'))mv.y-=1}
  const speed=(mode==='fly'?85:4.5)*(keys.has('ShiftLeft')||keys.has('ShiftRight')?2.8:1);if(mv.lengthSq())mv.normalize().multiplyScalar(dt*speed);
  if(mode==='walk'){
   let nx=camera.position.x+mv.x,nz=camera.position.z+mv.z;
   if(!blocked(nx,camera.position.z,camera.position.y))camera.position.x=nx;else collisionHits++;
   if(!blocked(camera.position.x,nz,camera.position.y))camera.position.z=nz;else collisionHits++;
   upVelocity-=12*dt;camera.position.y=Math.max(2.6,camera.position.y+upVelocity*dt);if(camera.position.y===2.6)upVelocity=0;
  }else camera.position.add(mv);
  camera.position.y=Math.max(2.6,camera.position.y);camera.position.x=THREE.MathUtils.clamp(camera.position.x,-2400,2300);camera.position.z=THREE.MathUtils.clamp(camera.position.z,-1500,2200);
 }
 for(const water of waterBodies){water.material.uniforms.time.value+=dt*.22;water.material.uniforms.sunDirection.value.copy(sun.position).normalize();}
 if(waterNormal)waterNormal.offset.x+=dt*.008;if(mode==='walk'&&high)renderer.shadowMap.needsUpdate=true;renderer.render(scene,camera);frames++;elapsed+=dt;mapTimer+=dt;
 if(elapsed>1){fps=Math.round(frames/elapsed);$('status').textContent=(loaded?(mode==='walk'?'步行':mode==='fly'?'飞行':'俯瞰')+' · '+Math.round(camera.position.y)+' m · '+fps+' FPS':'加载城市 '+tilesLoaded+' / 54');frames=0;elapsed=0;window.__cityStats={fps,calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,position:camera.position.toArray(),mode,collisionHits,tilesLoaded};}
 if(mapTimer>.15){drawMap();for(const tile of cityTiles)tile.scene.visible=tile.landmark||!tile.center||((camera.position.x-tile.center[0])**2+(camera.position.z-tile.center[2])**2<(mode==='orbit'?2400:850)**2);mapTimer=0}requestAnimationFrame(tick);
}
window.__cityTest={teleport:(x,y,z,angle)=>{avatar.root.position.set(x,y,z);yaw=angle;pitch=-.18;upVelocity=0;followCamera(1);},floorAt,getAvatar:()=>avatar?{name:avatar.name,height:avatar.height,floor:playerFloor,sourceHeight:avatar.sourceHeight,animation:avatar.state,position:avatar.root.position.toArray(),rotation:avatar.root.rotation.y}:null,setMode,preset,blocked,getCamera:()=>camera.position.toArray(),keyDown:k=>keys.add(k),keyUp:k=>keys.delete(k)};
init();tick();
