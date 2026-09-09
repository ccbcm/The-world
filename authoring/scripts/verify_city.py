import bpy,json,math
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;dest=Path(bpy.data.filepath).parent
def top(prefix):
 objs=[o for o in s.objects if o.name.startswith(prefix)]
 assert objs,prefix
 return max((o.matrix_world@Vector(v)).z for o in objs for v in o.bound_box)
tops={p:top(p) for p in ['天线尖端','上海中心632m扭转幕墙','环球金融中心492m主体','金茂420.5m尖塔','平安顶部尖端203m']}
for (name,z),h in zip(tops.items(),[468,632,492,420.5,203]):assert abs(z-h)<.03,(name,z,h)
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()]
assert not missing,missing
finite=all(math.isfinite(v) for o in s.objects for row in o.matrix_world for v in row);assert finite
character=bpy.data.collections.get('20 人物 · Vita 可编辑骨骼')
if character:
 deps=bpy.context.evaluated_depsgraph_get();coords=[]
 for o in character.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();coords.extend([o.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
 low=min(p.z for p in coords);high=max(p.z for p in coords)
 assert abs(high-low-1.6)<.002,(low,high)
 (dest/'制作资料/人物尺度验证.json').write_text(json.dumps({'height_m':high-low,'feet_z':low,'editable_rig':any(o.type=='ARMATURE' for o in character.objects)},indent=2),encoding='utf8')
report=dict(file=bpy.data.filepath,blender=bpy.app.version_string,objects=len(s.objects),meshes=len(bpy.data.meshes),heights=tops,missing_images=missing,finite_transforms=finite,render_engine=s.render.engine,cameras=[o.name for o in s.objects if o.type=='CAMERA'],editable_geometry=True,website_game_complete=False)
(dest/'保存验证.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True),flush=True)
