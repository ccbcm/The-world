from pathlib import Path
import requests,json
out=Path(__file__).resolve().parents[1]/'reference'
out.mkdir(exist_ok=True)
query='''[out:json][timeout:45];(way[building](31.234,121.487,31.246,121.506);way[highway](31.234,121.487,31.246,121.506);way[natural=water](31.230,121.480,31.250,121.510);relation[natural=water](31.230,121.480,31.250,121.510););out geom;'''
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
    try:
        r=requests.post(endpoint,data={'data':query},timeout=55);r.raise_for_status();data=r.json()
        (out/'osm.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        print('OK',endpoint,len(data['elements']),flush=True)
        for e in data['elements']:
            t=e.get('tags',{})
            if t.get('building') and t.get('name'): print(e['id'],json.dumps(t,ensure_ascii=True))
        break
    except Exception as e: print(type(e).__name__,str(e)[:250],flush=True)
