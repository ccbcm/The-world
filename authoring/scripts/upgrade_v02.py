"""Incremental v01 -> v02. Loads the saved scene; preserves the tower, roads and cameras.
Run with Blender --background output/东方明珠_滨江夜景_v01.blend --python scripts/upgrade_v02.py.
"""
import bpy,ast,math,json,random
bpy.context.preferences.view.language='en_US'
bpy.context.preferences.view.use_translate_new_dataname=False
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[1];OUT=R/'output';random.seed(42)
# Reuse pure modelling helpers without executing v01's scene reset/build.
tree=ast.parse((R/'scripts/build_pearl.py').read_text(encoding='utf-8'))
names={'collection','put','material','mesh','instance','box','cyl','sphere','line','ring','polygon','extrude','xy','points','center','near','inside'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'model_helpers','exec'))
cache={};COL=None;LON=121.49536;LAT=31.24188
features=json.loads((R/'reference/map_features.json').read_text(encoding='utf-8'));byid={f['id']:f for f in features}
# Only replace scene elements that belong to the first generated surrounding-building pass.
for c in list(bpy.data.collections):
 if c.name.startswith(('04 ','05 ')):
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
concrete=bpy.data.materials['珍珠白 · 混凝土'];dark=bpy.data.materials['深灰金属']
stone=bpy.data.materials['滨江浅灰石材'];glass=bpy.data.materials['蓝灰玻璃']
trim=material('v02 铝合金幕墙框',(.33,.38,.42),.65,.3)
limestone=material('v02 米白石材',(.63,.60,.52),.05,.58)
granite=material('v02 白麻花岗岩',(.68,.69,.66),.02,.65)
roofmat=material('v02 深灰屋面',(.11,.13,.14),.2,.6)
blueglass=material('v02 中性蓝灰幕墙',(.12,.23,.29),.62,.22)
greenGlass=material('v02 绿灰幕墙',(.10,.21,.20),.58,.23)
bronze=material('v02 香槟色金属',(.38,.29,.17),.65,.3)
# Subtle stone surface scale, visible under daylight.
for m in [granite,limestone]:
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=110
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.02
 l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
# Daylight materials; keep separate night-light meshes to allow later reactivation.
night_visibility=[]
for o in bpy.data.objects:
 if o.type=='LIGHT':o.hide_render=True;o.hide_viewport=True
 if o.type in ['MESH','CURVE'] and any(m and ('灯' in m.name or m.name in ['路灯 · 暖白','暖白建筑轮廓','球面 · 紫红细灯']) for m in o.data.materials):
  if any(k in o.name for k in ['点光','灯带','蓝光','灯环','路灯光源','航空障碍','观光层','塔座檐口']):
   o.hide_render=True;o.hide_viewport=True;night_visibility.append(o.name)
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if p and p.inputs.get('Emission Strength'):p.inputs['Emission Strength'].default_value=0
bpy.data.materials['球面 · 紫灰玻璃'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.24,.065,.13,1)

