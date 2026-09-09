import bpy,json,math,ast,random
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(bpy.data.filepath).parent;s=bpy.context.scene;bpy.context.preferences.view.language='en_US'
t=ast.parse((R/'制作资料/scripts/build_pearl.py').read_text(encoding='utf8'));names={'collection','put','material','mesh','polygon','line','ring','extrude'};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'));cache={};COL=None
plan=json.loads((R/'制作资料/道路分层修正方案.json').read_text(encoding='utf8'));pts=next(b['points'] for b in plan['bridges'] if b['id']=='48876367')
# Polygon centroid, not the previous hand-entered floral offset.
area=0;cx=0;cy=0
for a,b in zip(pts,pts[1:]+pts[:1]):
 cross=a[0]*b[1]-b[0]*a[1];area+=cross;cx+=(a[0]+b[0])*cross;cy+=(a[1]+b[1])*cross
cx/=3*area;cy/=3*area
for o in list(bpy.data.objects):
 if o.name.startswith(('环岛低矮季节','环岛内缘','统一环岛')) or (o.name.startswith(('树冠','树干')) and math.hypot(o.location.x-cx,o.location.y-cy)<28):bpy.data.objects.remove(o,do_unlink=True)
collection('25 同心环岛与细植栽')
circle=[(cx+20*math.cos(i*math.tau/128),cy+20*math.sin(i*math.tau/128)) for i in range(128)]
extrude('统一环岛 石材围边基座',circle,.5,.89,bpy.data.materials['滨江浅灰石材'])
polygon('统一环岛 草坪',[(cx+19.75*math.cos(i*math.tau/128),cy+19.75*math.sin(i*math.tau/128)) for i in range(128)],.91,bpy.data.materials['v02 草地'])
soil=material('花坛真实土壤',(.15,.10,.06),0,1);leaf=material('花坛细叶',(.045,.12,.027),0,.9);bloom=material('季节花瓣',(.42,.025,.038),0,.85)
random.seed(218);vs=[];fs=[];lv=[];lf=[]
for k in range(5):
 a=k*math.tau/5
 def pos(u,v):return (cx+u*math.cos(a)-v*math.sin(a),cy+u*math.sin(a)+v*math.cos(a))
 polygon('统一环岛 花带土壤',[pos(9+5*math.cos(j*math.tau/64),2.5*math.sin(j*math.tau/64)) for j in range(64)],.93,soil)
 for n in range(150):
  t=random.random()*math.tau;r=math.sqrt(random.random());x,y=pos(9+4.85*r*math.cos(t),2.35*r*math.sin(t));z=.99+random.random()*.16
  for j in range(5):
   ang=j*math.tau/5;xx=x+.09*math.cos(ang);yy=y+.09*math.sin(ang);h=len(vs);vs.extend([(x,y,z-.025),(xx-.075,yy,z),(xx,yy+.07,z+.018),(xx+.075,yy,z)]);fs.append((h,h+1,h+2,h+3))
  for j in range(3):
   ang=random.random()*math.tau;dx=.16*math.cos(ang);dy=.16*math.sin(ang);h=len(lv);lv.extend([(x,y,.94),(x+dx-dy*.3,y+dy+dx*.3,z-.03),(x+dx*1.4,y+dy*1.4,z-.01),(x+dx+dy*.3,y+dy-dx*.3,z-.03)]);lf.append((h,h+1,h+2,h+3))
mesh('统一环岛 合批花瓣',vs,fs,bloom);mesh('统一环岛 合批叶片',lv,lf,leaf)
specs=[]
for name in ['v02 白麻花岗岩','v02 米白石材','v03 会议中心浅米石','v04 平安玫瑰白麻石','道路缘石']:
 specs.append(dict(name=name,asset='granite_tile',res='2k',scale=3,strength=.18,tint=[1,1,1]))
for name in ['v02 深灰屋面','v02 城市地表']:
 specs.append(dict(name=name,asset='concrete_wall_007',res='1k',scale=3,strength=.22,tint=[.72,.74,.75]))
specs.extend([dict(name='花坛真实土壤',asset='brown_mud_03',res='1k',scale=2,strength=.45,tint=[1,1,1]),dict(name='v02 草地',asset='aerial_grass_rock',res='2k',scale=5,strength=.22,tint=[.76,.9,.62])])
for spec in specs:
 m=bpy.data.materials.get(spec['name'])
 if not m:continue
 m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs['Surface']);uv=n.new('ShaderNodeUVMap');uv.uv_map='RealWorldPBR'
 for channel,socket in [('diff','Base Color'),('rough','Roughness'),('nor_gl',None)]:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'纹理'/f"{spec['asset']}_{channel}_{spec['res']}.jpg"),check_existing=True);l.new(uv.outputs[0],tex.inputs['Vector'])
  if channel!='diff':tex.image.colorspace_settings.name='Non-Color'
  if socket:l.new(tex.outputs['Color'],bs.inputs[socket])
  else:
   normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=spec['strength'];l.new(tex.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs[0],bs.inputs['Normal'])
 m['texture_repeat_metres']=spec['scale'];m['asset_source']='https://polyhaven.com/a/'+spec['asset'];m['asset_license']='CC0'
mapping={v['name']:v for v in specs};mapping.update({'滨江浅灰石材':{'scale':3}})
for o in s.objects:
 if o.type!='MESH' or not any(m and m.name in mapping for m in o.data.materials):continue
 if o.data.users>1:o.data=o.data.copy()
 uv=o.data.uv_layers.get('RealWorldPBR') or o.data.uv_layers.new(name='RealWorldPBR')
 for p in o.data.polygons:
  m=o.data.materials[p.material_index]
  if m.name not in mapping:continue
  scale=mapping[m.name]['scale'];normal=o.matrix_world.to_3x3()@p.normal;axis=max(range(3),key=lambda k:abs(normal[k]));u,v=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[u]/scale,co[v]/scale)
(R/'网页漫游/assets/material-bindings.json').write_text(json.dumps(specs,ensure_ascii=False),encoding='utf8')
(R/'制作资料/环岛定位验证.json').write_text(json.dumps({'bridge_center':[cx,cy],'flowerbed_center':[cx,cy],'offset_metres':0,'source':'OSM 48876367','planting':'reference-inspired approximate seasonal layout'}),encoding='utf8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);print('ISLAND_MATERIALS_SAVED',cx,cy,len(specs))
