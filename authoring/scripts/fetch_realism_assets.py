import json,urllib.request,shutil,hashlib
from pathlib import Path
urllib.request.install_opener(urllib.request.build_opener())
urllib.request._opener.addheaders=[('User-Agent','Mozilla/5.0 LujiazuiAssetStudy')]
R=Path(__file__).resolve().parents[2];web=R/'网页漫游';records=[]
def download(url,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(url,timeout=45) as response:path.write_bytes(response.read())
 records.append({'url':url,'file':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for asset in ['concrete_wall_007','brown_mud_03']:
 with urllib.request.urlopen('https://api.polyhaven.com/files/'+asset) as r:files=json.load(r)
 for channel,key in [('diff','Diffuse'),('nor_gl','nor_gl'),('rough','Rough')]:
  target=web/'assets/textures'/f'{asset}_{channel}_1k.jpg';download(files[key]['1k']['jpg']['url'],target);shutil.copy2(target,R/'纹理'/target.name)
download('https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.5.5/lib/three-vrm.module.min.js',web/'vendor/three-vrm/three-vrm.module.min.js')
download('https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.5.5/LICENSE',web/'licenses/three-vrm-MIT.txt')
(R/'制作资料/新增素材来源.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print('ASSETS_DOWNLOADED',len(records))

