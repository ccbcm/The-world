import bpy,ast,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(bpy.data.filepath).parent;D=R/'制作资料';s=bpy.context.scene
bpy.context.preferences.view.language='en_US'
t=ast.parse((D/'scripts/build_pearl.py').read_text(encoding='utf8'));names={'collection','put','material','mesh','instance','box','cyl','line','extrude','polygon','ring'}
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'helpers','exec'));cache={};COL=None
plan=json.loads((D/'道路分层修正方案.json').read_text(encoding='utf8'))
for o in list(bpy.data.objects):
 if o.name.startswith('连续路网 ') or any(c.name.startswith('21 道路与连廊') for c in o.users_collection):bpy.data.objects.remove(o,do_unlink=True)
collection('21 道路与连廊 · 地面高架分层')
asphalt=bpy.data.materials['道路沥青'];paving=bpy.data.materials['人行浅色铺装'];white=material('道路标线白',(.72,.73,.68),0,.8);steel=material('桥栏杆银灰',(.32,.35,.36),.55,.4)
deckmat=paving.copy();deckmat.name='步行桥面 · 7m';stairmat=paving.copy();stairmat.name='桥接台阶';edge=material('道路缘石',(.36,.37,.34),0,.8)
def uv(o,scale=3):
 layer=o.data.uv_layers.get('RealWorldPBR') or o.data.uv_layers.new(name='RealWorldPBR')
 for p in o.data.polygons:
  for li in p.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co;layer.data[li].uv=(v.x/scale,v.y/scale)
def triangles(name,data,z,mat):
 vs=[];fs=[]
 for tri in data:k=len(vs);vs.extend([(x,y,z) for x,y in tri]);fs.append((k,k+1,k+2))
 ob=mesh(name,vs,fs,mat);uv(ob);return ob
triangles('连续路网 road',plan['road_triangles'],.69,asphalt);triangles('连续路网 walk',plan['walk_triangles'],.72,paving)
# Thin marking geometry is merged for export. Curbs follow the unioned carriageway boundary.
vs=[];fs=[]
for a,b in plan['markings']:
 a=Vector(a);b=Vector(b);u=(b-a).normalized();n=Vector((-u.y,u.x))*.075;k=len(vs)
 vs.extend([(q.x,q.y,.707) for q in [a-n,b-n,b+n,a+n]]);fs.append((k,k+1,k+2,k+3))
mesh('车道分界虚线 · 避让交叉口',vs,fs,white)
for pts in plan['curbs']:line('连续道路缘石',[(x,y,.74) for x,y in pts],.10,edge)
for x,y in plan['lamps']:
 cyl('街灯杆',(x,y,.72),(x,y,8),.09,steel,n=8);box('街灯灯头',(x,y,8),(1.1,.32,.16),white)
def resample(pts,spacing):
 out=[Vector(pts[0])]
 for a,b in zip(pts,pts[1:]):
  a=Vector(a);b=Vector(b);n=max(1,math.ceil((b-a).length/spacing));out.extend([a+(b-a)*i/n for i in range(1,n+1)])
 return out
def ribbon(name,pts,width,zs,mat,thickness=.55):
 p=[Vector(q) for q in pts];closed=(p[0]-p[-1]).length<.05;vs=[];fs=[];sides=[[],[]]
 for i,q in enumerate(p):
  prev=p[i-1] if i else p[-2] if closed else p[0];nxt=p[(i+1)%len(p)] if i<len(p)-1 else p[1] if closed else p[-1]
  u=(nxt-prev).normalized();n=Vector((-u.y,u.x));a=q-n*width/2;b=q+n*width/2
  vs.extend([(a.x,a.y,zs[i]),(b.x,b.y,zs[i]),(a.x,a.y,zs[i]-thickness),(b.x,b.y,zs[i]-thickness)])
  sides[0].append((a.x,a.y,zs[i]));sides[1].append((b.x,b.y,zs[i]))
 for i in range(len(p)-1):
  k=i*4;fs.extend([(k,k+4,k+5,k+1),(k+2,k+3,k+7,k+6),(k,k+2,k+6,k+4),(k+1,k+5,k+7,k+3)])
 ob=mesh(name,vs,fs,mat);uv(ob);ob['walkable']=True;return sides
bridge_paths=[]
for e in plan['bridges']:
 pts=e['points'];width=9.7 if e['id']=='48876367' else e['width'];sides=ribbon('连廊桥面 '+e['id'],pts,width,[7]*len(pts),deckmat)
 for side in sides:
  for h in [.15,.65,1.15]:line('连廊连续扶手',[(x,y,z+h) for x,y,z in side],.045,steel)
  for q in resample(side,3):cyl('连廊栏杆立柱',(q.x,q.y,q.z),(q.x,q.y,q.z+1.15),.035,steel,n=6)
 bridge_paths.append(e)
stairs=[]
for e in plan['stairs']:
 p=resample(e['points'],.30);dist=[0]
 for a,b in zip(p,p[1:]):dist.append(dist[-1]+(b-a).length)
 total=dist[-1]
 if total<3:continue
 z=[7-(7-.72)*d/total for d in dist]
 # The actual visual treads are separate; a continuous collision ramp is generated in the web runtime.
 sides=ribbon('桥接台阶斜结构 '+e['id'],[list(v) for v in p],e['width'],z,stairmat,.35)
 for i,(a,b) in enumerate(zip(p,p[1:])):
  u=(b-a).normalized();normal=Vector((-u.y,u.x));zz=z[i];vs=[(q.x,q.y,zz) for q in [a-normal*e['width']/2,b-normal*e['width']/2,b+normal*e['width']/2,a+normal*e['width']/2]]
  mesh('桥阶踏面',vs,[(0,1,2,3)],paving)
 for side in sides:line('阶梯连续扶手',[(x,y,z+1.05) for x,y,z in side],.045,steel)
 for side in sides:
  for q in resample(side,2):cyl('阶梯扶手柱',(q.x,q.y,q.z),(q.x,q.y,q.z+1.05),.03,steel,n=6)
 stairs.append({'id':e['id'],'points':[[q.x,zz,-q.y] for q,zz in zip(p,z)],'width':e['width']})
(R/'网页漫游/assets/walkways.json').write_text(json.dumps({'stairs':stairs,'bridge_deck_height':7},ensure_ascii=False),encoding='utf8')
cam=bpy.data.objects.get('道路分层实景校核')
if not cam:
 data=bpy.data.cameras.new('道路分层实景校核');cam=bpy.data.objects.new(data.name,data);s.collection.objects.link(cam)
cam.location=(-150,105,245);cam.rotation_euler=(Vector((65,-190,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('STREET_SAVED',plan['counts'],len(stairs))
