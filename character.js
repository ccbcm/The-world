import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {VRMLoaderPlugin} from './vendor/three-vrm/three-vrm.module.min.js';

// VRM 0.x includes standard glTF skinning and textures; use those directly.
// Procedural gait is original code, independent of third-party motion files.
export async function loadCharacter(scene){
 const loader=new GLTFLoader();loader.register(parser=>new VRMLoaderPlugin(parser));
 const gltf=await loader.loadAsync('./assets/character/Vita.vrm'),vrm=gltf.userData.vrm;
 // Keep the authored standard glTF appearance; only use VRM for rig dynamics.
 const original=await new GLTFLoader().loadAsync('./assets/character/Vita.vrm'),materials=new Map();
 original.scene.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])materials.set(m.name,m);});
 gltf.scene.traverse(o=>{if(o.isMesh)o.material=Array.isArray(o.material)?o.material.map(m=>materials.get(m.name)||m):materials.get(o.material.name)||o.material;});
 vrm.humanoid.autoUpdateHumanBones=false;
 const root=new THREE.Group(),visual=gltf.scene;root.name='Vita · 1.60 m';root.add(visual);scene.add(root);
 visual.updateMatrixWorld(true);const bounds=new THREE.Box3().setFromObject(visual),height=bounds.max.y-bounds.min.y;
 visual.scale.setScalar(1.60/height);visual.position.y=-bounds.min.y*visual.scale.x;visual.rotation.y=Math.PI;
 const bones={},rest={};
 for(const [name,{node}] of Object.entries(vrm.humanoid.rawHumanBones)){bones[name]=node;rest[name]=node.quaternion.clone();}
 visual.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.isOutline){m.visible=false;continue;}m.side=THREE.DoubleSide;m.roughness=.85;m.metalness=0;}}});
 root.position.set(-180,.8,148);let phase=0,amount=0,run=0,air=0,clock=0,landing=0,wasAir=false,smoothing=1;
 const hipRest=bones.hips.position.clone(),q=new THREE.Quaternion(),delta=new THREE.Quaternion(),euler=new THREE.Euler();
 const state={speed:0,phase:0,air:0,run:0,engine:'three-vrm 3.5.5 + procedural gait'};
 function pose(name,x=0,y=0,z=0){if(bones[name]){q.copy(rest[name]).multiply(delta.setFromEuler(euler.set(x,y,z)));bones[name].quaternion.slerp(q,smoothing);}}
 function update(dt,speed,airborne){
  dt=Math.min(dt,.05);clock+=dt;smoothing=dt?1-Math.exp(-18*dt):1;
  amount=THREE.MathUtils.damp(amount,Math.min(1,speed/.9),8,dt);run=THREE.MathUtils.damp(run,speed>2.6?1:0,6,dt);air=THREE.MathUtils.damp(air,airborne?1:0,12,dt);
  if(wasAir&&!airborne)landing=.07;wasAir=airborne;landing=THREE.MathUtils.damp(landing,0,12,dt);
  phase+=dt*(6.8+run*3.7)*amount;const swing=Math.sin(phase),stride=(.38+run*.30)*amount*(1-air),breath=Math.sin(clock*1.8)*.009;
  for(const [side,sign] of [['left',1],['right',-1]]){
   const t=phase+(sign===1?0:Math.PI),lift=Math.max(0,-Math.sin(t)),support=Math.max(0,Math.sin(t));
   pose(side+'UpperLeg',Math.sin(t)*stride-air*.25,0,sign*amount*.015);
   pose(side+'LowerLeg',lift*(.7+run*.65)*amount*(1-air)+air*.65+landing*1.7);
   pose(side+'Foot',-lift*.32*amount+support*.16*amount-air*.12);pose(side+'Toes',-support*.20*amount);
   pose(side+'Shoulder',0,sign*swing*amount*.035,sign*breath);
   pose(side+'UpperArm',-Math.sin(t)*stride*.72-air*.20,0,sign*(1.28-air*.14));
   pose(side+'LowerArm',-(.18+run*.85+lift*.16*amount+air*.25),0,-sign*.06);pose(side+'Hand',breath,0,sign*.035);
   for(const finger of ['Index','Middle','Ring','Little'])for(const joint of ['Proximal','Intermediate','Distal'])pose(side+finger+joint,0,0,-sign*(.12+run*.18));
   pose(side+'ThumbProximal',0,sign*.12,-sign*.10);
  }
  pose('hips',run*.055,Math.sin(phase)*amount*.045,Math.sin(phase)*amount*.022);
  pose('spine',breath+run*.045+landing*.5,-Math.sin(phase)*amount*.035,-Math.sin(phase)*amount*.014);
  pose('chest',breath*.5,-Math.sin(phase)*amount*.025,0);pose('neck',-run*.025,Math.sin(clock*.4)*.018,0);pose('head',-breath,Math.sin(clock*.4)*.012,0);
  bones.hips.position.copy(hipRest);bones.hips.position.y+=(Math.cos(phase*2)*.009*amount+breath*.2-landing)/visual.scale.x;
  const blinkPhase=clock%4.3;vrm.expressionManager?.setValue('blink',blinkPhase<.16?Math.sin(blinkPhase/.16*Math.PI):0);
  root.updateMatrixWorld(true);vrm.update(dt);Object.assign(state,{speed,phase,air,run});
 }
 update(0,0,false);
 return {root,update,height:1.60,name:'Vita',bones,sourceHeight:height,state};
}


