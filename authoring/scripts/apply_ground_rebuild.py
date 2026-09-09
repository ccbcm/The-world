import bpy,json
from pathlib import Path
R=Path(bpy.data.filepath).parent;plan=json.loads((R/'制作资料/道路重铺.json').read_text())
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith(('连续路网','连续道路缘石','车道分界虚线','重铺道路','重铺人行','重铺标线')) or o.name.endswith(' · OSM道路'):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
c=bpy.data.collections.get('24 道路重铺') or bpy.data.collections.new('24 道路重铺')
if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
for key,name,z,mat in [('roads','重铺道路 · 连续沥青',.76,'道路沥青'),('walks','重铺人行 · 独立铺装',.80,'人行浅色铺装'),('marks','重铺标线 · 路口留白',.775,'道路标线白')]:
 vs=[];fs=[]
 for tri in plan[key]:k=len(vs);vs.extend([(x,y,z) for x,y in tri]);fs.append((k,k+1,k+2))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);c.objects.link(o);m=bpy.data.materials[mat];me.materials.append(m)
 uv=me.uv_layers.new(name='RealWorldPBR')
 for p in me.polygons:
  for li in p.loop_indices:v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)
 m['texture_repeat_metres']=3;o['walkable']=True
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('REBUILT',len(removed),plan['source_ways'])
