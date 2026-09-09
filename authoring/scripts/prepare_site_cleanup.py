import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union,triangulate
from shapely import make_valid
R=Path(__file__).resolve().parents[1]
features=json.loads((R/'reference/map_expanded.json').read_text(encoding='utf8'))
audit=json.loads((R/'待修正场景审计.json').read_text(encoding='utf8'))
def xy(p):return ((p[0]-121.49536)*111320*math.cos(math.radians(31.24188)),(p[1]-31.24188)*110900)
def poly(f):
 try:return make_valid(Polygon([xy(p) for p in f['points']]))
 except:return Polygon()
build=unary_union([poly(f) for f in features if (f['tags'].get('building') or f['tags'].get('building:part')) and float(f['tags'].get('min_height',0))<4])
green=unary_union([poly(f) for f in features if f['tags'].get('landuse') in ['grass','forest'] or f['tags'].get('leisure') in ['garden','park'] or f['tags'].get('natural') in ['wood','scrub']])
limit=Point(0,0).buffer(1450,quad_segs=64)
groups={'road':[],'walk':[],'walk_bridge':[]};lines=[]
for f in features:
 t=f['tags'];hw=t.get('highway')
 if hw not in ['primary','secondary','tertiary','residential','service','unclassified','pedestrian','footway','cycleway']:continue
 if t.get('tunnel')=='yes' or t.get('location')=='underground' or len(f['points'])<2:continue
 line=LineString([xy(p) for p in f['points']]);ped=hw in ['pedestrian','footway','cycleway'];bridge=t.get('bridge')=='yes'
 if not line.intersects(limit):continue
 width={'primary':6.4,'secondary':5.2,'tertiary':4.4,'residential':3.2,'service':2.5,'unclassified':3.2,'pedestrian':3,'footway':1.6,'cycleway':1.8}[hw]
 try:
  if 'width' in t:width=min(18,max(.8,float(t['width'])/2))
  elif 'lanes' in t and not ped:width=min(16,max(2,float(t['lanes'])*1.65))
 except:pass
 key='walk_bridge' if bridge else 'walk' if ped else 'road'
 shape=line.buffer(width,quad_segs=4,join_style=1).intersection(limit)
 if not bridge:shape=shape.difference(build.buffer(.4))
 groups[key].append(shape)
 if not ped and t.get('name'):lines.append((line,width,t))
unions={k:unary_union(v) for k,v in groups.items()}
unions['walk']=unions['walk'].difference(unions['road'].buffer(.08))
def polygons(g):
 if g.geom_type=='Polygon':yield g
 elif hasattr(g,'geoms'):
  for x in g.geoms:yield from polygons(x)
roads=[]
for k,g in unions.items():
 tris=[]
 for p in polygons(g):
  if p.area<.3:continue
  for t in triangulate(p):
   if p.covers(t):tris.append(list(t.exterior.coords)[:3])
 roads.append(dict(name=k,z=7 if k.endswith('bridge') else .72 if k=='walk' else .69,triangles=tris))
exclusion=build.buffer(3.5).union(unions['road'].buffer(3)).union(unions['walk'].buffer(2.1)).union(Point(0,0).buffer(78))
allowed=green.buffer(-2).difference(exclusion);keep=[];removed=[];pts=[]
for o in audit:
 if not o['name'].startswith('树冠'):continue
 x,y=o['loc'][:2];p=Point(x,y)
 if not allowed.covers(p) or any((x-a)**2+(y-b)**2<42.25 for a,b in pts):removed.append(o['name'])
 else:keep.append(o['name']);pts.append((x,y))
result=dict(roads=roads,keep_trees=keep,remove_trees=removed,tree_locations=pts,tree_policy='Mapped green areas only; >=6.5m spacing, road and building clearance. Exact tree surveying unavailable.')
(R/'场地清理方案.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
print('TREES',len(keep),'removed',len(removed),'ROAD_TRIANGLES',[(r['name'],len(r['triangles'])) for r in roads])
