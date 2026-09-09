"""v03 -> v04. Rebuild Ping An building from referenced stone supplier photographs.
Retain previous scenes. Heights sourced; articulation remains photograph-derived.
"""
import bpy,ast,math,json,random,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];OUT=R/'output'
assert Path(bpy.data.filepath).name=='东方明珠_实景细化_v03.blend'
bpy.context.preferences.view.language='en_US';bpy.context.preferences.view.use_translate_new_dataname=False
for file,names in [('build_pearl.py',{'collection','put','material','mesh','instance','box','cyl','sphere','line','ring','polygon','extrude','xy','points','center','near','inside'}),('upgrade_v02.py',{'clean','signed','shell','facade'})]:
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),file,'exec'))
cache={};COL=None;LON=121.49536;LAT=31.24188
features=json.loads((R/'reference/map_features.json').read_text(encoding='utf-8'));byid={f['id']:f for f in features}
stone=material('v04 平安玫瑰白麻石',(.48,.43,.34),.03,.65)
darkglass=material('v04 平安深色窗',(.018,.035,.039),.38,.22)
copper=material('v04 穹顶深灰铜板',(.022,.041,.043),.6,.32)
trim=bpy.data.materials['v02 铝合金幕墙框'];limestone=stone;roofmat=bpy.data.materials['v02 深灰屋面']
targetids={'520990201','164958064','165170316'}
oldnames=[]
for o in list(bpy.data.objects):
 if o.get('osm_id') in targetids:oldnames.append(o.name)
for o in list(bpy.data.objects):
 if any(o.name==n or o.name.startswith(n+' ·') for n in oldnames):bpy.data.objects.remove(o,do_unlink=True)
# Generic dome ribs and rooftop devices of the previous tower had no ID; spatial selection is bounded.
for o in list(bpy.data.objects):
 if o.name.startswith(('穹顶金属肋','屋顶设备 · 示意')):
  if o.type=='CURVE':v=o.data.splines[0].points[0].co;xx,yy=v.x,v.y
  else:xx,yy=o.location.x,o.location.y
  if 222<xx<279 and -68<yy<0:bpy.data.objects.remove(o,do_unlink=True)
collection('04P 平安金融大厦 v04 · 石材柱廊与203m穹顶')
pts=clean(points(byid['164958064']));cx=(min(p[0] for p in pts)+max(p[0] for p in pts))/2;cy=(min(p[1] for p in pts)+max(p[1] for p in pts))/2
def contracted(poly,amount):
 c=Vector(center(poly));return [tuple(c+(Vector(p)-c)*amount) for p in poly]
def classical_facade(name,pts,z0,z1,spacing=3.4,floor=4.2):
 sg=signed(pts);vs=[];fs=[]
 def quad(v):k=len(vs);vs.extend(v);fs.append(tuple(range(k,k+4)))
 for a,b in zip(pts,pts[1:]+pts[:1]):
  a=Vector(a);b=Vector(b);u=(b-a).normalized();n=Vector((u.y,-u.x))*sg;length=(b-a).length
  def p(d,z,off=.15):q=a+u*d+n*off;return (q.x,q.y,z)
  count=max(1,round(length/spacing))
  for i in range(count+1):
   ss=i*length/count;w=.23 if i not in [0,count] else .62
   quad([p(max(0,ss-w),z0),p(min(length,ss+w),z0),p(min(length,ss+w),z1),p(max(0,ss-w),z1)])
  z=z0
  while z<z1:
   quad([p(0,z),p(length,z),p(length,min(z+.43,z1)),p(0,min(z+.43,z1))]);z+=floor
  for zz in [z0+.3,z1-.5,z1]:line(name+'石材檐口',[p(0,zz,.32),p(length,zz,.32)],.22,stone)
 ob=mesh(name+'厚石材窗间墙',vs,fs,stone);return ob
for z0,z1,scale in [(30,124,1),(124,155,.95),(155,170,.86)]:
 pp=contracted(pts,scale);o=extrude('平安主楼 '+str(z1)+'m',pp,z0,z1,darkglass);o['osm_id']='164958064';o['height_source']='https://www.kanglistone.com/index.php/Case/show/id/41.html';classical_facade('平安主楼',pp,z0,z1)