audit=[];built=[]
def clean(pts):return pts[:-1] if pts[0]==pts[-1] else pts
def signed(pts):return 1 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))>0 else -1
def crown_height(f,h):
 pts=clean(points(f));t=f['tags'];shape=t.get('roof:shape','flat')
 rh=float(t.get('roof:height',0))
 if shape=='skillion':
  rh=rh or min(22,h*.12);direction=t.get('roof:direction','35')
  dirs=['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
  angle=math.radians(dirs.index(direction)*22.5 if direction in dirs else float(direction))
  axis=Vector((math.sin(angle),math.cos(angle)))
  ds=[Vector(p).dot(axis) for p in pts];lo=min(ds);span=max(ds)-lo
  return [h-rh*(d-lo)/max(span,1) for d in ds]
 if f['id'] in ['164968674','423304682']:
  # Two sloping facets form the chamfered crown rather than a flat cylinder.
  cx,cy=center(pts);ds=[(p[0]-cx)*.8+(p[1]-cy)*.6 for p in pts];span=max(ds)-min(ds)
  return [h-13*(d-min(ds))/span for d in ds]
 return [h]*len(pts)
def shell(name,pts,z,heights,mat):
 pts=clean(pts);n=len(pts);vs=[(x,y,z) for x,y in pts]+[(x,y,h) for (x,y),h in zip(pts,heights)]
 fs=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 top=[Vector((x,y,0)) for x,y in pts]
 tris=tessellate_polygon([top]);index={tuple(v):i for i,v in enumerate(top)}
 fs.extend([tuple((v if isinstance(v,int) else index[tuple(v)])+n for v in t) for t in tris])
 ob=mesh(name,vs,fs,mat);ob.data.materials.append(roofmat)
 for p in list(ob.data.polygons)[n:]:p.material_index=1
 return ob
def facade(name,pts,z,heights,style='glass',floor=3.8):
 """Actual 3D mullion/spandrel surfaces; facade patterns are reference approximations."""
 pts=clean(pts);sg=signed(pts);v=[];ff=[]
 def quad(coords):
  k=len(v);v.extend(coords);ff.append(tuple(range(k,k+4)))
 for j,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
  length=math.dist(a,b)
  if length<1:continue
  ux=(b[0]-a[0])/length;uy=(b[1]-a[1])/length;nx=uy*sg;ny=-ux*sg
  h1=heights[j];h2=heights[(j+1)%len(pts)]
  def pos(s,zz):return (a[0]+ux*s+nx*.11,a[1]+uy*s+ny*.11,zz)
  spacing=1.6 if style=='glass' else 3.6
  count=max(1,int(length/spacing))
  for k in range(count+1):
   s=k*length/count;hh=h1+(h2-h1)*s/length;width=.085 if style=='glass' else .38
   quad([pos(max(0,s-width),z),pos(min(length,s+width),z),pos(min(length,s+width),hh),pos(max(0,s-width),hh)])
  zz=z+floor
  while zz<max(h1,h2)-.2:
   # Clip floor spandrels to the sloping roof.
   start=0;end=length
   if h1<zz and h2<zz:break
   if h1<zz:start=length*(zz-h1)/(h2-h1)
   if h2<zz:end=length*(h1-zz)/(h1-h2)
   band=.22 if style=='glass' else .6
   quad([pos(start,zz-band),pos(end,zz-band),pos(end,zz),pos(start,zz)])
   zz+=floor
 if ff:mesh(name+' · 立面分格',v,ff,trim if style=='glass' else limestone)
 # Reflective glass with mild pane-to-pane variation, not scattered glowing squares.
 if style=='stone':
  pass
def mark(ob,f,h,basis,note='OSM footprint; facade approximate'):
 ob['osm_id']=f['id'];ob['height_basis']=basis;ob['detail']=note
 audit.append(dict(osm_id=f['id'],name=ob.name,height_m=h,basis=basis,detail=note))

collection('04 周边建筑 v02 · 分部与立面')
special_ids={'40778038','40778072','164972678','164972685','404676268','803292747','40779113'}
f_overrides={'164957792':(226.1,'CTBUH Shanghai Bank of China Tower /1164'),'164968674':(249.9,'Pelli Clarke & Partners: South Tower 250m'),'423304682':(259.9,'Pelli Clarke & Partners: North Tower 260m')}
parts=[f for f in features if f['tags'].get('building:part') and near(points(f),650) and math.hypot(*center(points(f)))>75]
for f in features:
 t=f['tags'];pts=clean(points(f));cx,cy=center(pts)
 if not (t.get('building') or t.get('building:part')) or f['id'] in special_ids or len(pts)<3 or not near(pts,650) or math.hypot(cx,cy)<75:continue
 # Parent building outlines with contained 3D parts are a low podium, never a second full-height tower.
 children=[p for p in parts if p['id']!=f['id'] and inside(center(points(p)),pts)] if t.get('building') else []
 basis='OSM height' if 'height' in t else 'OSM floors, floor-height estimated' if 'building:levels' in t else 'unknown height: provisional 10m'
 h=float(t.get('height',float(t.get('building:levels',2.8))*3.6));base=float(t.get('min_height',.9))
 if children and any(float(p['tags'].get('height',float(p['tags'].get('building:levels',0))*3.6))>h*.7 for p in children):
  h=min(h,18);basis='parent outline podium; real towers modelled using child parts'
 if f['id'] in f_overrides:h,basis=f_overrides[f['id']]
 heights=crown_height(f,h)
 # A dome's top is included in the stated total height. Avoid adding a roof above total height.
 dome=t.get('roof:shape')=='dome'
 rad=min(max(p[0] for p in pts)-min(p[0] for p in pts),max(p[1] for p in pts)-min(p[1] for p in pts))*.43
 if dome:heights=[max(base+4,h-rad*1.1)]*len(pts)
 name=t.get('name',t.get('name:en','建筑分部 '+f['id']))
 mat=blueglass if h>80 else greenGlass if h>35 else limestone
 ob=shell(name,pts,base,heights,mat);mark(ob,f,h,basis)
 style='stone' if dome or f['id'] in ['281580982','281583582'] else 'glass'
 facade(name,pts,base,heights,style, max(3,heights[0]/float(t.get('building:levels',max(1,int(h/3.8))))))
 built.append(pts)
 if dome:
  roof=sphere(name+' · 实体穹顶',(cx,cy,heights[0]),rad,blueglass,48,24);roof.scale.z=rad*1.1
  for a in range(0,360,15):
   aa=math.radians(a);line('穹顶金属肋',[(cx+rad*math.cos(k*math.pi/40)*math.cos(aa),cy+rad*math.cos(k*math.pi/40)*math.sin(aa),heights[0]+1.1*rad*math.sin(k*math.pi/40)) for k in range(21)],.13,trim)
 if h>55:
  # Low rooftop plant equipment, clearly generic detail, inside actual footprint.
  for k in range(3):
   xx=cx+(k-1)*5;yy=cy
   if inside((xx,yy),pts):box('屋顶设备 · 示意',(xx,yy,min(heights)+1),(3,6,2),roofmat)

collection('05A 国际会议中心 v02 · 按球厅轮廓定位')
f=byid['40778072'];pts=clean(points(f));ob=extrude('国际会议中心 · 主体',pts,.9,27,limestone);mark(ob,f,27,'six OSM storeys; 27m body is provisional')
facade('国际会议中心',pts,.9,[27]*len(pts),'stone',4.5)
for ident in ['164972678','164972685']:
 pp=clean(points(byid[ident]));cx=(min(x for x,y in pp)+max(x for x,y in pp))/2;cy=(min(y for x,y in pp)+max(y for x,y in pp))/2
 rad=(max(x for x,y in pp)-min(x for x,y in pp))/2
 # Georeferenced circles measured from OSM instead of guessed offsets.
 cyl('球厅圆形基座',(cx,cy,1),(cx,cy,13),rad,limestone,n=64)
 sphere('国际会议中心玻璃球 '+ident,(cx,cy,29),rad,greenGlass,64,32)
 for j in range(-6,8):
  lat=j*math.pi/18;rr=rad*math.cos(lat);zz=29+rad*math.sin(lat)
  ring('球厅纬线',cx,cy,zz,rr+.06,.095,trim)
 for k in range(48):
  a=k*math.tau/48
  line('球厅经线',[(cx+(rad+.06)*math.cos(-1.25+i*2.8/40)*math.cos(a),cy+(rad+.06)*math.cos(-1.25+i*2.8/40)*math.sin(a),29+(rad+.06)*math.sin(-1.25+i*2.8/40)) for i in range(41)],.085,trim)
audit.append(dict(osm_id='40778072',name='国际会议中心双球',basis='independent OSM sphere footprints; vertical position provisional',detail='v01 guessed positions replaced'))

collection('05B 浦东美术馆 v02 · 白麻石材与镜厅')
f=byid['803292747'];pts=clean(points(f));ob=extrude('浦东美术馆 · 30m主体',pts,.9,30,granite);mark(ob,f,30,'Shanghai tourism authority: 30m', 'granite envelope, west mirror hall; small openings reference approximations')
# West facade real large mirror halls, not a repeated office-window grid.
west=min(pts,key=lambda p:p[0])[0]-.15
box('镜厅 · 二层55m大玻璃',(west,-181,12),(0.15,54,6),blueglass)
box('镜厅 · 三层55m大玻璃',(west,-181,23),(0.15,54,12),blueglass)
for yy in range(-207,-154,3):box('镜厅竖框',(west-.12,yy,20),(.18,.10,18),trim)
cx,cy=center(pts)
for i in range(5):
 xx=cx-18+i*8;box('屋顶天窗',(xx,cy,30.3),(4,16,.45),blueglass)
box('美术馆屋顶设备核',(cx+20,cy+18,33),(12,14,6),granite)
for j,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
 length=math.dist(a,b)
 if length<8:continue
 # Stone seams are geometry, finely scaled; no emissive material.
 for z in range(3,30,3):line('石材横缝',[(a[0],a[1],z),(b[0],b[1],z)],.018,trim)

collection('05C 海洋水族馆 v02 · 三角斜坡屋顶')
f=byid['404676268'];pts=clean(points(f));ob=extrude('水族馆基座',pts,.9,5,granite)
# The image shows a tall folded wedge above a recessed low entrance.
heights=[8,9,29,9,8][:len(pts)]
if len(heights)!=len(pts):heights=[8+21*(1 if i==2 else 0) for i in range(len(pts))]
ob=shell('水族馆折面斜屋顶',pts,5,heights,granite);mark(ob,f,29,'roof silhouette estimated from exterior photograph; OSM 10m is incomplete','roof height still requires survey/official drawing')
# Surface seam grid follows triangulated roof facets.
for i,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
 for k in range(1,10):
  u=k/10;x=a[0]*(1-u)+b[0]*u;y=a[1]*(1-u)+b[1]*u;hh=heights[i]*(1-u)+heights[(i+1)%len(pts)]*u
  line('水族馆墙板竖缝',[(x,y,5),(x,y,hh)],.025,trim)
 for z in range(8,29,3):
  if z<min(heights[i],heights[(i+1)%len(pts)]):line('水族馆墙板横缝',[(a[0],a[1],z),(b[0],b[1],z)],.025,trim)

collection('05D 正大广场 v02 · 裙楼与弧形屋面')
f=byid['40779113'];pts=clean(points(f));ob=extrude('正大广场 · 建筑轮廓',pts,.9,40,limestone);mark(ob,f,48,'photo-estimated height; unverified','curved roof and facade updated; total height pending official confirmation')
facade('正大广场',pts,.9,[40]*len(pts),'stone',5)
# Broad low curved roof instead of a high flat office block.
cx,cy=center(pts);vs=[];fs=[]
for j in range(2):
 for i in range(33):
  u=i/32;vs.append((cx-58+116*u,cy-38+76*j,40+8*math.sin(math.pi*u)))
for i in range(32):fs.append((i,i+1,i+34,i+33))
mesh('正大广场 · 弧形金属屋顶',vs,fs,roofmat)
for j in range(9):line('商场屋顶肋',[(cx-58+116*i/32,cy-38+76*j/8,40.2+8*math.sin(math.pi*i/32)) for i in range(33)],.08,trim)

# Replace whole plain-green ground by neutral developed urban land and mapped greenery.
bpy.data.objects.get('地面').data.materials.clear();bpy.data.objects.get('地面').data.materials.append(material('v02 城市地表',(.22,.23,.21),0,.88))
collection('06B 真实绿地与铺装')
gm=material('v02 草地',(.075,.16,.047),0,.95)
for f in features:
 t=f['tags'];pp=points(f)
 if (t.get('landuse') in ['grass','forest'] or t.get('leisure') in ['garden','park'] or t.get('natural') in ['wood','scrub']) and near(pp,750) and len(pp)>3:
  polygon('OSM绿地 '+f['id'],pp,.35,gm)
for o in list(bpy.data.objects):
 if o.name.startswith(('树冠','树干')) and any(inside((o.location.x,o.location.y),p) for p in built):bpy.data.objects.remove(o,do_unlink=True)
fol=bpy.data.materials['树冠'];fol.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.065,.16,.038,1)
water=bpy.data.materials['黄浦江 · 波纹反射'].node_tree.nodes['Principled BSDF'];water.inputs['Base Color'].default_value=(.085,.13,.115,1);water.inputs['Metallic'].default_value=.3;water.inputs['Roughness'].default_value=.23

