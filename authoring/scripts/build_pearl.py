import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1]
OUT=R/'output'; OUT.mkdir(exist_ok=True)
random.seed(27)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name != 'Collection': bpy.data.collections.remove(c)
COL=None
def collection(name):
 global COL
 COL=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(COL)
 return COL
def put(obj,name,mat=None):
 obj.name=name
 for c in list(obj.users_collection): c.objects.unlink(obj)
 COL.objects.link(obj)
 if mat:obj.data.materials.append(mat)
 return obj
def material(name,color,metal=0,rough=.5,emit=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 return m
concrete=material('珍珠白 · 混凝土',(.48,.53,.59),.15,.38)
dark=material('深灰金属',(.023,.036,.057),.6,.32)
stone=material('滨江浅灰石材',(.18,.205,.23),.05,.55)
asphalt=material('道路沥青',(.017,.022,.032),.1,.7)
grass=material('滨江绿地',(.018,.047,.029),0,.95)
foliage=material('树冠',(.022,.065,.041),0,.9)
glass=material('蓝灰玻璃',(.026,.062,.092),.7,.24)
gold=material('暖白建筑轮廓',(.95,.58,.23),.15,.35,2.5)
cyan=material('东方明珠 · 冰蓝灯光',(.05,.42,1),.1,.35,3)
white=material('路灯 · 暖白',(.95,.81,.58),0,.4,7)
magenta=material('球面 · 紫红细灯',(.55,.085,.27),.15,.4,1.6)
panel=material('球面 · 紫灰玻璃',(.11,.035,.075),.65,.27)
window_mats=[material('窗灯 '+str(i),col,.1,.35,e) for i,(col,e) in enumerate([
 ((.82,.64,.37),1.4),((.58,.75,.9),1.15),((.9,.79,.6),2.2),((.14,.22,.3),.15)])]

def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);COL.objects.link(ob)
 if mat: me.materials.append(mat)
 return ob
cache={}
def instance(name,key,verts,faces,mat):
 if key not in cache:
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(mat);cache[key]=me
 o=bpy.data.objects.new(name,cache[key]);COL.objects.link(o);return o
def box(name,loc,scale,mat,bevel=0):
 v=[(x,y,z) for x,y,z in [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]]
 f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 o=instance(name,('box',mat.name),v,f,mat);o.location=loc;o.scale=scale;return o
def cyl(name,a,b,r,mat,r2=None,n=24):
 d=Vector(b)-Vector(a)
 r2=r if r2 is None else r2
 vs=[(rr*math.cos(i*math.tau/n),rr*math.sin(i*math.tau/n),z) for rr,z in [(r,-.5),(r2,.5)] for i in range(n)]
 fs=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))]
 o=instance(name,('cyl',r,r2,n,mat.name),vs,fs,mat);o.location=(Vector(a)+Vector(b))/2;o.scale.z=d.length;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
def sphere(name,loc,r,mat,segments=48,rings=24):
 key=('sphere',segments,rings,mat.name)
 vs=[];fs=[]
 if key not in cache:
  for j in range(rings+1):
   lat=-math.pi/2+math.pi*j/rings
   for i in range(segments):
    a=i*math.tau/segments;vs.append((math.cos(lat)*math.cos(a),math.cos(lat)*math.sin(a),math.sin(lat)))
  for j in range(rings):
   for i in range(segments):
    k=j*segments+i;ni=j*segments+(i+1)%segments;fs.append((k,ni,ni+segments,k+segments))
 o=instance(name,key,vs,fs,mat);o.location=loc;o.scale=(r,r,r)
 for p in o.data.polygons:p.use_smooth=True
 return o
def line(name,pts,r,mat,closed=False):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=1
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 sp.use_cyclic_u=closed
 ob=bpy.data.objects.new(name,cu);COL.objects.link(ob);cu.materials.append(mat);return ob
def ring(name,x,y,z,r,width,mat):
 return line(name,[(x+r*math.cos(i*math.tau/96),y+r*math.sin(i*math.tau/96),z) for i in range(96)],width,mat,True)