# Broad middle vertical stone pier seen in photos.
sg=signed(pts)
for a,b in zip(pts,pts[1:]+pts[:1]):
 u=(Vector(b)-Vector(a)).normalized();n=Vector((u.y,-u.x))*sg;mid=(Vector(a)+Vector(b))/2
 if math.dist(a,b)>55:
  pp=[tuple(mid-u*1.4),tuple(mid+u*1.4),tuple(mid+u*1.4+n*.8),tuple(mid-u*1.4+n*.8)]
  extrude('平安贯通竖向石脊',pp,30,169,stone)
# Podium follows the saved mapped outer outline, no random replacement footprint.
pod=clean(points(byid['520990201']));o=extrude('平安裙房玻璃实体',pod,.9,28,darkglass);o['osm_id']='520990201';o['height_basis']='28m podium photo-estimated'
sg=signed(pod)
for a,b in zip(pod,pod[1:]+pod[:1]):
 u=(Vector(b)-Vector(a)).normalized();n=Vector((u.y,-u.x))*sg;ln=math.dist(a,b)
 if ln<10:continue
 for k in range(max(2,round(ln/5))+1):
  ss=ln*k/max(2,round(ln/5));q=Vector(a)+u*ss+n*.8
  cyl('平安裙房高石柱',(*q,1.3),(*q,24),.64,stone,n=16)
  cyl('平安柱头',(*q,23.8),(*q,24.5),.86,stone,n=16)
 for zz,rr in [(1.4,.3),(24.8,.4),(26.5,.45),(28,.4)]:
  line('平安裙房檐口',[(a[0]+n.x*.5,a[1]+n.y*.5,zz),(b[0]+n.x*.5,b[1]+n.y*.5,zz)],rr,stone)
# Drum, copper dome, ribs, lantern; maximum geometry reaches precisely 203m.
cx=251.3;cy=-38.4;rad=19
cyl('平安穹顶基座',(cx,cy,170),(cx,cy,180),rad,darkglass,n=96)
for k in range(32):
 a=k*math.tau/32;x=cx+(rad+.15)*math.cos(a);y=cy+(rad+.15)*math.sin(a)
 cyl('穹顶鼓座壁柱',(x,y,170),(x,y,180),.25,stone,n=8)
for z in [170,172,179.5,180]:ring('穹顶鼓座厚檐',cx,cy,z,rad+.45,.25,stone)
vs=[];fs=[]
for j in range(25):
 lat=j*math.pi/48
 for k in range(96):
  a=k*math.tau/96;vs.append((cx+rad*math.cos(lat)*math.cos(a),cy+rad*math.cos(lat)*math.sin(a),180+20*math.sin(lat)))
for j in range(24):
 for k in range(96):i=j*96+k;ni=j*96+(k+1)%96;fs.append((i,ni,ni+96,i+96))
o=mesh('平安巴洛克穹顶',vs,fs,copper);o['top_height_basis']='dome ensemble 203m from stone supplier; main body170m';o['osm_id']='165170316'
for face in o.data.polygons:face.use_smooth=True
for k in range(48):
 a=k*math.tau/48;line('平安穹顶金属肋',[(cx+(rad+.06)*math.cos(j*math.pi/48)*math.cos(a),cy+(rad+.06)*math.cos(j*math.pi/48)*math.sin(a),180+20.06*math.sin(j*math.pi/48)) for j in range(25)],.065,trim)
for j in range(1,16):
 lat=j*math.pi/36;ring('平安铜板横接缝',cx,cy,180+20*math.sin(lat),rad*math.cos(lat)+.025,.025,trim)
cyl('平安穹顶灯亭',(cx,cy,199.6),(cx,cy,201.8),1.4,copper,n=24)
cyl('平安顶部尖端203m',(cx,cy,201.8),(cx,cy,203),.6,copper,r2=0,n=24)
orange=material('v04 平安标识橙色',(.8,.16,.013),.12,.4)
fontpath=Path('C:/Windows/Fonts/msyh.ttc');font=bpy.data.fonts.load(str(fontpath)) if fontpath.exists() else None
pp=contracted(pts,.87);sg=signed(pp)
for a,b in zip(pp,pp[1:]+pp[:1]):
 if math.dist(a,b)<35:continue
 u=(Vector(b)-Vector(a)).normalized();n=Vector((u.y,-u.x))*sg;q=(Vector(a)+Vector(b))/2+n*.45
 c=bpy.data.curves.new('中国平安标识','FONT');c.body='中国平安';c.size=3.6;c.align_x='CENTER';c.extrude=.045
 if font:c.font=font
 ob=bpy.data.objects.new('中国平安 · 建筑原有标识',c);COL.objects.link(ob);ob.location=(q.x,q.y,158.5);ob.rotation_euler=(math.pi/2,0,math.atan2(u.y,u.x));c.materials.append(orange)

