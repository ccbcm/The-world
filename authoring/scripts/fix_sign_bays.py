import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(bpy.data.filepath).parent;s=bpy.context.scene
data=json.loads((R/'制作资料/reference/map_expanded.json').read_text(encoding='utf8'))
raw=next(x['points'] for x in data if x['id']=='164958064')
pts=[Vector(((x-121.49536)*111320*math.cos(math.radians(31.24188)),(y-31.24188)*110900)) for x,y in raw]
if (pts[0]-pts[-1]).length<.01:pts.pop()
c=sum(pts,Vector((0,0)))/len(pts)
sg=1 if sum(a.x*b.y-b.x*a.y for a,b in zip(pts,pts[1:]+pts[:1]))>0 else -1
edges=[]
for a,b in zip(pts,pts[1:]+pts[:1]):
 if (b-a).length*.86<35:continue
 u=(b-a).normalized();n=Vector((u.y,-u.x))*sg
 q=c+((a+b)/2-c)*.86
 if (b-a).length>55:q-=u*((b-a).length*.86*.25)
 edges.append((q,u,n))
signs=[o for o in s.objects if o.type=='FONT' and o.data.body=='中国平安']
for o in signs:
 old=o.rotation_euler.to_matrix()@Vector((0,0,1))
 q,u,n=max(edges,key=lambda e:e[2].dot(Vector((old.x,old.y))))
 normal=Vector((n.x,n.y,0));right=Vector((-n.y,n.x,0))
 o.rotation_euler=Matrix((right,Vector((0,0,1)),normal)).transposed().to_euler()
 o.location=(q.x+n.x*.65,q.y+n.y*.65,161);o.data.size=2.5;o.data.align_x='CENTER'
 o['placement_note']='Shifted into side bay clear of original central stone pier'
cam=bpy.data.objects.get('标识近景校核');cam.location=(180,40,163);cam.rotation_euler=(Vector((245,-32,162))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=65
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1000;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.filepath=str(R/'预览/标识遮挡修正.png')
bpy.ops.render.render(write_still=True)
print('SIGN_BAYS_SAVED')