def polygon(name,pts,z,mat):
 if pts[0]==pts[-1]:pts=pts[:-1]
 vs=[Vector((x,y,z)) for x,y in pts]
 if len(vs)<3:return None
 tris=tessellate_polygon([vs]);idx={tuple(v):i for i,v in enumerate(vs)}
 return mesh(name,vs,[[v if isinstance(v,int) else idx[tuple(v)] for v in t] for t in tris],mat)
def extrude(name,pts,z,h,mat):
 if pts[0]==pts[-1]:pts=pts[:-1]
 n=len(pts);v=[(x,y,z) for x,y in pts]+[(x,y,h) for x,y in pts]
 faces=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 top=[Vector((x,y,h)) for x,y in pts];ix={tuple(v):i+n for i,v in enumerate(top)}
 faces.extend([[p+n if isinstance(p,int) else ix[tuple(p)] for p in t] for t in tessellate_polygon([top])])
 return mesh(name,v,faces,mat)
LON=121.49536;LAT=31.24188
def xy(p):return ((p[0]-LON)*111320*math.cos(math.radians(LAT)),(p[1]-LAT)*110900)
features=json.loads((R/'reference/map_features.json').read_text(encoding='utf-8'))
def points(f):return [xy(p) for p in f['points']]
def center(pts):return tuple(sum(v[i] for v in pts)/len(pts) for i in range(2))
def near(pts,r=760):
 x,y=center(pts);return math.hypot(x,y)<r
def inside(pt,poly):
 x,y=pt;c=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:c=not c
 return c

