import bpy,ast,math,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import tessellate_polygon
R=Path(bpy.data.filepath).parent;D=R/'制作资料';s=bpy.context.scene
bpy.context.preferences.view.language='en_US';LON=121.49536;LAT=31.24188;cache={};COL=None
for filename,names in [('build_pearl.py',{'collection','put','material','mesh','instance','box','cyl','line','extrude','polygon','ring','xy','points','center'}),('upgrade_v02.py',{'clean','signed','shell'})]:
 t=ast.parse((D/'scripts'/filename).read_text(encoding='utf8'));exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))
f=json.loads((D/'reference/map_expanded.json').read_text(encoding='utf8'));byid={x['id']:x for x in f}
white=material('低层白色铝板',(.64,.66,.65),.15,.53);dark=material('低层内退橱窗',(.022,.042,.043),.25,.24);metal=material('低层幕墙铝肋',(.36,.39,.4),.65,.4);blue=material('水族馆蓝色鱼群',(.015,.1,.25),.3,.4);green=material('水族馆绿色鱼群',(.015,.23,.12),.15,.5);roofmat=bpy.data.materials['v02 深灰屋面']
for o in list(bpy.data.objects):
 if o.name.startswith(('迪士尼旗舰店','水族馆基座','水族馆墙板')) or any(c.name.startswith('22 低层实景') for c in o.users_collection):bpy.data.objects.remove(o,do_unlink=True)
collection('22 低层实景 · 水族馆与旗舰店')
font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc',check_existing=True)
def sign(text,q,n,size,mat):
 c=bpy.data.curves.new(text,'FONT');c.body=text;c.font=font;c.size=size;c.align_x='CENTER';c.extrude=.025;o=bpy.data.objects.new(text,c);COL.objects.link(o);o.location=q
 normal=Vector((n.x,n.y,0));right=Vector((-n.y,n.x,0));o.rotation_euler=Matrix((right,Vector((0,0,1)),normal)).transposed().to_euler();c.materials.append(mat)
pts=clean(points(byid['404676268']));heights=[8,9,29,9,8];base=extrude('水族馆内退入口层',pts,.9,5,dark);base['osm_id']='404676268'
old=bpy.data.objects.get('水族馆折面斜屋顶')
if old:
 old.data.materials[0]=white
 # A folded aluminium enclosure should keep the same white material on its sloping top.
 for p in old.data.polygons:p.material_index=0
sg=signed(pts)
for i,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
 a=Vector(a);b=Vector(b);u=(b-a).normalized();normal=Vector((u.y,-u.x))*sg;length=(b-a).length;h1,h2=heights[i],heights[(i+1)%len(pts)]
 def pos(d,z):q=a+u*d+normal*.055;return(q.x,q.y,z)
 for d in range(0,int(length),3):
  h=h1+(h2-h1)*d/length;line('水族馆铝板竖缝',[pos(d,5),pos(d,h)],.012,metal)
 for z in range(7,29,2):
  if z>=max(h1,h2):continue
  lo=0;hi=length
  if z>h1:lo=(z-h1)/(h2-h1)*length
  if z>h2:hi=(z-h1)/(h2-h1)*length
  if hi>lo:line('水族馆铝板横缝',[pos(lo,z),pos(hi,z)],.012,metal)
 for d in range(2,int(length)-1,6):
  q=a+u*d+normal*.15;box('入口层方柱',(q.x,q.y,2.95),(.5,.5,4.1),white)
 if length>55:
  for d in range(8,int(length)-7,7):
   ceiling=h1+(h2-h1)*d/length
   if ceiling<11:continue
   for k in [-1,1]:
    chain=[pos(d+t*3.0,9.7+k*.40*math.sin(t*math.pi)) for t in [j/12 for j in range(-12,13)]];line('水族馆蓝绿鱼形饰带',chain,.085,blue if (d//7)%2 else green)
  d=length*.58;h=h1+(h2-h1)*d/length
  if h>17:sign('上海海洋水族馆',pos(d,15.5),normal,1.45,green)
# Distinct mapped crescent storefront, folded low roof and roof motif visible in the aerial reference.
pts=clean(points(byid['427786590']));ob=extrude('迪士尼旗舰店低层橱窗',pts,.8,5.3,dark);ob['osm_id']='427786590';ob['height_m']=6.8;ob['geometry_accuracy']='Mapped plan and reference-fitted low roof; approximate height'
roof=extrude('迪士尼旗舰店异形屋面',pts,5.3,6.0,roofmat)
sg=signed(pts)
for a,b in zip(pts,pts[1:]+pts[:1]):
 a=Vector(a);b=Vector(b);u=(b-a).normalized();normal=Vector((u.y,-u.x))*sg;length=(b-a).length
 for d in range(max(1,math.ceil(length/.8))):
  q=a+u*min(length,d*.8)+normal*.06;line('旗舰店竖向银色细肋',[(q.x,q.y,.8),(q.x,q.y,5.45)],.035,metal)
 line('旗舰店弧形檐口',[(a.x,a.y,5.5),(b.x,b.y,5.5)],.14,white)
for cx,cy,radius in [(-53,-170,7.3),(-62,-164,4.5),(-49,-159,4.5)]:ring('旗舰店屋顶轮廓标识',cx,cy,6.08,radius,.14,white)
# Entrance glass and panel seams are true geometry, editable without raster facade photos.
for name,loc,target in [('低层建筑实景校核',(320,-70,55),(183,86,13)),('环岛低层与道路',(0,-430,150),(28,-180,10))]:
 cam=bpy.data.objects.get(name)
 if not cam:data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);s.collection.objects.link(cam)
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('LOWRISE_SAVED')
