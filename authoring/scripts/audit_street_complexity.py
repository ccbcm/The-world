import bpy,json
from pathlib import Path
s=bpy.context.scene;d=bpy.context.evaluated_depsgraph_get();rows=[]
for o in s.objects:
 if any(c.name.startswith('21 ') for c in o.users_collection) and o.type in ['MESH','CURVE']:
  ev=o.evaluated_get(d);m=ev.to_mesh();rows.append((len(m.vertices),o.name));ev.to_mesh_clear()
print('TOTAL',sum(x[0] for x in rows));print(sorted(rows,reverse=True)[:12])