collection('01 地理底图 · OSM')
box('地面', (0,0,-2),(100000,100000,4),grass)
water=material('黄浦江 · 波纹反射',(.015,.033,.055),.65,.19)
n=water.node_tree.nodes;l=water.node_tree.links;p=n.get('Principled BSDF')
tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.7;tex.inputs['Detail'].default_value=3
coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(.35,1.5,1)
l.new(coord.outputs['Object'],mapping.inputs[0]);l.new(mapping.outputs['Vector'],tex.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27;bump.inputs['Distance'].default_value=.18
l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
river=[]
for f in features:
 if f['tags'].get('water')=='river':
  river=points(f);polygon('黄浦江 · 实际河岸',river,.25,water)
  # Bank lighting only inside local project boundary. Both banks remain georeferenced.
  seg=[]
  for pt in river:
   if abs(pt[0])<1700 and abs(pt[1])<1700:seg.append((*pt,.7))
   else:
    if len(seg)>1:line('河堤轮廓',seg,.7,stone)
    seg=[]
  if len(seg)>1:line('河堤轮廓',seg,.7,stone)

collection('02 道路 · 步道 · 滨江灯光')
roadpaths=[];treepts=[]
for f in features:
 t=f['tags'];pts=points(f)
 if not near(pts,1100):continue
 hw=t.get('highway')
 if hw not in ['primary','secondary','tertiary','residential','service','unclassified','pedestrian','footway','cycleway','steps']:continue
 if t.get('tunnel')=='yes' or t.get('location')=='underground':continue
 if len(pts)<2:continue
 ped=hw in ['pedestrian','footway','cycleway','steps']
 width=2.6 if ped else {'primary':10,'secondary':8,'tertiary':6,'service':3}.get(hw,5)
 z=7 if t.get('bridge')=='yes' else .7
 # Flat ribbons preserve local widths; round joins use low curb curves.
 vv=[];ff=[]
 for a,b in zip(pts,pts[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];dist=math.hypot(dx,dy)
  if dist<.1:continue
  nx=-dy/dist;ny=dx/dist;k=len(vv)
  vv.extend([(a[0]+nx*width,a[1]+ny*width,z),(a[0]-nx*width,a[1]-ny*width,z),(b[0]-nx*width,b[1]-ny*width,z),(b[0]+nx*width,b[1]+ny*width,z)])
  ff.append((k,k+1,k+2,k+3))
  if not ped:
   for s in range(4,int(dist),14):
    x=a[0]+dx*s/dist;y=a[1]+dy*s/dist
    line('道路虚线',[(x,y,z+.02),(x+dx/dist*5,y+dy/dist*5,z+.02)],.12,stone)
  if dist>10:
   for s in range(6,int(dist),28 if ped else 38):
    x=a[0]+dx*s/dist+nx*(width+1);y=a[1]+dy*s/dist+ny*(width+1)
    if math.hypot(x,y)<700:
     cyl('路灯杆',(x,y,z),(x,y,z+6),.16,dark,n=8)
     sphere('路灯光源',(x,y,z+6),.48,white,12,8)
     if not ped:treepts.append((x+nx*4,y+ny*4))
 if ff:mesh(t.get('name',hw)+' · OSM道路',vv,ff,stone if ped else asphalt)
 roadpaths.append((pts,width))

collection('03 东方明珠 · 主体与灯光')
for radius,z in [(69,1.2),(65,2.1),(61,3),(56,4)]:
 cyl('阶梯环台',(0,0,z-1),(0,0,z),radius,stone,n=96)
 ring('环台灯带',0,0,z+.1,radius-.3,.16,cyan)
cyl('塔座',(0,0,4),(0,0,14),35,concrete,31,96)
ring('塔座檐口',0,0,14,31,.45,cyan)
for a in [math.radians(30)+i*math.tau/3 for i in range(3)]:
 x,y=8.8*math.cos(a),8.8*math.sin(a)
 cyl('直径9m承重立柱',(x,y,10),(x,y,263),4.5,concrete,n=48)
 bx,by=55*math.cos(a),55*math.sin(a)
 cyl('外斜撑',(bx,by,4),(x,y,92),3.7,concrete,3.1,32)
 # Long fine edge lights, separate from the white concrete surface.
 for off in [-.55,.55]:
  aa=a+off
  ox,oy=4.52*math.cos(aa),4.52*math.sin(aa)
  cyl('立柱蓝光',(x+ox,y+oy,119),(x+ox,y+oy,255),.24,cyan,n=8)
 line('斜撑蓝光',[(bx,by,5),(x+2*math.cos(a),y+2*math.sin(a),78)],.26,cyan)
 sphere('斜撑小球',(bx*.52+x*.48,by*.52+y*.48,46),5.5,panel)
 ring('小球腰线',bx*.52+x*.48,by*.52+y*.48,46,5.5,.15,gold)
for z in [133,157,181,205,229,252]:
 for i in range(3):
  a=math.radians(30)+i*math.tau/3;b=a+math.tau/3
  cyl('立柱间连桥',(8.8*math.cos(a),8.8*math.sin(a),z),(8.8*math.cos(b),8.8*math.sin(b),z),1.5,concrete,n=12)
for i,z in enumerate([135,157,179,201,223]):sphere('空中客房球体 '+str(i+1),(0,0,z),5,panel,32,16)

def pearl(name,x,y,z,r):
 sphere(name,(x,y,z),r,panel,96,48)
 for j in range(-7,8):
  lat=j*math.pi/18;rr=r*math.cos(lat);zz=z+r*math.sin(lat)
  ring(name+' 纬向细框',x,y,zz,rr+.03,.09,dark)
 # Diamond diagonal mullions follow the curved skin.
 for phase in range(32):
  for sign in [-1,1]:
   pts=[]
   for k in range(41):
    lat=-1.38+2.76*k/40;a=phase*math.tau/32+sign*lat*.55
    pts.append((x+(r+.08)*math.cos(lat)*math.cos(a),y+(r+.08)*math.cos(lat)*math.sin(a),z+(r+.08)*math.sin(lat)))
   line(name+' 菱形骨架',pts,.075,concrete)
 # Tiny luminous nodes make a dotted lattice, not a solid neon sphere.
 for j in range(-7,8):
  lat=j*math.pi/18;rr=(r+.18)*math.cos(lat);zz=z+(r+.18)*math.sin(lat)
  for i in range(40):
   a=(i+(j%2)*.5)*math.tau/40
   sphere(name+' 点光',(x+rr*math.cos(a),y+rr*math.sin(a),zz),.19,cyan if j%3 else magenta,8,4)
 for dz in [-r*.57,-r*.49]:
  rr=math.sqrt(r*r-dz*dz)
  ring(name+' 观光层',x,y,z+dz,rr+.2,.48,cyan)
pearl('下球体 · 直径50m',0,0,95,25)
pearl('上球体 · 直径45m',0,0,277.5,22.5)
cyl('上球体至太空舱',(0,0,296),(0,0,343),3.4,concrete,2.8,40)
for z in range(303,338,4):ring('上塔节段',0,0,z,3.45,.1,gold)
pearl('太空舱',0,0,344,7)
cyl('天线基段',(0,0,350),(0,0,388),2.2,concrete,1.6,24)
cyl('天线中段',(0,0,388),(0,0,430),1.2,concrete,.7,20)
cyl('天线尖端',(0,0,430),(0,0,468),.65,concrete,.10,16)
for z,r in [(358,2.5),(379,2.1),(391,1.7),(413,1.3),(437,.9),(463,.5)]:ring('天线灯环',0,0,z,r,.17,cyan)
sphere('航空障碍灯',(0,0,468),.45,white,12,8)

collection('04 周边建筑 · OSM轮廓与分部')
audit=[];footprints=[]
# Urban objects with missing heights are explicitly marked estimated.
special={'40779113':48,'165166879':100,'165985305':95,'520990201':120,'965004738':55}
skip={'40778038','40778072'}
def windows(name,pts,h,z0=1.0):
 if pts[0]==pts[-1]:pts=pts[:-1]
 verts=[];faces=[];inds=[]
 area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]));sgn=1 if area>0 else -1
 for a,b in zip(pts,pts[1:]+pts[:1]):
  dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
  if length<2:continue
  ux,uy=dx/length,dy/length;nx,ny=uy*sgn,-ux*sgn
  for z in range(max(3,int(z0+2)),int(h-1),4):
   for k in range(1,max(2,int(length/3.5))):
    if random.random()>.55:continue
    s=k*length/max(2,int(length/3.5));x=a[0]+ux*s+nx*.08;y=a[1]+uy*s+ny*.08
    ww=min(1.05,length*.12);ii=len(verts)
    verts.extend([(x-ux*ww,y-uy*ww,z),(x+ux*ww,y+uy*ww,z),(x+ux*ww,y+uy*ww,z+1.7),(x-ux*ww,y-uy*ww,z+1.7)])
    faces.append((ii,ii+1,ii+2,ii+3));inds.append(random.choices(range(4),[4,3,1,3])[0])
 if faces:
  o=mesh(name+' · 窗灯',verts,faces,None)
  for m in window_mats:o.data.materials.append(m)
  for p,i in zip(o.data.polygons,inds):p.material_index=i
