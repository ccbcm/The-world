import * as THREE from 'three';
// World-space, metre-scaled architectural finish. Original meshes/colliders stay intact.
export function createArchitectureFinish(){
 const dusk={value:0},materials=new Map();
 function apply(mesh){
  if(!mesh.isMesh)return;
  const finish=m=>{
   if(!m||m.userData.architectureFinish)return m;
   const name=m.name||'';
   const glass=/幕墙|玻璃|橱窗|深色窗/.test(name)&&!/框|铝肋/.test(name);
   const stone=/石材|白麻|混凝土|石$|铝板/.test(name);
   const roof=/屋面|铜板/.test(name);
   const metal=/框|铝肋|银灰结构/.test(name);
   if(!(glass||stone||roof||metal))return m;
   if(materials.has(m.uuid))return materials.get(m.uuid);
   const n=m.clone();n.userData.architectureFinish=true;
   n.roughness=glass?.26:metal?.38:roof?.78:.72;
   n.metalness=glass?.48:metal?.65:roof?.25:.06;
   n.envMapIntensity=glass?1.15:.65;
   const kind=glass?0:stone?1:roof?2:3;
   n.onBeforeCompile=s=>{
    s.uniforms.cityDusk=dusk;
    s.vertexShader='varying vec3 cityWorld;\n'+s.vertexShader;
    s.vertexShader=s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ncityWorld=(modelMatrix*vec4(position,1.0)).xyz;');
    s.fragmentShader='varying vec3 cityWorld;\nuniform float cityDusk;\nfloat cityHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}\n'+s.fragmentShader;
    s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
     vec3 cn=abs(normalize(cross(dFdx(cityWorld),dFdy(cityWorld))));
     vec2 cp=vec2(cn.x>cn.z?cityWorld.z:cityWorld.x,cityWorld.y);
     float wall=1.0-smoothstep(.65,.9,cn.y);
     vec2 cell=cp/vec2(2.6,3.8), f=fract(cell), aa=max(fwidth(cell)*1.2,vec2(.002));
     float pane=smoothstep(.035,.035+aa.x,f.x)*(1.0-smoothstep(.965-aa.x,.965,f.x))*smoothstep(.10,.10+aa.y,f.y)*(1.0-smoothstep(.90-aa.y,.90,f.y));
     float seed=cityHash(floor(cell));
     float farFade=1.0-smoothstep(.18,.6,max(aa.x,aa.y));
     float cityLit=0.0;
     ${kind===0?`float blind=mix(1.0,.48,step(.72,seed)*step(.52,f.y));
     vec3 tint=mix(vec3(.36,.53,.62),vec3(.72,.82,.83),seed)*blind;
     tint*=mix(.58,1.15,smoothstep(.1,.9,f.y));
     diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb*tint*1.65,mix(.35,1.0,farFade)*wall);
     diffuseColor.rgb*=mix(1.0,mix(.32,1.0,pane),farFade*wall);
     cityLit=step(.68,seed)*pane*wall*cityDusk;
     diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.65,.38,.15),cityLit*.35);`:
     kind===1?`vec2 sf=fract(cp/vec2(3.2,1.3));vec2 sa=max(fwidth(cp/vec2(3.2,1.3)),vec2(.002));float seam=smoothstep(.012,.012+sa.x,sf.x)*smoothstep(.025,.025+sa.y,sf.y);diffuseColor.rgb*=mix(.72,1.04,seam)*mix(.94,1.04,cityHash(floor(cp/vec2(3.2,1.3))));`:
     kind===2?`vec2 rf=fract(cityWorld.xz/3.0);float joint=smoothstep(.025,.07,min(rf.x,rf.y));diffuseColor.rgb*=mix(.55,1.1,joint);`:
     `diffuseColor.rgb*=.86+.14*sin(cp.y*16.0)*sin(cp.y*16.0);`}
    `);
    s.fragmentShader=s.fragmentShader.replace('#include <emissivemap_fragment>','#include <emissivemap_fragment>\ntotalEmissiveRadiance+=vec3(1.0,.56,.22)*cityLit*.65;');
   };
   n.customProgramCacheKey=()=> 'city-finish-1-'+kind;
   materials.set(m.uuid,n);return n;
  };
  mesh.material=Array.isArray(mesh.material)?mesh.material.map(finish):finish(mesh.material);
 }
 return {apply,setDusk:value=>dusk.value=value,materials};
}