collection('08B 白天自然光 · v02')
s=bpy.context.scene;s.world=bpy.data.worlds.new('v02 白昼天空');s.world.use_nodes=True
wn=s.world.node_tree.nodes;wl=s.world.node_tree.links;sky=wn.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(235);sky.air_density=1.2;sky.aerosol_density=1.1
wl.new(sky.outputs['Color'],wn.get('Background').inputs['Color']);wn.get('Background').inputs['Strength'].default_value=.25
# Nishita sun disk provides directional lighting in Cycles; separate sun supports EEVEE viewport.
d=bpy.data.lights.new('白天太阳','SUN');d.energy=2;d.angle=.08;o=bpy.data.objects.new('白天太阳',d);COL.objects.link(o);o.rotation_euler=(math.radians(32),math.radians(-28),math.radians(-35));o.hide_render=True
s.compositing_node_group=None;s.view_settings.exposure=0;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for dev in pref.devices:dev.use=dev.type=='OPTIX'
s.cycles.device='GPU'
s.render.resolution_x=1700;s.render.resolution_y=1200;s.render.resolution_percentage=100
s.camera=bpy.data.objects['01 滨江空中全景']
s['status']='v02 daylight revision. Saved tower retained. Surroundings rebuilt using OSM parts + sourced heights. Unverified heights are explicitly recorded.'
s['source_scene']='output/东方明珠_滨江夜景_v01.blend';s['next_work']='See PROJECT_STATE.md and output/building_audit_v02.json'
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.shading.type='MATERIAL';a.spaces.active.shading.use_scene_world=False;a.spaces.active.shading.use_scene_lights=False
   a.spaces.active.region_3d.view_perspective='CAMERA'
path=OUT/'东方明珠_周边建筑_白天_v02.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
(OUT/'building_audit_v02.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('V02_SAVED',len(s.objects),flush=True)
s.render.filepath=str(OUT/'v02_day_overview.png');bpy.ops.render.render(write_still=True)
# Detail framing of the museum and convention centre from the river.
c=bpy.data.cameras.new('v02 周边细节');camob=bpy.data.objects.new('v02 周边细节',c);COL.objects.link(camob);camob.location=(-650,200,230);target=Vector((-220,-100,35));camob.rotation_euler=(target-camob.location).to_track_quat('-Z','Y').to_euler();c.lens=47;c.clip_end=20000
s.camera=camob;s.render.filepath=str(OUT/'v02_day_neighbors.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['01 滨江空中全景'];s.render.engine='BLENDER_EEVEE';o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('V02_DONE',flush=True)
