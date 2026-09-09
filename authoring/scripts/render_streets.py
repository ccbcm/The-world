import bpy
from pathlib import Path
R=Path(bpy.data.filepath).parent;s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.render.resolution_x=1280;s.render.resolution_y=900;s.render.resolution_percentage=100
for name,file in [('道路分层实景校核','道路分层校核.png'),('低层建筑实景校核','水族馆实景校核.png'),('环岛低层与道路','环岛低层校核.png')]:
 s.camera=bpy.data.objects[name];s.render.filepath=str(R/'预览'/file);bpy.ops.render.render(write_still=True)
print('RENDER_DONE')