for f in features:
 t=f['tags'];pts=points(f)
 if not (t.get('building') or t.get('building:part')) or f['id'] in skip or len(pts)<4 or not near(pts,650):continue
 if math.hypot(*center(pts))<70:continue
 h=float(t['height'].split(';')[0].replace('m','')) if t.get('height') else float(t.get('building:levels',3))*3.8
 source='OSM height' if t.get('height') else 'OSM levels x 3.8m' if t.get('building:levels') else 'estimated 11.4m'
 if f['id'] in special:h=special[f['id']];source='estimated visual massing'
 h=max(h,4);base=float(t.get('min_height',.9));name=t.get('name',t.get('name:en','建筑 '+f['id']))
 o=extrude(name,pts,base,h,glass if h>45 else stone);o['osm_id']=f['id'];o['height_basis']=source;o['detail']='simplified massing; facade not surveyed'
 footprints.append(pts);windows(name,pts,h,base)
 line(name+' 檐口',[(*p,h+.1) for p in pts],.17,gold,True)
 if h>80:
  for z in range(12,int(h),12):line(name+' 层间线',[(*p,z) for p in pts],.10,gold if int(f['id'])%3==0 else dark,True)
  cx,cy=center(pts)
  if t.get('roof:shape')=='dome':
   r=min(max(p[0] for p in pts)-min(p[0] for p in pts),max(p[1] for p in pts)-min(p[1] for p in pts))*.38
   dome=sphere(name+' 穹顶',(cx,cy,h),r,glass);dome.scale.z=r*1.25
   for a in range(0,360,15):
    aa=math.radians(a);line('穹顶肋',[(cx+r*math.cos(k*math.pi/40)*math.cos(aa),cy+r*math.cos(k*math.pi/40)*math.sin(aa),h+1.25*r*math.sin(k*math.pi/40)) for k in range(21)],.18,gold)
  else:box(name+' 屋顶机房',(cx,cy,h+2),(7,9,4),dark)
 audit.append(dict(osm_id=f['id'],name=name,height=h,basis=source))

