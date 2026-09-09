import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(bpy.data.filepath).parent
f=json.loads((ROOT/'制作资料/reference/map_features.json').read_text(encoding='utf-8'))
rp=next(x['points'] for x in f if x['tags'].get('water')=='river')[59:83]
pts=[Vector(((a-121.49536)*111320*math.cos(math.radians(31.24188)),(b-31.24188)*110900,0)) for a,b in rp]
vs=[]
for i,p in enumerate(pts):
 d=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();n=Vector((-d.y,d.x,0))
 for off in [.9,9.5]:q=p+n*off;vs.append((q.x,q.y,.78))
faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)]
me=bpy.data.meshes.new('滨江石材步道连续铺装');me.from_pydata(vs,[],faces);me.materials.append(bpy.data.materials['滨江浅灰石材']);uv=me.uv_layers.new(name='RealWorldPBR')
for p in me.polygons:
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)
ob=bpy.data.objects.new('滨江石材步道连续铺装',me);bpy.data.collections['17 滨江实景细部 · 地图岸线'].objects.link(ob);ob['accuracy']='Mapped edge; 8.6m walking-strip width is a visual approximation.'
s=bpy.context.scene;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.camera=bpy.data.objects['滨江材质检查'];s.render.filepath=str(ROOT/'预览/滨江材质近景.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
