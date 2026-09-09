import bpy,ast,json,math
from pathlib import Path
from mathutils import Vector
R=Path(bpy.data.filepath).parent;s=bpy.context.scene;bpy.context.preferences.view.language='en_US'
t=ast.parse((R/'制作资料/scripts/build_pearl.py').read_text(encoding='utf8'));names={'collection','put','material','mesh','instance','cyl','line'};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'));cache={};COL=bpy.data.collections['21 道路与连廊 · 地面高架分层']
plan=json.loads((R/'制作资料/道路分层修正方案.json').read_text(encoding='utf8'));mat=bpy.data.materials['道路缘石']
for x,y in plan['bridge_piers']:cyl('连廊承重墩 · 避开车道',(x,y,.7),(x,y,6.5),.45,mat,n=12)
entries=[Vector(e['points'][0]) for e in plan['stairs']]
for o in list(COL.objects):
 if not o.name.startswith('连廊连续扶手') or o.type!='CURVE':continue
 material=o.data.materials[0];radius=o.data.bevel_depth
 for spline in o.data.splines:
  pts=[Vector(p.co[:3]) for p in spline.points];runs=[];run=[]
  for p in pts:
   if any((Vector((p.x,p.y))-e).length<7 for e in entries):
    if len(run)>1:runs.append(run)
    run=[]
   else:run.append(tuple(p))
  if len(run)>1:runs.append(run)
  for points in runs:line('连廊扶手 · 入口留空',points,radius,material)
 bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print('BRIDGE_STRUCTURE_SAVED')