collection('05 国际会议中心 · 双球与柱廊')
f=next(f for f in features if f['id']=='40778072');pts=points(f)
extrude('国际会议中心 · OSM基底',pts,.9,27,concrete);footprints.append(pts)
windows('会议中心',pts,27)
line('会议中心屋檐',[(*p,27.3) for p in pts],.27,gold,True)
# Photo-estimated spheres anchored to the north/south ends of the mapped footprint.
cx,cy=center(pts)
for lon,lat,rad in [(121.49237,31.24216,19),(121.49208,31.24118,23)]:
 x,y=xy((lon,lat));cyl('球厅裙房',(x,y,.9),(x,y,18),rad+2,concrete,n=64)
 sphere('会议中心玻璃球',(x,y,28),rad,glass,64,32)
 for dz in range(-14,rad,4):
  rr=math.sqrt(max(.01,rad*rad-dz*dz));ring('球厅纬向框',x,y,28+dz,rr+.04,.10,concrete)
 for a in range(0,360,15):
  aa=math.radians(a);line('球厅经向框',[(x+rad*math.cos(k*math.pi/40)*math.cos(aa),y+rad*math.cos(k*math.pi/40)*math.sin(aa),28+rad*math.sin(k*math.pi/40)) for k in range(-20,21)],.09,concrete)
 ring('球厅灯带',x,y,18,rad*.9,.24,cyan)
for a,b in zip(pts,pts[1:]):
 dist=math.dist(a,b)
 if dist<30:continue
 for k in range(1,int(dist/6)):
  x=a[0]+(b[0]-a[0])*k/int(dist/6);y=a[1]+(b[1]-a[1])*k/int(dist/6)
  cyl('会议中心外柱廊',(x,y,1),(x,y,26),.55,concrete,n=12)

collection('06 绿化 · 实例树木')
# Gather mapped green polygons and plant only outside buildings and road ribbons.
green_polys=[points(f) for f in features if (f['tags'].get('landuse') in ['grass','forest'] or f['tags'].get('leisure') in ['garden','park'] or f['tags'].get('natural') in ['wood','scrub']) and near(points(f),650)]
for poly in green_polys:
 if len(poly)<3:continue
 xmin=max(-550,min(p[0] for p in poly));xmax=min(600,max(p[0] for p in poly));ymin=max(-600,min(p[1] for p in poly));ymax=min(400,max(p[1] for p in poly))
 for _ in range(min(550,int(max(0,(xmax-xmin)*(ymax-ymin))/140))):
  pt=(random.uniform(xmin,xmax),random.uniform(ymin,ymax))
  if inside(pt,poly) and math.hypot(*pt)>76 and not any(inside(pt,b) for b in footprints):treepts.append(pt)
# Reusable meshes avoid thousands of unique tree geometries.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);proto=put(bpy.context.object,'树冠原型',foliage);canopy_mesh=proto.data;bpy.data.objects.remove(proto,do_unlink=True)
bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.25,radius2=.13,depth=4);proto=put(bpy.context.object,'树干原型',dark);trunk_mesh=proto.data;bpy.data.objects.remove(proto,do_unlink=True)
for x,y in treepts:
 if inside((x,y),river) or any(inside((x,y),b) for b in footprints):continue
 o=bpy.data.objects.new('树干',trunk_mesh);COL.objects.link(o);o.location=(x,y,2.8)
 o=bpy.data.objects.new('树冠',canopy_mesh);COL.objects.link(o);o.location=(x,y,6);s=random.uniform(2.4,4.5);o.scale=(s,s,s*1.35)

