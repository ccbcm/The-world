import json
from pathlib import Path
from shapely.geometry import Point,Polygon
from shapely import make_valid,constrained_delaunay_triangles
R=Path(__file__).resolve().parents[1];data=json.loads((R/'草坪面索引.json').read_text(encoding='utf8'));cut=Point(67.85471503142614,-191.68563288241953).buffer(44,quad_segs=64);items=[]
for f in data:
 g=make_valid(Polygon(f['points']))
 if not g.intersects(cut):continue
 remaining=g.difference(cut);tris=constrained_delaunay_triangles(remaining)
 items.append({'name':f['name'],'polygon':f['polygon'],'z':f['z'],'triangles':[list(t.exterior.coords)[:3] for t in tris.geoms]})
(R/'草坪修正.json').write_text(json.dumps(items,ensure_ascii=False),encoding='utf8');print('CLIPPED_FACES',len(items))
