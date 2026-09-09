import bpy,json,math,ast
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(bpy.data.filepath).parent;s=bpy.context.scene
bpy.context.preferences.view.language='en_US'
t=ast.parse((R/'制作资料/scripts/build_pearl.py').read_text(encoding='utf8'));names={'collection','put','material','mesh','polygon','line','ring'};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'));cache={};COL=None
targets=[o for o in s.objects if o.get('osm_id')=='484295018'];names=[o.name for o in targets]
for o in list(bpy.data.objects):
 if any(o.name==n or o.name.startswith(n+' ·') or o.name.startswith(n+'立面') for n in names):bpy.data.objects.remove(o,do_unlink=True)
# The aerial photo shows a planted flower island, not mature trees at the roundabout center.
for o in list(bpy.data.objects):
 if o.name.startswith('树冠') and math.hypot(o.location.x-67,o.location.y+192)<24:bpy.data.objects.remove(o,do_unlink=True)
collection('23 实景纠错 · 环岛花坛')
red=material('环岛低矮花带',(.28,.025,.03),0,.95);stone=bpy.data.materials['滨江浅灰石材']
for k in range(5):
 a=k*math.tau/5;pts=[]
 for j in range(48):
  t=j*math.tau/48;u=5*math.cos(t)+9;v=2.5*math.sin(t);pts.append((67+u*math.cos(a)-v*math.sin(a),-192+u*math.sin(a)+v*math.cos(a)))
 polygon('环岛低矮季节花带',pts,.58,red)
ring('环岛内缘',67,-192,.5,20,.12,stone)
cam=bpy.data.objects['低层建筑实景校核'];cam.location=(125,5,32);cam.rotation_euler=(Vector((181,86,15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=40
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print('REMOVED FALSE ROOF VOLUME',names)
