import xml.etree.ElementTree as ET,json,math
from pathlib import Path
p=Path(__file__).resolve().parents[1]
r=ET.parse(p/'reference/osm.xml').getroot()
nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in r.findall('node')}
ways=[]
for w in r.findall('way'):
 t={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')}
 pts=[nodes[n.attrib['ref']] for n in w.findall('nd') if n.attrib['ref'] in nodes]
 if not pts:continue
 ways.append(dict(id=w.attrib['id'],tags=t,points=pts))
 if t.get('building') or t.get('waterway') or t.get('natural')=='water':
  print(w.attrib['id'],json.dumps(t,ensure_ascii=True), 'center', [round(sum(x[i] for x in pts)/len(pts),6) for i in (0,1)])
(p/'reference/map_features.json').write_text(json.dumps(ways,ensure_ascii=False),encoding='utf-8')
print('WAYS',len(ways))
