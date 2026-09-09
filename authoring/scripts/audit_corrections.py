import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(bpy.data.filepath).parent
out=[]
for o in bpy.context.scene.objects:
 if o.type=='FONT' or o.name.startswith(('树冠','树干','路缘','道路','路灯','河堤','连续路网')) or o.get('osm_id'):
  out.append(dict(name=o.name,type=o.type,loc=list(o.location),scale=list(o.scale),dimensions=list(o.dimensions),osm=o.get('osm_id'),body=o.data.body if o.type=='FONT' else None,bounds=[list(o.matrix_world@Vector(v)) for v in o.bound_box]))
(r/'制作资料/待修正场景审计.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf8')
print('TEXTS',[(o.name,o.data.body,list(o.location)) for o in bpy.data.objects if o.type=='FONT'],flush=True)
print('GROUPS',[(c.name,len(c.objects)) for c in bpy.data.collections],flush=True)
