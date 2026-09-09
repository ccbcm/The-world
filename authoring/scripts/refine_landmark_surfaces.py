import bpy,ast,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(bpy.data.filepath).parent
tree=ast.parse((ROOT/'制作资料/scripts/build_pearl.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'collection','put','material','mesh','instance','box','cyl','line','ring'}],type_ignores=[]),'helpers','exec'))
cache={};COL=None
collection('16 金茂金属肋与塔冠细化')
silver=bpy.data.materials['金茂银灰结构']
def bsdf(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bsdf(silver).inputs['Base Color'].default_value=(.48,.51,.52,1)
for name,col,metal,rough in [('超高层蓝灰幕墙',(.19,.27,.32,1),.68,.20),('金茂灰玻璃',(.26,.30,.31,1),.60,.24),('v02 中性蓝灰幕墙',(.22,.32,.36,1),.63,.22),('v02 绿灰幕墙',(.18,.28,.25,1),.60,.23)]:
 m=bpy.data.materials.get(name)
 if m:
  p=bsdf(m);p.inputs['Base Color'].default_value=col;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
  p.inputs['Coat Weight'].default_value=.22;p.inputs['Coat Roughness'].default_value=.13
  m.diffuse_color=col
cx,cy=576.74,-513.44
# Replace the visibly incorrect solid conical crown with open octagonal steelwork.
for o in list(bpy.data.objects):
 if o.name.startswith(('金茂层叠冠部','金茂冠部横梁')):bpy.data.objects.remove(o,do_unlink=True)
levels=[(353,11.8),(361,11),(369,9.2),(378,7.6),(387,5.8),(398,3.2),(407,1.3)]
for j,(z,r) in enumerate(levels):
 pp=[(cx+r*math.cos(math.pi/8+i*math.tau/8),cy+r*math.sin(math.pi/8+i*math.tau/8),z) for i in range(8)]
 line('金茂冠部八角环梁',pp,.24,silver,True)
 if j==len(levels)-1:break
 zn,rn=levels[j+1]
 for i in range(8):
  a=math.pi/8+i*math.tau/8;b=a+math.tau/8
  p=(cx+r*math.cos(a),cy+r*math.sin(a),z);q=(cx+rn*math.cos(a),cy+rn*math.sin(a),zn)
  cyl('金茂冠部收分钢肋',p,q,.3,silver,n=8)
  line('金茂冠部斜撑',[p,(cx+rn*math.cos(b),cy+rn*math.sin(b),zn)],.10,silver)
  for zz in range(int(z)+2,int(zn),2):
   rr=r+(rn-r)*(zz-z)/(zn-z)
   # Horizontal narrow louvres leave sky visible through the framework.
   line('金茂冠部百叶',[(cx+rr*math.cos(a),cy+rr*math.sin(a),zz),(cx+rr*math.cos(b),cy+rr*math.sin(b),zz)],.085,silver)
# Raised metal strips flank the existing stepped glass bays, following each actual model tier.
for o in list(bpy.data.objects):
 if not (o.type=='MESH' and o.name.startswith('金茂第')):continue
 vs=[o.matrix_world@v.co for v in o.data.vertices];lo=min(p.z for p in vs);hi=max(p.z for p in vs)
 pp=sorted({(round(p.x,4),round(p.y,4)) for p in vs},key=lambda p:math.atan2(p[1]-cy,p[0]-cx))
 for i,a in enumerate(pp):
  b=pp[(i+1)%len(pp)];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
  for t in [.055,.945]:
   x=a[0]+dx*t;y=a[1]+dy*t;off=Vector((x-cx,y-cy,0)).normalized()*.22
   cyl('金茂凸起银色竖肋',(x+off.x,y+off.y,lo),(x+off.x,y+off.y,hi),.46,silver,n=6)
s=bpy.context.scene
for n in s.world.node_tree.nodes:
 if n.type=='BACKGROUND' and n.inputs['Color'].is_linked and n.inputs['Color'].links[0].from_node.type=='TEX_ENVIRONMENT':n.inputs['Strength'].default_value=1.1
s['jinmao_detail_source']='https://www.som.com/projects/jin-mao-tower/; reference-led approximation, not construction drawings'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.device='GPU'
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.camera=bpy.data.objects['三座超高层建筑'];s.render.filepath=str(ROOT/'预览/三座超高层.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.filepath=str(ROOT/'预览/实拍材质全景.png');bpy.ops.render.render(write_still=True)
s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
print('LANDMARK_SURFACES_SAVED',flush=True)
