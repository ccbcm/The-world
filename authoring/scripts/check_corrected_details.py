import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(bpy.data.filepath).parent;s=bpy.context.scene
walkmat=bpy.data.materials['v02 城市地表'].copy();walkmat.name='人行浅色铺装';walkmat['texture_repeat_metres']=3
for o in s.objects:
 if o.name.startswith('连续路网 walk'):o.data.materials.clear();o.data.materials.append(walkmat)
# Use geometry ray intersections at sign height to place text just outside the actual facade.
deps=bpy.context.evaluated_depsgraph_get();signchecks=[]
for o in [x for x in s.objects if x.type=='FONT' and x.data.body=='中国平安']:
 centre=Vector((251.3,-38.4,158.5));normal=o.rotation_euler.to_matrix()@Vector((0,0,1));distances=[]
 for ob in bpy.data.collections['04P 平安金融大厦 v04 · 石材柱廊与203m穹顶'].objects:
  if ob.type!='MESH':continue
  inv=ob.matrix_world.inverted();origin=inv@centre;direction=(inv.to_3x3()@normal).normalized()
  hit,co,no,idx=ob.ray_cast(origin,direction,distance=200,depsgraph=deps)
  if hit:
   d=(ob.matrix_world@co-centre).dot(normal)
   if 0<d<55:distances.append(d)
 if distances:o.location=centre+normal*(max(distances)+.28)
 signchecks.append(dict(name=o.name,text=o.data.body,ray_surface=max(distances) if distances else None,position=list(o.location),normal=list(normal)))
(R/'制作资料/标识位置校核.json').write_text(json.dumps(signchecks,ensure_ascii=False,indent=2),encoding='utf8')
cam=bpy.data.objects['金茂轮廓校核'];cam.location=(150,-190,215);cam.rotation_euler=(Vector((576.74,-513.44,215))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=680
data=bpy.data.cameras.new('标识近景校核');signcam=bpy.data.objects.new('标识近景校核',data);s.collection.objects.link(signcam);signcam.location=(180,40,162);signcam.rotation_euler=(Vector((251,-38,158.5))-signcam.location).to_track_quat('-Z','Y').to_euler();data.lens=65;data.clip_end=30000
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.cycles.device='GPU';p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
for ob,file in [(cam,'金茂重建.png'),(signcam,'标识遮挡修正.png')]:s.camera=ob;s.render.filepath=str(R/'预览'/file);bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