collection('07 江面船只 · 简化配景')
for lon,lat,angle in [(121.488,31.2418,25),(121.490,31.245,-40),(121.489,31.2384,70)]:
 x,y=xy((lon,lat));hull=box('游船船体',(x,y,1.3),(42,11,2.2),dark,2);hull.rotation_euler.z=math.radians(angle)
 for z,size in [(3,(32,8,2)),(5,(25,7,1.5))]:
  o=box('游船上层',(x,y,z),size,concrete,1);o.rotation_euler.z=math.radians(angle)
 aa=math.radians(angle)
 for side in [-1,1]:
  pts=[(x+u*math.cos(aa)-side*4*math.sin(aa),y+u*math.sin(aa)+side*4*math.cos(aa),4.2) for u in [-16,16]]
  line('船舷灯',pts,.18,white)

collection('08 灯光与相机')
scene=bpy.context.scene
scene.world=bpy.data.worlds.new('蓝调夜空');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.062,.12,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
def area(name,loc,target,energy,color,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 return o
area('月光主光',(-300,-100,650),(0,0,100),800000,(.48,.65,1),500)
area('塔身正面补光',(-100,100,200),(0,0,180),100000,(.25,.5,1),120)
area('塔身背面补光',(120,-100,220),(0,0,180),100000,(.25,.5,1),100)
area('塔座泛光',(0,0,65),(0,0,0),45000,(.3,.65,1),65)
area('会议中心泛光',(-250,20,100),(-260,-20,0),30000,(1,.68,.37),140)
def cam(name,loc,target,lens):
 d=bpy.data.cameras.new(name);d.lens=lens;d.clip_end=20000
 o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cameras=[cam('01 滨江空中全景',(-800,510,610),(0,-60,150),38),cam('02 东方明珠近景',(-490,260,160),(0,0,240),40),cam('03 朝向外滩航拍',(640,-640,630),(-60,45,165),40)]
scene.camera=cameras[0]
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for dev in pref.devices:dev.use=dev.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print('GPU setup',e)
scene.cycles.max_bounces=5;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=3
scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.3
nt=bpy.data.node_groups.new('夜景光晕','CompositorNodeTree');scene.compositing_node_group=nt
nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.inputs['Type'].default_value='Fog Glow';gl.inputs['Quality'].default_value='Medium';gl.inputs['Strength'].default_value=.25
nt.links.new(rl.outputs['Image'],gl.inputs['Image']);co=nt.nodes.new('NodeGroupOutput');nt.links.new(gl.outputs['Image'],co.inputs['Image'])
scene.unit_settings.system='METRIC'
scene['georeference']='WGS84 local tangent approximation: origin 121.49536 E, 31.24188 N; X east, Y north, Z up; metres'
scene['status']='v01 study: real OSM footprints, custom tower; approximate facades and selected missing heights. Not a survey model.'
scene['reference_video']='WCY Douyin 7544342884154805561; visual reference only, not bundled in redistributable asset.'
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.clip_end=20000;a.spaces.active.region_3d.view_perspective='CAMERA'
   a.spaces.active.shading.type='MATERIAL';a.spaces.active.shading.use_scene_world=True;a.spaces.active.shading.use_scene_lights=True
   a.spaces.active.overlay.show_overlays=False
bpy.ops.object.select_all(action='DESELECT')
# Store editable .blend before costly rendering.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'东方明珠_滨江夜景_v01.blend'))
(OUT/'building_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('SCENE_SAVED',len(bpy.data.objects),'objects',flush=True)
for i,c in enumerate(cameras):
 scene.camera=c;scene.render.filepath=str(OUT/f'preview_{i+1:02d}.png');bpy.ops.render.render(write_still=True)
scene.camera=cameras[0]
scene.render.engine='BLENDER_EEVEE'
if hasattr(scene.eevee,'use_raytracing'):scene.eevee.use_raytracing=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'东方明珠_滨江夜景_v01.blend'))
print('DONE',flush=True)
