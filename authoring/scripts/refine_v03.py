"""Load saved v02 ONLY; refine identified buildings and vegetation, save v03.
No global preferences saved. All new source-dependent estimates remain labelled.
"""
import bpy,ast,math,json,random
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];OUT=R/'output'
assert Path(bpy.data.filepath).name=='东方明珠_周边建筑_白天_v02.blend'
bpy.context.preferences.view.language='en_US';bpy.context.preferences.view.use_translate_new_dataname=False
for file,names in [('build_pearl.py',{'collection','put','material','mesh','instance','box','cyl','sphere','line','ring','polygon','extrude','xy','points','center','near','inside'}),('upgrade_v02.py',{'clean','signed','shell','facade'})]:
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8'))
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),file,'exec'))
cache={};COL=None;LON=121.49536;LAT=31.24188;random.seed(303)
features=json.loads((R/'reference/map_features.json').read_text(encoding='utf-8'));byid={f['id']:f for f in features}
trim=bpy.data.materials['v02 铝合金幕墙框'];limestone=bpy.data.materials['v02 米白石材'];roofmat=bpy.data.materials['v02 深灰屋面'];granite=bpy.data.materials['v02 白麻花岗岩']
glass=material('v03 会议中心深蓝绿玻璃',(.028,.075,.078),.46,.19)
glass2=material('v03 球厅反射玻璃',(.045,.12,.14),.65,.16)
for name in ['v02 中性蓝灰幕墙','v02 绿灰幕墙']:
 m=bpy.data.materials[name];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(.045,.09,.115,1);p.inputs['Metallic'].default_value=.48;p.inputs['Roughness'].default_value=.2
stone=material('v03 会议中心浅米石',(.48,.46,.41),.02,.63)
shadow=material('v03 窗框阴影',(.035,.04,.041),.3,.5)
for c in list(bpy.data.collections):
 if c.name.startswith('05A '):
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
collection('05A 国际会议中心 v03 · 设计院尺寸和实景柱廊')
f=byid['40778072'];pts=clean(points(f))
# The curved riverside hotel wing is lower than the 40m entrance hall.
ob=extrude('会议中心 · 滨江低层翼楼',pts,.9,22,glass);ob['osm_id']=f['id'];ob['height_basis']='22m lower wing estimated from photograph; main hall separately 40m'
facade('滨江翼楼',pts,.9,[22]*len(pts),'glass',3.65)
for z in [1.3,4.2,7.8,11.4,15,18.6,22]:line('滨江翼楼石材水平檐',[(x,y,z) for x,y in pts],.32,stone,True)
# Long straight east entrance facade, observed in front photograph.
A=Vector((-315.1,-106.3));B=Vector((-195.5,-36.5));U=(B-A).normalized();N=Vector((U.y,-U.x));length=(B-A).length
def p(s,d,z):
 q=A+U*s+N*d;return (q.x,q.y,z)
def slab(name,s0,s1,d0,d1,z0,z1,mat):
 pp=[p(s0,d0,0)[:2],p(s1,d0,0)[:2],p(s1,d1,0)[:2],p(s0,d1,0)[:2]]
 return extrude(name,pp,z0,z1,mat)
body=slab('会议中心主厅 · 40m',0,length,-22,0,.9,40,stone);body['verified_height_m']=40;body['height_source']='https://www.ziad.cn/product/13.html'
# Actual separate glass surface, tall columns and arches; detail dimensions photo-estimated.
slab('主厅玻璃幕墙',9,length-10,-.18,.06,3,35,glass)
for z in [6.1,8.7,11.3,13.9,16.5,19.1,21.7,24.3,26.9,29.5,32.1,34.7]:line('主厅细横框',[p(9,.17,z),p(length-10,.17,z)],.055,trim)
for i in range(54):
 ss=9+(length-19)*i/53;line('主厅细竖框',[p(ss,.17,3),p(ss,.17,35)],.07,trim)
bay=(length-23)/12
for i in range(13):
 ss=11.5+i*bay
 cyl('主厅石柱',p(ss,1.1,8),p(ss,1.1,33.8),.65,stone,r2=.52,n=20)
 for z,rad,h in [(7.9,.94,.65),(8.5,.77,.35),(33.5,.82,.45),(34,1.1,.65)]:cyl('石柱柱础和柱冠',p(ss,1.1,z),p(ss,1.1,z+h),rad,stone,n=16)
 # Stylized solid volutes at capital, restrained instead of texture-painted ornament.
 for side in [-1,1]:sphere('柱冠卷叶',p(ss+side*.64,1.14,34.1),.35,stone,12,8)
 if i<12:
  mid=ss+bay/2;rr=(bay-1.7)/2
  line('拱窗半圆', [p(mid+rr*math.cos(k*math.pi/32),.30,17+rr*math.sin(k*math.pi/32)) for k in range(33)],.10,trim)
  for side in [-1,1]:line('拱窗侧框',[p(mid+side*rr,.30,9),p(mid+side*rr,.30,17)],.10,trim)
  line('窗台阳台',[p(ss+1,.55,23),p(ss+bay-1,.55,23)],.1,trim)
  for k in range(9):
   u=ss+1+(bay-2)*k/8;line('窗台栏杆',[p(u,.55,22),p(u,.55,23)],.035,trim)
