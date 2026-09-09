"""Incremental PBR pass on the saved city. Preserve geometry and existing edits."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(bpy.data.filepath).parent
s=bpy.context.scene
bpy.context.preferences.view.language='en_US'
specs={'道路沥青':('asphalt_02',3.0,.55),'滨江浅灰石材':('granite_tile',3.0,.35),'v02 城市地表':('concrete_pavement',4.0,.4)}
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
# Real local environment for reflections; retain the existing analytic sky for camera rays.
w=s.world;w.use_nodes=True;n=w.node_tree.nodes;l=w.node_tree.links
out=next(nod for nod in n if nod.type=='OUTPUT_WORLD')
old=out.inputs['Surface'].links[0].from_socket
env=n.new('ShaderNodeTexEnvironment');env.name='上海滨江实拍 HDRI';env.image=bpy.data.images.load(str(ROOT/'纹理/shanghai_riverside_4k.hdr'),check_existing=True)
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.65;l.new(env.outputs['Color'],bg.inputs['Color'])
lp=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);l.new(bg.outputs[0],mix.inputs[1]);l.new(old,mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
w['environment_license']='CC0 https://polyhaven.com/a/shanghai_riverside'
sun=bpy.data.objects.get('白天太阳')
if sun:sun.hide_render=False;sun.data.energy=2;sun.data.angle=math.radians(2)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.use_scene_world=True;area.spaces.active.shading.use_scene_lights=True
s['material_pass']='CC0 scanned asphalt, granite paving, concrete; metre-scale UV; Shanghai HDR reflections'
bpy.ops.file.pack_all()
s.render.engine='BLENDER_EEVEE';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
print('PBR_SAVED',count,flush=True)
s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=True;s.cycles.device='GPU'
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
for cam,file in [('陆家嘴全景','实拍材质全景.png'),('三座超高层建筑','三座超高层.png')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(ROOT/'预览'/file);bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['陆家嘴全景'];s.render.engine='BLENDER_EEVEE'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'上海陆家嘴.blend'))
print('PBR_DONE',flush=True)
