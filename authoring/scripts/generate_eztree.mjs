import {Tree} from '../第三方/ez-tree-node/tree.js';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const preset=JSON.parse(fs.readFileSync(new URL('../第三方/ez-tree-node/presets/oak_medium.json',import.meta.url)));
preset.branch.length[0]=28;preset.branch.start[1]=.40;preset.leaves.count=12;
const tree=new Tree();tree.loadFromJson(preset);
const result=[];let maxY=0,minY=1e9;
for(const mesh of [tree.branchesMesh,tree.leavesMesh]){const p=mesh.geometry.attributes.position;for(let i=0;i<p.count;i++){maxY=Math.max(maxY,p.getY(i));minY=Math.min(minY,p.getY(i));}}
const scale=10/(maxY-minY);
for(const [kind,mesh] of [['bark',tree.branchesMesh],['leaves',tree.leavesMesh]]){
 const g=mesh.geometry,p=g.attributes.position,verts=[];for(let i=0;i<p.count;i++)verts.push([p.getX(i)*scale,-p.getZ(i)*scale,(p.getY(i)-minY)*scale]);
 result.push({kind,vertices:verts,index:Array.from(g.index?.array||Array.from({length:p.count},(_,i)=>i)),uv:Array.from(g.attributes.uv.array)});
}
fs.writeFileSync(new URL('../eztree_geometry.json',import.meta.url),JSON.stringify(result));console.log(result.map(x=>[x.kind,x.vertices.length,x.index.length/3]));
