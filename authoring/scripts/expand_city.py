"""Expand saved detailed scene; maintain one production .blend in Documents/Blender.
Hero buildings use sourced total heights and georeferenced footprints.
Surface shape is a reference-led approximation, not as-built survey data.
"""
import bpy,ast,math,json,bmesh,re
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1]
DEST=Path('C:/Users/27035/OneDrive/文档/Blender/上海陆家嘴');DEST.mkdir(parents=True,exist_ok=True)
PRE=DEST/'预览';PRE.mkdir(exist_ok=True)
bpy.context.preferences.view.language='en_US';bpy.context.preferences.view.use_translate_new_dataname=False
for file,names in [('build_pearl.py',{'collection','put','material','mesh','instance','box','cyl','sphere','line','ring','polygon','extrude','xy','points','center','near','inside'}),('upgrade_v02.py',{'clean','signed','shell','facade','crown_height'})]:
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),file,'exec'))
cache={};COL=None;LON=121.49536;LAT=31.24188
features=json.loads((R/'reference/map_expanded.json').read_text(encoding='utf-8'));byid={f['id']:f for f in features}
trim=material('城市金属细框',(.26,.31,.34),.65,.28);glass=material('超高层蓝灰幕墙',(.028,.068,.10),.56,.19)
silver=material('金茂银灰结构',(.32,.34,.32),.62,.33);jglass=material('金茂灰玻璃',(.043,.064,.065),.48,.22)
limestone=bpy.data.materials['v02 米白石材'];roofmat=bpy.data.materials['v02 深灰屋面'];blueglass=glass
def closed(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
def metadata(o,ident,h,source):
 o['osm_id']=ident;o['height_m']=h;o['height_source']=source;o['geometry_accuracy']='Map footprint; facade and crown approximate from references';o['asset_role']='landmark_LOD0'
def bboxcentre(ident):
 p=clean(points(byid[ident]));return ((min(x for x,y in p)+max(x for x,y in p))/2,(min(y for x,y in p)+max(y for x,y in p))/2)

collection('10 上海中心 · 632m 扭转双层轮廓')
cx,cy=bboxcentre('165792123');NS=96;NZ=128
def st(a,t,offset=0):
 # Rounded triangular plan; sourced 120-degree twist and 55% top scale.
 rad=(46.5*(1+.105*math.cos(3*a)))*(1-.45*t)+offset;angle=a+math.radians(120)*t+.25
 z=632*t
 if t>.95:z-=13*((t-.95)/.05)*(.5-.5*math.cos(a+.6))
 return (cx+rad*math.cos(angle),cy+rad*math.sin(angle),z)
vs=[st(i*math.tau/NS,j/NZ) for j in range(NZ+1) for i in range(NS)];fs=[]
for j in range(NZ):
 for i in range(NS):k=j*NS+i;ni=j*NS+(i+1)%NS;fs.append((k,ni,ni+NS,k+NS))
o=mesh('上海中心632m扭转幕墙',vs,fs,glass);metadata(o,'165792123',632,'https://www.shanghaitower.com/office.html')
for f in o.data.polygons:f.use_smooth=True
for j in range(1,127):line('上海中心水平窗框',[st(i*math.tau/NS,j/128,.08) for i in range(NS)],.10,trim,True)
for i in range(NS):line('上海中心扭转竖框',[st(i*math.tau/NS,j/NZ,.09) for j in range(NZ+1)],.065,trim)
for i in [0,32,64]:line('上海中心三条转角脊线',[st(i*math.tau/NS,j/NZ,.20) for j in range(NZ+1)],.28,trim)
for z in [68,129,192,256,322,389,458,529,583]:
 line('上海中心空中大厅层间带',[st(i*math.tau/NS,z/632,.12) for i in range(NS)],.42,trim,True)
line('上海中心顶部冠沿',[st(i*math.tau/NS,1,.1) for i in range(NS)],.32,trim,True)
cyl('上海中心冠内屋面',(cx,cy,602),(cx,cy,603),21,roofmat,n=64)
extrude('上海中心底座',clean(points(byid['165792123'])),.8,8,glass)

collection('11 环球金融中心 · 492m 实体贯通开口')
cx,cy=bboxcentre('10691100');angle=math.atan2(5.3,59.9)
def wf(x,y,z):return (cx+x*math.cos(angle)-y*math.sin(angle),cy+x*math.sin(angle)+y*math.cos(angle),z)
def wh(z):return (30-3*z/492,30-23*(z/492)**1.1)
vs=[];fs=[]
for j in range(103):
 z=492*j/102;w,d=wh(z)
 for x,y in [(-w,-d),(w,-d),(w,d),(-w,d)]:vs.append(wf(x,y,z))
for j in range(102):
 for i in range(4):k=j*4+i;ni=j*4+(i+1)%4;fs.append((k,ni,ni+4,k+4))
fs.extend([(3,2,1,0),(408,409,410,411)])
o=mesh('环球金融中心492m主体',vs,fs,glass);closed(o)
# Explicit trapezoid through the entire depth, opening larger at its top.
cv=[wf(x,y,z) for y in [-50,50] for x,z in [(-13,440),(13,440),(20,479),(-20,479)]]
cut=mesh('临时环球开口',cv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],glass);closed(cut)
bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('顶部真实贯通梯形','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
metadata(o,'10691100',492,'https://www.swfc-shanghai.com/up_pdf/1321340644_23490.pdf')
for j in range(1,102):
 z=492*j/102;w,d=wh(z)
 for sign in [-1,1]:
  intervals=[(-w,w)] if not 440<z<479 else [(-w,-13-(z-440)*7/39),(13+(z-440)*7/39,w)]
  for l,r in intervals:line('环球正面水平窗框',[wf(l,sign*(d+.10),z),wf(r,sign*(d+.10),z)],.1,trim)
  line('环球侧面水平窗框',[wf(sign*(w+.1),-d,z),wf(sign*(w+.1),d,z)],.1,trim)
for k in range(33):
 u=-1+2*k/32
 for sign in [-1,1]:
  chain=[]
  for j in range(205):
   z=492*j/204;w,d=wh(z);x=u*w;skip=440<z<479 and abs(x)<13+(z-440)*7/39
   if skip:
    if len(chain)>1:line('环球竖向幕墙框',chain,.055,trim)
    chain=[]
   else:chain.append(wf(x,sign*(d+.1),z))
  if len(chain)>1:line('环球竖向幕墙框',chain,.055,trim)
for sx in [-1,1]:
 for sy in [-1,1]:line('环球四角脊线',[wf(sx*wh(j*492/102)[0],sy*wh(j*492/102)[1],j*492/102) for j in range(103)],.30,trim)
for sign in [-1,1]:line('环球梯形开口金属包边',[wf(x,sign*(wh(z)[1]+.13),z) for x,z in [(-13,440),(13,440),(20,479),(-20,479),(-13,440)]],.32,trim)

collection('12 金茂大厦 · 420.5m 八角退台')
cx,cy=bboxcentre('376075961')
def octagon(rad):return [(cx+rad*math.cos(math.pi/8+i*math.tau/8),cy+rad*math.sin(math.pi/8+i*math.tau/8)) for i in range(8)]
weights=[16,14,12,10,8,7,6,5,4,3,2,1];z=8
for i,weight in enumerate(weights):
 top=z+weight/sum(weights)*345;rad=39*(.9**i)
 pp=octagon(rad);ob=extrude('金茂第'+str(i+1)+'退台',pp,z,top,jglass);metadata(ob,'376075961',420.5,'https://www.chinajinmao.cn/Portals/69/his/pdf/en-gsgg/2011/LTN20110330883.pdf')
 facade('金茂银色立面',pp,z,[top]*8,'glass',3.9)
 for zz in [top-1.2,top-.5,top+.1]:line('金茂退台挑檐',[(x,y,zz) for x,y in octagon(rad+.6)],.23,silver,True)
 for x,y in pp:cyl('金茂竖向结构肋',(x,y,z),(x,y,top),.34,silver,n=8)
 z=top
for i,(zz,rr) in enumerate([(353,11),(365,9),(377,6.6),(387,4.5),(397,2.6)]):
 cyl('金茂层叠冠部',(cx,cy,zz),(cx,cy,zz+10),rr,silver,r2=rr*.75,n=8)
 ring('金茂冠部横梁',cx,cy,zz,rr+.5,.19,silver)
cyl('金茂420.5m尖塔',(cx,cy,407),(cx,cy,420.5),1.3,silver,r2=0,n=12)
extrude('金茂底座',clean(points(byid['376075961'])),.8,8,silver)

# Expand contextual buildings using mapped parts, preserving already detailed core.
collection('13 扩展楼群 · OSM实体位置')
existing={o.get('osm_id') for o in bpy.data.objects if o.get('osm_id')};heroes=[bboxcentre(i) for i in ['165792123','10691100','376075961']]
parts=[f for f in features if f['tags'].get('building:part')];added=[]
for f in features:
 t=f['tags'];pp=clean(points(f)) if len(f['points'])>2 else []
 if not pp or not (t.get('building') or t.get('building:part')) or f['id'] in existing:continue
 cc=center(pp)
 if math.hypot(*cc)<650 or math.hypot(*cc)>1450:continue
 if any(math.dist(cc,h)<68 for h in heroes):continue
 def numeric(value,default):
  m=re.search(r'[-+]?\d+(?:\.\d+)?',str(value));return float(m.group()) if m else default
 h=numeric(t.get('height'),numeric(t.get('building:levels'),3)*3.6);base=numeric(t.get('min_height'),.8)
 basis='OSM height' if 'height' in t else 'floor count conversion estimated' if 'building:levels' in t else 'unknown: provisional 10.8m'
 if str(t.get('height','')).startswith('<'):basis='OSM upper bound, provisional massing rather than measured height'
 if t.get('building') and any(p['id']!=f['id'] and inside(center(points(p)),pp) for p in parts):h=min(h,16);basis='parent podium; parts represented separately'
 if h<base+.2:continue
 hh=crown_height(f,h);name=t.get('name',t.get('name:en','地图建筑 '+f['id']))
 ob=shell(name,pp,base,hh,glass if h>40 else limestone);ob['osm_id']=f['id'];ob['height_m']=h;ob['height_basis']=basis;ob['asset_role']='context_LOD1'
 facade(name,pp,base,hh,'glass',4)
 added.append(dict(id=f['id'],name=name,height=h,basis=basis))
# Properly joined roads fix old coplanar overlapping segment artifacts.
collection('14 道路连续网格 · 扩展范围')
for o in list(bpy.data.objects):
 if o.name.endswith(' · OSM道路'):bpy.data.objects.remove(o,do_unlink=True)
for g in json.loads((R/'reference/expanded_roads_mesh.json').read_text()):
 vs=[];fs=[]
 for tri in g['triangles']:
  k=len(vs);vs.extend([(x,y,g['z']) for x,y in tri]);fs.append((k,k+1,k+2))
 mesh('连续路网 '+g['name'],vs,fs,bpy.data.materials['滨江浅灰石材' if g['name'].startswith('walk') else '道路沥青'])
for f in features:
 t=f['tags'];pp=points(f)
 if len(pp)>3 and 650<math.hypot(*center(pp))<1450 and (t.get('landuse')=='grass' or t.get('leisure') in ['garden','park']):polygon('扩展地图绿地 '+f['id'],pp,.35,bpy.data.materials['v02 草地'])

# Correct previous inspection camera/sign occlusion without altering neighbouring building positions.
for o in bpy.data.objects:
 if o.name.startswith('中国平安 · 建筑原有标识'):
  normal=o.rotation_euler.to_matrix()@Vector((0,0,1));o.location+=normal*1.0
o=bpy.data.objects.get('v04 平安建筑校核');o.location=(5,210,180);o.rotation_euler=(Vector((250,-38,108))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=32
collection('15 自由漫游相机 · 米制坐标')
def cam(name,loc,target,lens):
 c=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,c);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.lens=lens;c.clip_start=.15;c.clip_end=30000;return o
overview=cam('陆家嘴全景',(-1150,740,980),(340,-350,235),40)
trio=cam('三座超高层建筑',(-120,-1150,540),(625,-607,275),42)
street=cam('地面漫游起点',(-182,-147,2.1),(5,-2,160),24)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s['project_goal']='Website free-roaming real Shanghai scene. Blender source; later GLB tiles, LOD, baked PBR, collision, character and traffic.'
s['main_file']=str(DEST/'上海陆家嘴.blend');s['next_work']='Read 项目说明.md beside blend; do not rebuild from older numbered scenes.'
s.camera=overview;s.render.engine='CYCLES';s.cycles.samples=80;s.cycles.use_denoising=True;s.cycles.device='GPU'
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
sun=bpy.data.objects.get('白天太阳');sun.hide_render=True
s.render.resolution_x=1920;s.render.resolution_y=1280;s.render.resolution_percentage=100
path=DEST/'上海陆家嘴.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path));print('MAIN_SCENE_SAVED',len(added),flush=True)
(DEST/'扩展建筑依据.json').write_text(json.dumps(added,ensure_ascii=False,indent=2),encoding='utf-8')
for camera,file in [(overview,'陆家嘴全景.png'),(trio,'三座超高层.png')]:
 s.camera=camera;s.render.filepath=str(PRE/file);bpy.ops.render.render(write_still=True)
s.camera=overview;s.render.engine='BLENDER_EEVEE';sun.hide_render=False
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.clip_end=30000;a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('CITY_DONE',len(s.objects),flush=True)
