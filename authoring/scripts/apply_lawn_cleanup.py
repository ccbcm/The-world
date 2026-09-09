import bpy,bmesh,json
from pathlib import Path
R=Path(bpy.data.filepath).parent;data=json.loads((R/'制作资料/草坪修正.json').read_text(encoding='utf8'));groups={}
for f in data:groups.setdefault(f['name'],[]).append(f)
for name,items in groups.items():
 o=bpy.data.objects[name]
 if o.data.users>1:o.data=o.data.copy()
 bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[f['polygon']] for f in items],context='FACES');bm.to_mesh(o.data);bm.free()
 vs=[];fs=[]
 for f in items:
  for tri in f['triangles']:i=len(vs);vs.extend([(x,y,f['z']) for x,y in tri]);fs.append((i,i+1,i+2))
 if not vs:continue
 me=bpy.data.meshes.new('环岛外草坪');me.from_pydata(vs,[],fs);me.materials.append(bpy.data.materials['v02 草地']);ob=bpy.data.objects.new('环岛外草坪裁切',me);bpy.context.scene.collection.objects.link(ob);uv=me.uv_layers.new(name='RealWorldPBR')
 for p in me.polygons:
  for li in p.loop_indices:v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/5,v.y/5)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print('CLEANED_LAWN',len(groups))
