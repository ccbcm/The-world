import bpy,ast,math,json,random
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(bpy.data.filepath).parent;R=ROOT/'制作资料';s=bpy.context.scene
bpy.context.preferences.view.language='en_US'
tree=ast.parse((R/'scripts/build_pearl.py').read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'collection','put','material','mesh','instance','box','cyl','line','extrude'}],type_ignores=[]),'helpers','exec'))
from mathutils.geometry import tessellate_polygon
cache={};COL=None;report={}
# Superseded road adornments have no valid relation to the revised carriageway edges.
old=bpy.data.collections.get('02 道路 · 步道 · 滨江灯光');report['old_road_objects_removed']=len(old.objects)
for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
plan=json.loads((R/'场地清理方案.json').read_text(encoding='utf8'))
for o in list(bpy.data.objects):
 if o.name.startswith('连续路网 '):bpy.data.objects.remove(o,do_unlink=True)
collection('18 重新校核路网 · 车行人行分层')
for g in plan['roads']:
 vs=[];fs=[]
 for tri in g['triangles']:
  k=len(vs);vs.extend([(x,y,g['z']) for x,y in tri]);fs.append((k,k+1,k+2))
 ob=mesh('连续路网 '+g['name'],vs,fs,bpy.data.materials['道路沥青' if g['name']=='road' else '滨江浅灰石材'])
 uv=ob.data.uv_layers.new(name='RealWorldPBR')
 for p in ob.data.polygons:
  for li in p.loop_indices:v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)
# Replace the incorrect taper, not merely its tip.
for c in list(bpy.data.collections):
 if c.name.startswith(('12 金茂','16 金茂','16B 金茂')):
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
collection('19 金茂 · 参考轮廓重建')
cx,cy=576.74,-513.44
glass=bpy.data.materials['金茂灰玻璃'];silver=bpy.data.materials['金茂银灰结构']
p=next(n for n in silver.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Metallic'].default_value=.72;p.inputs['Roughness'].default_value=.34
# Control profile measured proportionally from supplied references; total elevation sourced separately.
profile=[(8,1),(60,.995),(111,.985),(157,.973),(198,.962),(234,.949),(266,.935),(292,.921),(313,.905),(330,.882),(342,.855),(352,.80),(361,.69),(369,.57),(376,.44),(383,.31),(390,.19)]
(R/'金茂轮廓控制.json').write_text(json.dumps(dict(profile=profile,note='Reference-fitted broad shaft; not construction survey. Shape control can be edited independently of detailing.'),ensure_ascii=False,indent=2),encoding='utf8')
quarter=[(34,0),(34,11),(31.5,13),(31.5,23),(23,31.5),(13,31.5),(11,34),(0,34)]
base=[]
for k in range(4):
 for x,y in quarter[:-1]:a=k*math.pi/2;base.append((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)))
def outline(scale):return [(cx+x*scale,cy+y*scale) for x,y in base]
for j,((z,scale),(top,nextscale)) in enumerate(zip(profile,profile[1:])):
 pp=outline(scale);ob=extrude('金茂参考主体第%02d段'%j,pp,z,top,glass);ob['osm_id']='376075961';ob['height_m']=420.5;ob['geometry_accuracy']='Reference-fitted, not survey';ob['height_source']='SOM / Jinmao operator'
 # Stepped facade ribs; broad bays remain almost vertical below the upper crown.
 for i,(a,b) in enumerate(zip(pp,pp[1:]+pp[:1])):
  ln=math.dist(a,b);ux=(b[0]-a[0])/ln;uy=(b[1]-a[1])/ln;nx,ny=uy,-ux
  if ln<2:continue
  for k in range(max(2,round(ln/1.35))+1):
   u=k/max(2,round(ln/1.35));x=a[0]+(b[0]-a[0])*u+nx*.11;y=a[1]+(b[1]-a[1])*u+ny*.11
   line('金茂幕墙细竖框',[(x,y,z),(x,y,top)],.055,silver)
  for zz in range(math.ceil(z/3.85),math.floor(top/3.85)+1):line('金茂逐层横框',[(a[0]+nx*.13,a[1]+ny*.13,zz*3.85),(b[0]+nx*.13,b[1]+ny*.13,zz*3.85)],.095,silver)
  if i%7 in [1,3,5]:
   for v in [a,b]:line('金茂成对竖向结构翼',[(v[0]+nx*.22,v[1]+ny*.22,z),(v[0]+nx*.65,v[1]+ny*.65,top-.8),(v[0]+nx*.22,v[1]+ny*.22,top)],.30,silver)
 for zz in [top-.7,top-.15]:line('金茂退台银色檐口',[(x,y,zz) for x,y in outline(scale+.008)],.15,silver,True)
