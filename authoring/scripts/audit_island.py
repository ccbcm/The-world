import bpy,json
from mathutils import Vector
for o in bpy.context.scene.objects:
 if o.type not in ['MESH','CURVE']:continue
 if any(s in o.name for s in ['环岛','环形','花坛','草地']):
  bb=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(bb,Vector())/8
  if (Vector((center.x,center.y))-Vector((67,-192))).length<90:print(o.name,list(center),list(o.dimensions))
print('MATERIALS', [m.name for m in bpy.data.materials if m.users>0])
