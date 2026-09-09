import bpy,ast,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(bpy.data.filepath).parent
bpy.context.preferences.view.language='en_US'
tree=ast.parse((ROOT/'制作资料/scripts/build_pearl.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'collection','put','material','mesh','instance','box','cyl','line'}],type_ignores=[]),'helpers','exec'))
cache={};COL=None
collection('17 滨江实景细部 · 地图岸线')
metal=material('滨江栏杆拉丝不锈钢',(.36,.39,.4),.8,.38)
features=json.loads((ROOT/'制作资料/reference/map_features.json').read_text(encoding='utf-8'))
river=next(f['points'] for f in features if f['tags'].get('water')=='river')
pts=[((lon-121.49536)*111320*math.cos(math.radians(31.24188)),(lat-31.24188)*110900) for lon,lat in river]
posts=0
for a,b in zip(pts[59:82],pts[60:83]):
 dx,dy=b[0]-a[0],b[1]-a[1];dist=math.hypot(dx,dy)
 if dist<4:continue
 # Offset toward the mapped land, avoiding placement in the river.
 nx,ny=-dy/dist,dx/dist
 for h in [1.35,1.55,1.75,1.95,2.15]:line('滨江栏杆水平扶手',[(a[0]+nx,a[1]+ny,h),(b[0]+nx,b[1]+ny,h)],.028 if h<2 else .045,metal)
 n=max(1,round(dist/2.0))
 for i in range(n+1):
  x=a[0]+dx*i/n+nx;y=a[1]+dy*i/n+ny
  cyl('滨江栏杆立柱',(x,y,.92),(x,y,2.17),.045,metal,n=10)
  box('滨江栏杆柱脚',(x,y,.98),(.16,.16,.06),metal);posts+=1
# Layered glass below the open steel pinnacle, rather than a fully empty 54m cage.
collection('16B 金茂塔冠玻璃与百叶')
cx,cy=576.74,-513.44;glass=bpy.data.materials['金茂灰玻璃']
for z,r,zn,rn in [(353,11.4,361,10.6),(361,10.6,369,8.8),(369,8.8,378,7.2),(378,7.2,387,5.4)]:
 vs=[(cx+rr*math.cos(math.pi/8+i*math.tau/8),cy+rr*math.sin(math.pi/8+i*math.tau/8),zz) for zz,rr in [(z,r),(zn,rn)] for i in range(8)]
 mesh('金茂冠部内退玻璃',vs,[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)],glass)
s=bpy.context.scene;s['riverfront_detail_note']='Railing follows OSM bank, post spacing and section sizes photo-estimated; not survey-grade.'
data=bpy.data.cameras.new('滨江材质检查');cam=bpy.data.objects.new('滨江材质检查',data);s.collection.objects.link(cam);cam.location=(-422,-60,8);cam.rotation_euler=(Vector((-342,1,30))-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=28;data.clip_end=30000
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.camera=cam;s.render.filepath=str(ROOT/'预览/滨江材质近景.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
print('RIVERFRONT_SAVED',posts,flush=True)
