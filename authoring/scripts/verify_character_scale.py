import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(bpy.data.filepath).parent;c=bpy.data.collections['20 人物 · Vita 可编辑骨骼'];root=bpy.data.objects['Vita 控制根 · 身高1.60m']
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
def bounds():
 coords=[]
 for o in c.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dep);m=ev.to_mesh();coords.extend([o.matrix_world@v.co for v in m.vertices]);ev.to_mesh_clear()
 return min(p.z for p in coords),max(p.z for p in coords)
lo,hi=bounds();root.scale*=1.6/(hi-lo);bpy.context.view_layer.update();lo,hi=bounds();root.location.z+=.8-lo;bpy.context.view_layer.update();lo,hi=bounds()
assert abs(hi-lo-1.6)<.002,(lo,hi)
(R/'制作资料/人物尺度验证.json').write_text(json.dumps({'height_m':hi-lo,'feet_z':lo,'editable_rig':any(o.type=='ARMATURE' for o in c.objects)},indent=2),encoding='utf8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print('VERIFIED_CHARACTER',lo,hi)
