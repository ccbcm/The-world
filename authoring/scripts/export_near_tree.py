import bpy
from pathlib import Path
R=Path(bpy.data.filepath).parent;source=next(o for o in bpy.context.scene.objects if o.name.startswith('树冠'))
for o in bpy.context.scene.objects:o.select_set(False)
scene=bpy.data.scenes.new('TREE_EXPORT_ONLY');bpy.context.window.scene=scene
o=bpy.data.objects.new('Oak full canopy',source.data.copy());scene.collection.objects.link(o);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'网页漫游/assets/tree_near.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_cameras=False,export_lights=False)
print('TREE_FULL_EXPORTED')