for z,w in [(35,.36),(36,.48),(38,.24),(39.7,.4)]:line('主厅厚檐口',[p(7,.65,z),p(length-7,.65,z)],w,stone)
slab('入口长玻璃雨棚',7,length-7,.1,5.8,7.35,7.55,glass2)
for i in range(27):
 ss=7+(length-14)*i/26;line('雨棚钢肋',[p(ss,.1,7.4),p(ss,5.8,7.4)],.095,trim)
for i in range(13):
 ss=11.5+i*bay;slab('入口门柱',ss-.6,ss+.6,-.1,.5,.9,7.3,stone)
for z in [1,1.2,1.4,1.6]:slab('入口台阶',8,length-8,1,6-(z-1)*5,z-.2,z,stone)
# OSM centres retained, design institute diameters take precedence over imperfect circles.
for ident,rad,zc in [('164972685',25,26),('164972678',19,24)]:
 pp=clean(points(byid[ident]));cx=(min(x for x,y in pp)+max(x for x,y in pp))/2;cy=(min(y for x,y in pp)+max(y for x,y in pp))/2
 # Lower ring glazed lobby with freestanding pillars.
 cyl('球厅玻璃圆厅 '+ident,(cx,cy,.9),(cx,cy,16),rad*.93,glass,n=96)
 for z in [1.1,8.5,11.5,15.5]:
  cyl('球厅环形楼板',(cx,cy,z),(cx,cy,z+.55),rad*1.03,stone,n=96)
 for k in range(48):
  a=k*math.tau/48;xx=cx+rad*.935*math.cos(a);yy=cy+rad*.935*math.sin(a)
  line('圆厅竖框',[(xx,yy,1.4),(xx,yy,16)],.065,trim)
 for k in range(16):
  a=k*math.tau/16;xx=cx+rad*1.005*math.cos(a);yy=cy+rad*1.005*math.sin(a)
  cyl('球厅底层外柱',(xx,yy,1),(xx,yy,8.5),.38,stone,n=16)
 # Sphere intersects the upper lobby, as in exterior photo; true diameter stored for inspection.
 sp=sphere('会议中心玻璃球 '+ident,(cx,cy,zc),rad,glass2,96,48);sp['verified_diameter_m']=rad*2;sp['vertical_center_basis']='photograph estimate, large overall top ~51m';sp['diameter_source']='https://www.ziad.cn/product/13.html'
 for j in range(-7,12):
  lat=j*math.pi/24;rr=rad*math.cos(lat);zz=zc+rad*math.sin(lat)
  if zz>16:ring('球厅细纬线',cx,cy,zz,rr+.045,.065,trim)
 for k in range(64):
  a=k*math.tau/64;la=max(-math.pi/2,math.asin((16-zc)/rad))
  line('球厅细经线',[(cx+(rad+.04)*math.cos(la+(math.pi/2-la)*j/48)*math.cos(a),cy+(rad+.04)*math.cos(la+(math.pi/2-la)*j/48)*math.sin(a),zc+(rad+.04)*math.sin(la+(math.pi/2-la)*j/48)) for j in range(49)],.055,trim)
 # Horizontal sunshades around lower glazing, visible from river.
 for z in [9.2,12.1,15.7]:ring('圆厅挑檐',cx,cy,z,rad*1.035,.14,stone)

# Museum: actual recessed glass rooms and roof sawtooth skylights, replacing stuck-on glass.
collection('05B 美术馆 v03 · 镜厅凹进与天窗')
museum=bpy.data.objects.get('浦东美术馆 · 30m主体')
for o in list(bpy.data.objects):
 if o.name.startswith(('镜厅 ·','镜厅竖框','屋顶天窗','美术馆屋顶设备核')):bpy.data.objects.remove(o,do_unlink=True)