# Small petal-shaped pinnacle rather than an oversized wire cage.
for k in range(8):
 a=k*math.tau/8;u=Vector((math.cos(a),math.sin(a),0));v=Vector((-math.sin(a),math.cos(a),0));c=Vector((cx,cy,0))
 vertices=[tuple(c+u*5.8+v*q+Vector((0,0,z))) for q,z in [(-.65,389),(.65,389),(.35,400),(-.35,403)]]
 mesh('金茂冠顶花瓣钢板',vertices,[(0,1,2,3)],silver)
cyl('金茂尖塔基座',(cx,cy,390),(cx,cy,404),2.1,silver,r2=.85,n=16)
cyl('金茂420.5m尖塔',(cx,cy,404),(cx,cy,420.5),.85,silver,r2=.04,n=16)
report['jinmao_profile']=profile
# Sign is actually China Ping An in the saved scene. Face normal used to point inward on half the faces.
fixed=[]
for o in [x for x in bpy.data.objects if x.type=='FONT']:
 if o.data.body not in ['中国平安','中国银行']:continue
 centre=Vector((251.3,-38.4,o.location.z));out=(o.location-centre).normalized();out.z=0;out.normalize()
 right=Vector((-out.y,out.x,0));up=Vector((0,0,1));o.rotation_euler=Matrix((right,up,out)).transposed().to_euler()
 # Existing tier projects farther than the old sign position: use its outer ray intersection envelope.
 radius=0
 for ob in bpy.data.collections['04P 平安金融大厦 v04 · 石材柱廊与203m穹顶'].objects:
  if ob.type!='MESH':continue
  for co in ob.bound_box:
   p=ob.matrix_world@Vector(co)
   if abs(p.z-158.5)<20:radius=max(radius,(p-centre).dot(out))
 o.location=centre+out*(max(radius,22)+.45);o.data.size=2.8;o.data.align_y='CENTER';o['sign_note']='Original China Ping An sign; corrected outward orientation and facade clearance.';fixed.append(o.name)
report['signs_corrected']=fixed
# Imported EZ-Tree geometry, with real branch hierarchy and transparent leaf cards.
collection('20 EZ-Tree · 地图绿地植被')
geom=json.loads((R/'eztree_geometry.json').read_text(encoding='utf8'));mats=[]
texroot=R/'第三方/ez-tree/src/app/public/textures'
for kind in ['bark','leaves']:
 m=material('EZ-Tree '+kind,(.2,.25,.14),0,.9);n=m.node_tree.nodes;l=m.node_tree.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');t=n.new('ShaderNodeTexImage')
 path=texroot/('leaves/oak.png' if kind=='leaves' else 'bark/Bark001_1K-JPG/Bark001_1K-JPG_Color.jpg')
 t.image=bpy.data.images.load(str(path),check_existing=True);l.new(t.outputs['Color'],bs.inputs['Base Color'])
 if kind=='leaves':l.new(t.outputs['Alpha'],bs.inputs['Alpha']);bs.inputs['Roughness'].default_value=.85
 m['license']='MIT Daniel Greenheck' if kind=='leaves' else 'CC0 ambientCG Bark001';mats.append(m)
vs=[];fs=[];uvs=[];mi=[]
for j,g in enumerate(geom):
 k=len(vs);vs.extend(g['vertices']);idx=g['index']
 for i in range(0,len(idx),3):
  ids=idx[i:i+3];fs.append(tuple(k+x for x in ids));uvs.extend([g['uv'][2*x:2*x+2] for x in ids]);mi.append(j)
me=bpy.data.meshes.new('EZ-Tree十米阔叶乔木');me.from_pydata(vs,[],fs);me.update()
for m in mats:me.materials.append(m)
uv=me.uv_layers.new(name='UVMap')
for i,co in enumerate(uvs):uv.data[i].uv=co
for p,i in zip(me.polygons,mi):p.material_index=i;p.use_smooth=i==0
for o in list(bpy.data.objects):
 if o.name.startswith(('树冠','树干')):bpy.data.objects.remove(o,do_unlink=True)
random.seed(531)
for x,y in plan['tree_locations']:
 o=bpy.data.objects.new('树冠 EZ-Tree',me);COL.objects.link(o);o.location=(x,y,.8);sc=random.uniform(.78,1.05);o.scale=(sc,sc,sc);o.rotation_euler.z=random.uniform(0,math.tau);o['full_tree']=True
report['trees_before']=1585;report['trees_after']=len(plan['tree_locations'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
(R/'本轮修正记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
for cname,pos,target,file,lens in [('金茂轮廓校核',(250,-960,215),(cx,cy,216),'金茂重建.png',48),('路网与绿化俯视',(-550,500,900),(0,-80,0),'路网绿化清理.png',42)]:
 cam=bpy.data.objects.new(cname,bpy.data.cameras.new(cname));s.collection.objects.link(cam);cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_end=30000;s.camera=cam;s.render.filepath=str(ROOT/'预览'/file);bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
print('CORE_CORRECTIONS_SAVED',report,flush=True)
