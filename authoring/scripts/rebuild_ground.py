import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,triangulate
from shapely import make_valid,constrained_delaunay_triangles
R=Path(__file__).resolve().parents[1]
features=json.loads((R/'reference/map_expanded.json').read_text(encoding='utf8'))
def xy(p):return ((p[0]-121.49536)*111320*math.cos(math.radians(31.24188)),(p[1]-31.24188)*110900)
buildings=unary_union([make_valid(Polygon([xy(p) for p in f['points']])) for f in features if f['tags'].get('building') and len(f['points'])>3]).buffer(.6)
limit=Point(0,0).buffer(1450,quad_segs=80);roads=[];paths=[];lines=[]
for f in features:
 t=f['tags'];h=t.get('highway','');base=h.removesuffix('_link')
 if len(f['points'])<2 or not h or t.get('indoor')=='yes' or t.get('tunnel') or t.get('bridge')=='yes' or float(t.get('layer','0'))!=0 or t.get('access') in ['no','private']:continue
 l=LineString([xy(p) for p in f['points']]).simplify(.4)
 if base in ['primary','secondary','tertiary','residential','unclassified','service','trunk']:
  w={'primary':11,'secondary':10,'tertiary':8,'residential':6,'unclassified':6,'service':4.5,'trunk':13}[base]
  try:w=float(t['width']) if 'width' in t else float(t['lanes'])*3.2+.4 if 'lanes' in t else w
  except:pass
  w=max(4,min(22,w));roads.append(l.buffer(w/2,quad_segs=8));lines.append((l,w))
 elif h in ['footway','pedestrian','path']:
  paths.append(l.buffer(1.65,quad_segs=6))
road=unary_union(roads).intersection(limit).difference(buildings)
# Remove tiny slivers, then tessellate one coherent carriageway surface.
road=road.buffer(.15).buffer(-.15).simplify(.12,preserve_topology=True).difference(buildings)
island=Point(67.85471503142614,-191.68563288241953)
road=road.union(island.buffer(40,quad_segs=64)).difference(island.buffer(20.1,quad_segs=64)).difference(buildings)
walk=unary_union(paths).union(road.buffer(1.8).difference(road)).intersection(limit).difference(buildings).difference(road.buffer(.04))
walk=walk.difference(island.buffer(40.1,quad_segs=64))
def polys(g):
 if g.geom_type=='Polygon':yield g
 elif hasattr(g,'geoms'):
  for q in g.geoms:yield from polys(q)
def tris(g):return [list(t.exterior.coords)[:3] for p in polys(g) for t in constrained_delaunay_triangles(p).geoms]
# Keep center markings only on broad roads, clipped away from all intersections.
ends=unary_union([Point(p).buffer(13) for l,w in lines for p in [l.coords[0],l.coords[-1]]]);marks=[]
for l,w in lines:
 if w<7:continue
 for d in range(5,int(l.length)-5,12):
  segment=LineString([l.interpolate(d),l.interpolate(d+4)]).buffer(.075,cap_style=2)
  if not segment.intersects(ends) and road.covers(segment):marks.extend(tris(segment))
(R/'道路重铺.json').write_text(json.dumps({'roads':tris(road),'walks':tris(walk),'marks':marks,'source_ways':len(lines),'road_area':road.area,'building_overlap':road.intersection(buildings).area,'tessellation_missing_area':abs(road.area-sum(Polygon(t).area for t in tris(road)))}),encoding='utf8')
print('ROAD_PLAN',len(lines),road.area,'overlap',road.intersection(buildings).area)

