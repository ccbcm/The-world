from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'网页漫游/main.js';s=p.read_text(encoding='utf8')
s=s.replace("scene.fog=new THREE.FogExp2('#b8cbd4',.00020)","scene.fog=new THREE.FogExp2('#b8cbd4',.000075)")
s=s.replace('scene.environmentIntensity=.07;','scene.environmentIntensity=.07;scene.add(sky);sky.material.depthWrite=false;sky.frustumCulled=false;')
s=s.replace("mode==='walk'?.25:1.48","mode==='walk'?1.35:1.48")
# Decouple looking up from lowering the orbit camera into the ground.
s=s.replace('Math.cos(pitch),-Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch)', 'Math.cos(Math.min(pitch,0)),-Math.sin(Math.min(pitch,0)),Math.cos(yaw)*Math.cos(Math.min(pitch,0))')
s=s.replace('camera.lookAt(target);\n}',"camera.lookAt(target.clone().add(new THREE.Vector3(-Math.sin(yaw)*Math.sin(Math.max(0,pitch))*2,Math.tan(Math.max(0,pitch))*followDistance,-Math.cos(yaw)*Math.sin(Math.max(0,pitch))*2)));\n}")
s=s.replace("manifest.colliders.forEach(addCollider);", "manifest.colliders.forEach(addCollider);manifest.trees.forEach(t=>{const r=Math.max(.18,.22*Math.max(t.s[0],t.s[2]));addCollider({name:'tree trunk',min:[t.p[0]-r,t.p[1],t.p[2]-r],max:[t.p[0]+r,t.p[1]+4,t.p[2]+r]});});")
# A physical ray contact layer covers walls, columns and rails missing OSM metadata.
s=s.replace('const obstacleGrid=new Map(),gridSize=80;',"const obstacleGrid=new Map(),gridSize=80;const solidMeshes=[],contactRay=new THREE.Raycaster(),contactDirections=[new THREE.Vector3(1,0,0),new THREE.Vector3(-1,0,0),new THREE.Vector3(0,0,1),new THREE.Vector3(0,0,-1)];")
s=s.replace(' }return false;\n}'," }\n for(const entry of solidMeshes){if(x<entry.box.min.x-.38||x>entry.box.max.x+.38||z<entry.box.min.z-.38||z>entry.box.max.z+.38||y<entry.box.min.y||y-1.3>entry.box.max.y)continue;for(const h of [y-1.1,y-.25])for(const d of contactDirections){contactRay.set(new THREE.Vector3(x,h,z),d);contactRay.far=.38;if(contactRay.intersectObject(entry.mesh,false).length)return true;}}return false;\n}")
s=s.replace("if(scannedMaterials.has(o.material?.name))", "if(!/道路|铺装|城市地表|草地|滨江浅灰|步行桥面|桥接台阶|黄浦江|标线|踏面/.test(o.material?.name||'') ){const box=new THREE.Box3().setFromObject(o);if(box.max.y-box.min.y>.8)solidMeshes.push({mesh:o,box});}if(scannedMaterials.has(o.material?.name))")
s=s.replace("const hdr=await new HDRLoader()", "for(const name of ['步行桥面 · 7m','桥接台阶'])scannedMaterials.set(name,scannedMaterials.get('人行浅色铺装'));\n  const hdr=await new HDRLoader()")
# A repeatable cloud opacity texture on a high dome; no city photograph projected around the player.
cloud='''
const cloudCanvas=document.createElement('canvas');cloudCanvas.width=512;cloudCanvas.height=256;
const cloudContext=cloudCanvas.getContext('2d'),cloudPixels=cloudContext.createImageData(512,256);
for(let y=0;y<256;y++)for(let x=0;x<512;x++){let n=0;for(let k=1;k<=6;k++){n+=Math.sin(x*.012*k+Math.sin(y*.019*k)*2+k)*Math.cos(y*.017*k+k*.8)/k;}const i=(y*512+x)*4;cloudPixels.data[i]=255;cloudPixels.data[i+1]=255;cloudPixels.data[i+2]=255;cloudPixels.data[i+3]=Math.max(0,Math.min(95,(n-.35)*75))*Math.sin(y/256*Math.PI);}
cloudContext.putImageData(cloudPixels,0,0);const cloudTexture=new THREE.CanvasTexture(cloudCanvas);cloudTexture.wrapS=THREE.RepeatWrapping;
const clouds=new THREE.Mesh(new THREE.SphereGeometry(6000,64,32,0,Math.PI*2,0,Math.PI*.49),new THREE.MeshBasicMaterial({map:cloudTexture,transparent:true,side:THREE.BackSide,depthWrite:false,fog:false}));clouds.renderOrder=-1;scene.add(clouds);
'''
s=s.replace('const hemi=new THREE.HemisphereLight',cloud+'\nconst hemi=new THREE.HemisphereLight')
p.write_text(s,encoding='utf8')
print('UPDATED web sky, camera and solid contacts')
