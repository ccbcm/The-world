import bpy
from mathutils import Vector
from pathlib import Path
s=bpy.context.scene;dest=Path(bpy.data.filepath).parent
o=bpy.data.objects['三座超高层建筑'];o.location=(-120,250,620);o.rotation_euler=(Vector((625,-607,280))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=42
s.camera=o;s.render.engine='CYCLES';s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
bpy.data.objects['白天太阳'].hide_render=True
s.render.filepath=str(dest/'预览/三座超高层.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE';bpy.data.objects['白天太阳'].hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
