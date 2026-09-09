"""Export browser tiles from the existing source. Never save staging geometry over source."""
import bpy,math,json,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(bpy.data.filepath).parent;OUT=ROOT/'网页漫游/assets';OUT.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
# Fit all three towers within the saved detail camera, not a cropped inspection shot.
cam=bpy.data.objects['三座超高层建筑'];corners=[]
for o in s.objects:
 if o.get('osm_id') in ['165792123','10691100','376075961']:corners.extend([o.matrix_world@Vector(v) for v in o.bound_box])
for k in range(50):
 uv=[world_to_camera_view(s,cam,p) for p in corners]
 if all(.06<p.x<.94 and .06<p.y<.94 and p.z>0 for p in uv):break
 cam.data.lens*=.95
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
start=time.time();deps=bpy.context.evaluated_depsgraph_get();buckets={};trees=[];colliders=[]
def bucket(key,mat):
 if key not in buckets:buckets[key]=[[],[],mat,[],[]]
 return buckets[key]
source=list(s.objects)
for oi,o in enumerate(source):
 if o.get('web_separate_character'):continue
 if o.hide_render or o.type not in ['MESH','CURVE','FONT']:continue
 if o.name.startswith('树冠'):
  trees.append(dict(p=[o.location.x,o.location.z,-o.location.y],s=[o.scale.x,o.scale.z,o.scale.y],ry=-o.rotation_euler.z));continue
 if o.name.startswith(('树干','路灯光源','点光','球面灯','航空障碍','窗灯')):continue
 if o.name=='地面':continue
 # Tiny emissive bulbs / repeated point fixtures are omitted from daylight web LOD.
 if max(o.dimensions)<.8:continue
 ev=o.evaluated_get(deps);me=ev.to_mesh()
 if not me:continue
 if not me.vertices:ev.to_mesh_clear();continue
 coords=[o.matrix_world@v.co for v in me.vertices]
 centre=sum(coords,Vector())/len(coords);tx=math.floor(centre.x/250);ty=math.floor(centre.y/250)
 # Long roads and river remain independent common tile; other geometry spatially chunked.
 tile='ground' if max(o.dimensions.x,o.dimensions.y)>600 else f'{tx}_{ty}'
 lookup={}
 for poly in me.polygons:
  mat=me.materials[poly.material_index] if len(me.materials)>poly.material_index else None
  mk=mat.name if mat else 'default';key=(tile,mk);v,f,m,uvs,smooth=bucket(key,mat)
  local=lookup.setdefault(key,{})
  face=[]
  for index in poly.vertices:
   if index not in local:local[index]=len(v);v.append(tuple(coords[index]))
   face.append(local[index])
  f.append(face)
  layer=me.uv_layers.get('RealWorldPBR')
  uvs.extend([tuple(layer.data[i].uv) if layer else (0,0) for i in poly.loop_indices])
  smooth.append(poly.use_smooth)
 if o.get('osm_id') and not o.name.endswith('立面分格') and o.dimensions.z>4:
  bb=[o.matrix_world@Vector(v) for v in o.bound_box]
  colliders.append(dict(name=o.name,min=[min(p.x for p in bb),min(p.z for p in bb),-max(p.y for p in bb)],max=[max(p.x for p in bb),max(p.z for p in bb),-min(p.y for p in bb)]))
 ev.to_mesh_clear()
 if oi%2000==0:print('GATHER',oi,len(buckets),flush=True)
print('GATHERED',len(buckets),len(trees),time.time()-start,flush=True)
# Imported character meshes may remain selected in the source scene. Clear them
# before entering staging so glTF never repeats the avatar in every city tile.
for ob in s.objects:ob.select_set(False)
staging=bpy.data.scenes.new('WEB_EXPORT_ONLY');bpy.context.window.scene=staging
tileobs={}
for (tile,mk),(verts,faces,mat,uvs,smooth) in buckets.items():
 me=bpy.data.meshes.new(tile+'_'+mk);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(tile+'_'+mk,me);staging.collection.objects.link(ob)
 if mat and mat.get('texture_repeat_metres'):
  uv=me.uv_layers.new(name='RealWorldPBR')
  for i,co in enumerate(uvs):uv.data[i].uv=co
 for p,flag in zip(me.polygons,smooth):p.use_smooth=flag
 if mat:me.materials.append(mat)
 tileobs.setdefault(tile,[]).append(ob)
buckets.clear()
args=dict(export_format='GLB',export_image_format='NONE',use_selection=True,export_yup=True,export_cameras=False,export_lights=False,export_extras=False)
if 'use_active_scene' in bpy.ops.export_scene.gltf.get_rna_type().properties:args['use_active_scene']=True
manifest=[]
for i,(tile,obs) in enumerate(tileobs.items()):
 for o in staging.objects:o.select_set(False)
 for o in obs:o.select_set(True)
 path=OUT/(tile+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),**args)
 manifest.append(dict(id=tile,file=path.name,bytes=path.stat().st_size,center=None if tile=='ground' else [int(tile.split('_')[0])*250+125,0,-int(tile.split('_')[1])*250-125]))
 print('TILE',i,len(tileobs),tile,flush=True)
# Shared low-detail tree: retain branches, sample every twelfth leaf; one GPU-instanced asset.
tree_source=next(o for o in source if o.name.startswith('树冠'));src=tree_source.data
full_tree=bool(tree_source.get('full_tree'))
verts=[];faces=[];idx=[];tree_uvs=[]
for i,poly in enumerate(src.polygons):
 if full_tree:
  if poly.material_index==1 and (i//4)%3:continue
 elif poly.material_index!=4 and i%12:continue
 k=len(verts);verts.extend([tuple(src.vertices[v].co) for v in poly.vertices]);faces.append(tuple(range(k,k+len(poly.vertices))));idx.append(poly.material_index)
 tree_uvs.extend([tuple(src.uv_layers.active.data[li].uv) if src.uv_layers.active else (0,0) for li in poly.loop_indices])
me=bpy.data.meshes.new('tree_LOD');me.from_pydata(verts,[],faces);me.update()
if full_tree:
 uv=me.uv_layers.new(name='UVMap')
 for i,co in enumerate(tree_uvs):uv.data[i].uv=co
for m in src.materials:me.materials.append(m)
for p,i in zip(me.polygons,idx):p.material_index=i
ob=bpy.data.objects.new('tree_LOD',me);staging.collection.objects.link(ob)
for o in staging.objects:o.select_set(False)
ob.select_set(True);bpy.ops.export_scene.gltf(filepath=str(OUT/'tree.glb'),**(args|{'export_image_format':'AUTO'}))
(OUT/'manifest.json').write_text(json.dumps(dict(tiles=manifest,trees=trees,colliders=colliders,source=str(ROOT/'上海陆家嘴.blend'),coordinate='X east Y up Z south',height_verified=True),ensure_ascii=False),encoding='utf-8')
print('WEB_EXPORT_DONE',len(manifest),sum(x['bytes'] for x in manifest),time.time()-start,flush=True)