# Fix v03 visual QA issues: roof cannot use facade glass; back wall needs fenestration.
collection('05E 会议中心 v04 · 屋面与背面窗')
o=bpy.data.objects.get('会议中心 · 滨江低层翼楼');o.data.materials.append(roofmat)
for face in o.data.polygons:
 if len(face.vertices)==3:face.material_index=len(o.data.materials)-1
# Front camera moved into unobstructed forecourt, without hiding any neighbouring tower.
cam=bpy.data.objects['v03 会议中心东立面'];cam.location=(-198,-165,30);cam.rotation_euler=(Vector((-270,-58,23))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25

# Denser foliage and coherent branches, still instanced to fit 8GB graphics memory.
collection('06D v04 乔木树枝与密叶')
leafmats=[bpy.data.materials['v03 叶片 '+str(i)] for i in range(4)];bark=bpy.data.materials['v03 树皮']
def newtree(seed):
 rng=random.Random(seed);verts=[];faces=[];mi=[]
 def branch(a,b,r):
  a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u);k=len(verts)
  for pos,rr in [(a,r),(b,r*.4)]:
   for j in range(6):verts.append(pos+(u*math.cos(j*math.tau/6)+v*math.sin(j*math.tau/6))*rr)
  for j in range(6):faces.append((k+j,k+(j+1)%6,k+(j+1)%6+6,k+j+6));mi.append(4)
 branch((0,0,-1.05),(0,0,.45),.055)
 centres=[]
 for j in range(14):
  a=j*2.4;z=-.45+j*.08;end=Vector((.70*math.cos(a),.70*math.sin(a),z+.3));branch((0,0,z-.15),end,.024);centres.append(end)
  for k in range(3):
   tip=end+Vector((rng.uniform(-.18,.18),rng.uniform(-.18,.18),rng.uniform(.1,.3)));branch(end*.7,tip,.008)
 for j in range(6500):
  c=centres[j%len(centres)];az=rng.random()*math.tau;zz=rng.uniform(-1,1);rr=math.sqrt(1-zz*zz)*rng.random()**.333
  cc=c*.8+Vector((rr*math.cos(az)*.46,rr*math.sin(az)*.46,zz*.42));a=rng.random()*math.tau
  u=Vector((math.cos(a),math.sin(a),rng.uniform(-.5,.5)))*rng.uniform(.035,.07);v=Vector((-math.sin(a),math.cos(a),rng.uniform(-.5,.5)))*rng.uniform(.02,.036)
  k=len(verts);verts.extend([cc-u,cc+v,cc+u,cc-v]);faces.append((k,k+1,k+2,k+3));mi.append(rng.randrange(4))
 me=bpy.data.meshes.new('v04 实例树枝叶'+str(seed));me.from_pydata(verts,[],faces);me.update()
 for mat in leafmats+[bark]:me.materials.append(mat)
 for f,i in zip(me.polygons,mi):f.material_index=i
 return me
trees=[newtree(i+404) for i in range(6)]
for i,o in enumerate([o for o in bpy.data.objects if o.name.startswith('树冠')]):o.data=trees[i%6]

s=bpy.context.scene;s['status']='v04 Ping An height and stone architecture corrected; foliage improved; no AI-rendered textures.'
path=OUT/'东方明珠_实景细化_v04.blend';s.render.engine='CYCLES';s.cycles.samples=96;s.cycles.use_denoising=True;s.cycles.device='GPU'
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
sun=bpy.data.objects.get('白天太阳');sun.hide_render=True
c=bpy.data.cameras.new('v04 平安建筑校核');co=bpy.data.objects.new('v04 平安建筑校核',c);COL.objects.link(co);co.location=(70,145,175);co.rotation_euler=(Vector((250,-38,100))-co.location).to_track_quat('-Z','Y').to_euler();c.lens=33;c.clip_end=20000
s.camera=co;bpy.ops.wm.save_as_mainfile(filepath=str(path));print('V04_CHECKPOINT_SAVED',flush=True)
for cam,file in [(co,'v04_pingan.png'),(bpy.data.objects['v03 会议中心东立面'],'v04_convention.png'),(bpy.data.objects['v03 滨江建筑细节'],'v04_river.png')]:
 s.camera=cam;s.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['v03 滨江建筑细节'];s.render.engine='BLENDER_EEVEE';sun.hide_render=False
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path));print('V04_DONE',flush=True)
