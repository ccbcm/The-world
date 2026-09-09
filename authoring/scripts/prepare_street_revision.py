import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,triangulate
from shapely import make_valid
R=Path(__file__).resolve().parents[1];features=json.loads((R/'reference/map_expanded.json').read_text(encoding='utf8'))
def xy(p):return ((p[0]-121.49536)*111320*math.cos(math.radians(31.24188)),(p[1]-31.24188)*110900)
limit=Point(0,0).buffer(1450,quad_segs=64)
buildings=unary_union([make_valid(Polygon([xy(p) for p in f['points']])) for f in features if f['tags'].get('building') and len(f['points'])>3])
roads=[];walks=[];bridges=[];steps=[];omitted=[]
for f in features:
 t=f['tags'];hw=t.get('highway','');base=hw.removesuffix('_link')
 if not hw or len(f['points'])<2:continue
 if t.get('indoor')=='yes' or t.get('tunnel') or t.get('location')=='underground' or float(t.get('layer','0'))<0 or t.get('access')=='no':omitted.append(f['id']);continue
 line=LineString([xy(p) for p in f['points']])
 if not line.intersects(limit):continue
 if hw=='steps':steps.append({'id':f['id'],'points':list(line.coords),'tags':t});continue
 ped=hw in ['pedestrian','footway','cycleway','path']
 if not ped and base not in ['primary','secondary','tertiary','residential','service','unclassified','trunk']:continue
 width=3.3 if ped else {'primary':12.8,'secondary':10.4,'tertiary':8.8,'residential':6.4,'service':5,'unclassified':6.4,'trunk':14}[base]
 try:
  if 'width' in t:width=float(t['width'])
  elif 'lanes' in t and not ped:width=float(t['lanes'])*3.25+.5
 except:pass
 width=max(1.8,min(width,32));bridge=t.get('bridge')=='yes'
 if bridge and ped:width=7 if f['id']=='48876367' else 4.6
 entry={'id':f['id'],'points':list(line.coords),'width':width,'tags':t}
 if bridge and ped:bridges.append(entry)
 elif ped:walks.append(entry)
 else:roads.append(entry)
def shape(entries):return unary_union([LineString(e['points']).buffer(e['width']/2,quad_segs=6,join_style=1) for e in entries]).intersection(limit)
road=shape(roads);walk=shape(walks).difference(road.buffer(.05))
def polys(g):
 if g.geom_type=='Polygon':yield g
 elif hasattr(g,'geoms'):
  for q in g.geoms:yield from polys(q)
def tris(g):return [list(t.exterior.coords)[:3] for p in polys(g) for t in triangulate(p) if p.covers(t) and t.area>.01]
# Mark lanes only away from intersections: no dashed lines crossing a junction arbitrarily.
ends=[Point(e['points'][i]) for e in roads for i in [0,-1]]
junctions=unary_union([p.buffer(11) for p in ends]);markings=[];curbs=[];lamps=[]
for e in roads:
 line=LineString(e['points']);t=e['tags'];length=line.length
 if length<10:continue
 lanes=max(1,round((e['width']-.5)/3.25))
 if lanes>1:
  for lane in range(1,lanes):
   off=-e['width']/2+.25+lane*3.25
   for d in range(4,int(length)-4,9):
    mid=line.interpolate(d+1.5)
    if junctions.covers(mid):continue
    a=line.interpolate(d);b=line.interpolate(min(d+3,length));dx,dy=b.x-a.x,b.y-a.y;ll=math.hypot(dx,dy)
    if ll<.2:continue
    markings.append([[a.x-dy/ll*off,a.y+dx/ll*off],[b.x-dy/ll*off,b.y+dx/ll*off]])
 if t.get('name') and not t.get('highway','').endswith('_link'):
  for d in range(18,int(length)-12,32):
   a=line.interpolate(d);b=line.interpolate(min(d+.5,length));dx,dy=b.x-a.x,b.y-a.y;ll=math.hypot(dx,dy)
   if ll<.01 or junctions.covers(a):continue
   for side in [-1,1]:
    q=Point(a.x-side*dy/ll*(e['width']/2+1),a.y+side*dx/ll*(e['width']/2+1))
    if q.distance(Point(67,-192))<72:continue
    if road.covers(q) or buildings.buffer(1).covers(q):continue
    if all(q.distance(Point(p))>18 for p in lamps):lamps.append([q.x,q.y])
for p in polys(road):
 for ring in [p.exterior,*p.interiors]:
  # Use the continuous union boundary rather than overlapping edge lines at junctions.
  if ring.length>8:curbs.append(list(ring.simplify(.12).coords))
bridge_shape=shape(bridges);stairs=[]
for e in steps:
 p=e['points'];d0=bridge_shape.distance(Point(p[0]));d1=bridge_shape.distance(Point(p[-1]))
 if min(d0,d1)>6 or abs(d0-d1)<2:continue
 if d1<d0:p=p[::-1]
 stairs.append(dict(id=e['id'],points=p,width=3.2,escalator=e['tags'].get('conveying')=='yes'))
result={'road_triangles':tris(road),'walk_triangles':tris(walk),'bridges':bridges,'stairs':stairs,'markings':markings,'curbs':curbs,'lamps':lamps,'omitted_indoor_underground':omitted,'counts':{'road_ways':len(roads),'walk_ways':len(walks),'bridges':len(bridges),'stairs':len(stairs),'lamps':len(lamps),'markings':len(markings)}}
(R/'道路分层修正方案.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8');print(result['counts'])
