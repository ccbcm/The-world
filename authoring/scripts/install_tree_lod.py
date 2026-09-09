from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'网页漫游/main.js';s=p.read_text(encoding='utf8')
a=s.index("  const tree=await loader.loadAsync('./assets/tree.glb')");b=s.index('  avatar=await loadCharacter(scene);',a)
s=s[:a]+'''  const [farTree,nearTree]=await Promise.all(['tree.glb','tree_near.glb'].map(file=>loader.loadAsync('./assets/'+file)));
  for(const [model,near] of [[farTree,false],[nearTree,true]]){model.scene.updateMatrixWorld(true);model.scene.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.name.includes('leaves')){m.transparent=false;m.alphaTest=.45;m.depthWrite=true;m.side=THREE.DoubleSide;m.roughness=.9;}}const geometry=o.geometry.clone();geometry.applyMatrix4(o.matrixWorld);const inst=new THREE.InstancedMesh(geometry,o.material,manifest.trees.length);inst.count=0;inst.frustumCulled=false;inst.receiveShadow=true;scene.add(inst);treeLOD.push({inst,near});});}
  updateTreeLOD();
'''+s[b:]
helper='''const treeLOD=[];let treeLODClock=0;const treeMatrix=new THREE.Matrix4(),treeRotation=new THREE.Quaternion(),treePosition=new THREE.Vector3(),treeScale=new THREE.Vector3();
function updateTreeLOD(){if(!manifest)return;for(const group of treeLOD){let count=0;for(const t of manifest.trees){const close=(camera.position.x-t.p[0])**2+(camera.position.y-t.p[1])**2+(camera.position.z-t.p[2])**2<180**2;if(close!==group.near)continue;treePosition.fromArray(t.p);treeRotation.setFromAxisAngle(THREE.Object3D.DEFAULT_UP,t.ry);treeScale.fromArray(t.s);treeMatrix.compose(treePosition,treeRotation,treeScale);group.inst.setMatrixAt(count++,treeMatrix);}group.inst.count=count;group.inst.instanceMatrix.needsUpdate=true;}}
'''
s=s.replace('const scannedMaterials=new Map();',helper+'const scannedMaterials=new Map();')
s=s.replace(' const frameDt=Math.min(clock.getDelta(),.25),dt=Math.min(frameDt,.05);',' const frameDt=Math.min(clock.getDelta(),.25),dt=Math.min(frameDt,.05);treeLODClock+=dt;if(treeLODClock>.5){updateTreeLOD();treeLODClock=0;}')
p.write_text(s,encoding='utf8')
