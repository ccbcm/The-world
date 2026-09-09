import json,math
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union,triangulate
R=Path(__file__).resolve().parents[1]
features=json.loads((R/'reference/map_expanded.json').read_text(encoding='utf-8'))
groups={}
for f in features:
 t=f['tags'];hw=t.get('highway')
 if hw not in ['primary','secondary','tertiary','residential','service','unclassified','pedestrian','footway','cycleway','steps']:continue
 if t.get('tunnel')=='yes' or t.get('location')=='underground':continue
 pts=[((x-121.49536)*111320*math.cos(math.radians(31.24188)),(y-31.24188)*110900) for x,y in f['points']]
 if len(pts)<2:continue
 if min(math.hypot(x,y) for x,y in pts)>1500:continue
 ped=hw in ['pedestrian','footway','cycleway','steps'];width=2.6 if ped else {'primary':10,'secondary':8,'tertiary':6,'service':3}.get(hw,5)
 key=('walk' if ped else 'road')+('_bridge' if t.get('bridge')=='yes' else '')
 groups.setdefault(key,[]).append(LineString(pts).buffer(width,quad_segs=4,join_style=2))
unions={k:unary_union(v) for k,v in groups.items()}
if 'walk' in unions:unions['walk']=unions['walk'].difference(unions['road'])
out=[]
for key,g in unions.items():
 tris=[]
 for poly in getattr(g,'geoms',[g]):
  if poly.area<.1:continue
  for tri in triangulate(poly):
   if poly.covers(tri):tris.append(list(tri.exterior.coords)[:3])
 out.append(dict(name=key,z=7 if 'bridge' in key else .7,triangles=tris))
(R/'reference/expanded_roads_mesh.json').write_text(json.dumps(out),encoding='utf-8')
print({g['name']:len(g['triangles']) for g in out})
