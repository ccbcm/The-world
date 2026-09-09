import bpy,json,math
from pathlib import Path
s=bpy.context.scene
out=Path(bpy.data.filepath).parent
points=[o for o in bpy.data.objects if o.name.startswith('天线尖端')]
from mathutils import Vector
top=max((points[0].matrix_world@Vector(v)).z for v in points[0].bound_box)
cams=[o for o in bpy.data.objects if o.type=='CAMERA']
report={'blender':bpy.app.version_string,'objects':len(s.objects),'meshes':len(bpy.data.meshes),'cameras':[o.name for o in cams],'tower_top_m':top,'engine_on_open':s.render.engine,'missing_images':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and i.filepath and not Path(bpy.path.abspath(i.filepath)).exists()],'finite_object_transforms':all(math.isfinite(v) for o in s.objects for row in o.matrix_world for v in row),'preview_files':[{ 'name':p.name,'bytes':p.stat().st_size} for p in out.glob('preview_*.png')]}
assert abs(top-468)<.01,top
assert len(cams)==3
assert report['finite_object_transforms']
assert not report['missing_images']
assert len(report['preview_files'])==3
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True),flush=True)
