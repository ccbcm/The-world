from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'网页漫游/main.js';s=p.read_text(encoding='utf-8-sig')
needle='  manifest=await fetch'
code='''  const bindings=await fetch('./assets/material-bindings.json').then(r=>r.json());
  const textureCache=new Map();
  for(const binding of bindings){
   const textures=await Promise.all(['diff','nor_gl','rough'].map(async channel=>{const key=binding.asset+'_'+channel+'_'+binding.res;if(!textureCache.has(key)){const t=await new THREE.TextureLoader().loadAsync('./assets/textures/'+key+'.jpg');t.wrapS=t.wrapT=THREE.RepeatWrapping;t.flipY=false;t.anisotropy=8;if(channel==='diff')t.colorSpace=THREE.SRGBColorSpace;textureCache.set(key,t);}return textureCache.get(key);}));
   scannedMaterials.set(binding.name,new THREE.MeshStandardMaterial({name:binding.name,map:textures[0],normalMap:textures[1],roughnessMap:textures[2],normalScale:new THREE.Vector2(binding.strength,binding.strength),color:new THREE.Color(...binding.tint),roughness:1,side:THREE.DoubleSide}));
  }
'''
if 'const bindings=await fetch' not in s:s=s.replace(needle,code+needle)
s=s.replace('sourceHeight:avatar.sourceHeight,position:','sourceHeight:avatar.sourceHeight,animation:avatar.state,position:')
s=s.replace("m.side=THREE.DoubleSide;if(/框", "m.side=THREE.DoubleSide;if(/标线/.test(m.name)){m.polygonOffset=true;m.polygonOffsetFactor=-1;m.polygonOffsetUnits=-1;}if(/框")
p.write_text(s,encoding='utf8')
