import bpy,math
from pathlib import Path
ROOT=Path(bpy.data.filepath).parent
s=bpy.context.scene
bpy.context.preferences.view.language='en_US'
specs={'v02 草地':('aerial_grass_rock',8.0,.3)}
for name,(asset,metres,strength) in specs.items():
 m=bpy.data.materials.get(name)
 if not m:continue
 m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Metallic'].default_value=0
 uv=n.new('ShaderNodeUVMap');uv.uv_map='RealWorldPBR'
 for channel,socket in [('diff','Base Color'),('rough','Roughness'),('nor_gl',None)]:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'纹理'/f'{asset}_{channel}_2k.jpg'),check_existing=True)
  if channel!='diff':tex.image.colorspace_settings.name='Non-Color'
  l.new(uv.outputs['UV'],tex.inputs['Vector'])
  if socket:l.new(tex.outputs['Color'],bs.inputs[socket])
  else:
   normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=strength;l.new(tex.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],bs.inputs['Normal'])
 m['asset_source']='https://polyhaven.com/a/'+asset;m['asset_license']='CC0';m['texture_repeat_metres']=metres
count=0
for o in list(s.objects):
 if o.type!='MESH' or not any(m and m.name in specs for m in o.data.materials):continue
 if o.data.users>1:o.data=o.data.copy()
 me=o.data;uv=me.uv_layers.get('RealWorldPBR') or me.uv_layers.new(name='RealWorldPBR')
 normalmatrix=o.matrix_world.to_3x3().inverted().transposed()
 for p in me.polygons:
  mat=me.materials[p.material_index] if p.material_index<len(me.materials) else None
  if not mat or mat.name not in specs:continue
  scale=specs[mat.name][1];normal=normalmatrix@p.normal;axis=max(range(3),key=lambda i:abs(normal[i]));a,b=[i for i in range(3) if i!=axis]
  for li in p.loop_indices:
   co=o.matrix_world@me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[a]/scale,co[b]/scale)
 count+=1

bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('GRASS_SAVED',count)
