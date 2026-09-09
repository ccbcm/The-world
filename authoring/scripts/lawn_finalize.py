import bpy
from pathlib import Path
R=Path(bpy.data.filepath).parent
m=bpy.data.materials['v02 草地'];n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Roughness'].default_value=.96
uv=n.new('ShaderNodeUVMap');uv.uv_map='RealWorldPBR';t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(R/'纹理/eztree_grass.jpg'),check_existing=True);l.new(uv.outputs['UV'],t.inputs['Vector']);l.new(t.outputs['Color'],bs.inputs['Base Color'])
m['asset_source']='https://github.com/dgreenheck/ez-tree';m['asset_license']='MIT';m['texture_repeat_metres']=8
root=bpy.data.objects['Vita 控制根 · 身高1.60m'];root.location.z-=.435
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
