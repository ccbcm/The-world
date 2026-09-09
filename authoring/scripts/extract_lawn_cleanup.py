import bpy,json
from pathlib import Path
R=Path(bpy.data.filepath).parent;items=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.name.startswith('统一环岛') or not any(m and m.name=='v02 草地' for m in o.data.materials):continue
 for p in o.data.polygons:
  if o.data.materials[p.material_index].name!='v02 草地':continue
  co=[o.matrix_world@o.data.vertices[i].co for i in p.vertices]
  if max(v.z for v in co)-min(v.z for v in co)<.1:items.append({'name':o.name,'polygon':p.index,'points':[[v.x,v.y] for v in co],'z':sum(v.z for v in co)/len(co)})
(R/'制作资料/草坪面索引.json').write_text(json.dumps(items,ensure_ascii=False),encoding='utf8');print('LAWN_FACES',len(items))
