import bpy,shutil,json
from pathlib import Path
from mathutils import Vector
R=Path(bpy.data.filepath).parent
for c in list(bpy.data.collections):
 if c.name=='20 人物 · Vita 可编辑骨骼':
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
c=bpy.data.collections.new('20 人物 · Vita 可编辑骨骼');bpy.context.scene.collection.children.link(c)
asset=R/'网页漫游/assets/character/Vita.vrm';target=R/'制作资料/第三方/Vita.glb';shutil.copyfile(asset,target)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(target));added=set(bpy.data.objects)-before
for o in added:
 for parent in list(o.users_collection):parent.objects.unlink(o)
 c.objects.link(o);o['web_separate_character']=True
root=bpy.data.objects.new('Vita 控制根 · 身高1.60m',None);c.objects.link(root)
for o in added:
 if o.parent not in added:o.parent=root
bpy.context.view_layer.update();coords=[o.matrix_world@Vector(p) for o in added if o.type=='MESH' for p in o.bound_box]
low=min(p.z for p in coords);height=max(p.z for p in coords)-low;root.scale=(1.6/height,)*3;root.location=(-180,-148,.8-low*1.6/height)
root['height_m']=1.6;root['license']='CC0';root['source']='https://github.com/madjin/vrm-samples/blob/master/vroid/beta/Vita.vrm';root['web_separate_character']=True
bpy.ops.file.pack_all();bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('CHARACTER_SAVED',len(added),height)