# Make extruded museum closed and manifold before exact boolean cuts.
bmpts=clean(points(byid['803292747']))
import bmesh
bm=bmesh.new();bm.from_mesh(museum.data);edges=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=edges,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(museum.data);bm.free()
for z0,z1 in [(9,15),(17,29)]:
 cutter=box('临时镜厅切口',(-362,-181.5,(z0+z1)/2),(12,54,z1-z0),shadow)
 bpy.context.view_layer.objects.active=mutex=museum
 mod=museum.modifiers.new('实体镜厅凹进','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 box('镜厅后侧玻璃',(-356.7,-181.5,(z0+z1)/2),(.12,53.8,z1-z0-.2),glass2)
 box('镜厅地板',(-360.2,-181.5,z0+.1),(7,54,.2),granite)
 for yy in range(-207,-154,3):box('镜厅玻璃鳍',(-359,yy,(z0+z1)/2),(5.4,.06,z1-z0-.15),trim)
for i in range(6):
 xx=-320+i*6
 pp=[(xx,-187,30.1),(xx+4.7,-187,30.1),(xx+4.7,-175,30.1),(xx,-175,30.1)]
 # Sloped solid roof with vertical glass face, not arbitrary rooftop mechanical boxes.
 mesh('美术馆锯齿天窗',[(xx,-187,30.1),(xx+4.7,-187,30.1),(xx+4.7,-175,31),(xx,-175,31)],[(0,1,2,3)],granite)
 mesh('天窗竖向玻璃',[(xx,-175,30.1),(xx+4.7,-175,30.1),(xx+4.7,-175,31),(xx,-175,31)],[(0,1,2,3)],glass)
museum['detail']='Recessed west mirror halls 6m/12m, exact opening placement and roof skylight count photo approximation; no claim of as-built interior.'

# Vegetation: replace faceted balls with reusable branching broadleaf crown geometry.
collection('06C v03 乔木细节 · 实例化枝叶')
bark=material('v03 树皮',(.07,.047,.027),0,.95)
leafmats=[material('v03 叶片 '+str(i),c,0,.8) for i,c in enumerate([(.023,.069,.013),(.047,.115,.020),(.077,.145,.029),(.10,.17,.04)])]
for m in leafmats:
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Subsurface Weight'].default_value=.055
def crown_mesh(seed):
 rng=random.Random(seed);vs=[];fs=[];inds=[]
 # Geometry leaf sprays with open gaps, six shared meshes across all existing tree positions.
 for j in range(1800):
  az=rng.random()*math.tau;zz=rng.uniform(-.82,.85);rr=math.sqrt(max(0,1-zz*zz))*rng.uniform(.25,1)
  cc=Vector((rr*math.cos(az),rr*math.sin(az),zz));a=rng.random()*math.tau
  u=Vector((math.cos(a),math.sin(a),rng.uniform(-.4,.4)))*rng.uniform(.038,.075)
  vv=Vector((-math.sin(a),math.cos(a),rng.uniform(-.3,.3)))*rng.uniform(.018,.04)
  k=len(vs);vs.extend([cc-u,cc+vv,cc+u,cc-vv,cc+Vector((0,0,.011))]);fs.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)]);inds.extend([rng.randrange(4)]*4)
 me=bpy.data.meshes.new('乔木枝叶共享 '+str(seed));me.from_pydata(vs,[],fs);me.update()
 for m in leafmats:me.materials.append(m)
 for poly,mi in zip(me.polygons,inds):poly.material_index=mi
 return me
crowns=[crown_mesh(300+i) for i in range(6)]
treecount=0
for o in list(bpy.data.objects):
 if o.name.startswith('树冠'):
  o.data=crowns[treecount%6];o.rotation_euler.z=(treecount*.793)%math.tau;treecount+=1
 if o.name.startswith('树干'):
  # Shared material replacement only once is safe.
  o.data.materials.clear();o.data.materials.append(bark)

# Small-scale stone and asphalt texture in real metre-space; no painted false buildings.
for name,scale,strength,dist in [('道路沥青',7,.22,.035),('滨江浅灰石材',3,.16,.015),('v02 白麻花岗岩',45,.12,.012)]:
 m=bpy.data.materials[name];nt=m.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 coord=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
 nt.links.new(coord.outputs['Object'],noise.inputs['Vector']);b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=dist;nt.links.new(noise.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],p.inputs['Normal'])

s=bpy.context.scene;s['status']='v03 reference-led conference centre reconstruction, recessed museum halls, detailed foliage. Still incomplete architectural reconstruction.'
s['next_work']='PROJECT_STATE.md';s['v03_tree_crowns']=treecount
s.render.engine='CYCLES';s.cycles.samples=96;s.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for dev in pref.devices:dev.use=dev.type=='OPTIX'
s.cycles.device='GPU';s.view_settings.exposure=-.5
sun=bpy.data.objects.get('白天太阳');sun.hide_render=True
def camera(name,loc,target,lens):
 c=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,c);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.lens=lens;c.clip_end=20000;return o
front=camera('v03 会议中心东立面',(-105,-315,66),(-266,-60,22),45)
river=camera('v03 滨江建筑细节',(-650,185,170),(-245,-85,28),50)
s.camera=river;s.render.resolution_x=1700;s.render.resolution_y=1200
path=OUT/'东方明珠_实景细化_v03.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('V03_CHECKPOINT_SAVED',flush=True)
for cam,file in [(front,'v03_convention_front.png'),(river,'v03_river_detail.png'),(bpy.data.objects['01 滨江空中全景'],'v03_overview.png')]:
 s.camera=cam;s.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
s.camera=river;s.render.engine='BLENDER_EEVEE';sun.hide_render=False
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.clip_end=20000;a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('V03_DONE',len(s.objects),treecount,flush=True)
