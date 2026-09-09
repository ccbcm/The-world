import pathlib,re,json,shutil
R=pathlib.Path(__file__).resolve().parents[1];src=R/'第三方/ez-tree/src/lib';dst=R/'第三方/ez-tree-node';dst.mkdir(exist_ok=True)
three=(R.parent/'网页漫游/vendor/three/build/three.module.js').as_uri()
for p in src.rglob('*'):
 if not p.is_file():continue
 q=dst/p.relative_to(src);q.parent.mkdir(exist_ok=True,parents=True)
 if p.suffix=='.js':
  t=p.read_text(encoding='utf8').replace("from 'three'",'from '+json.dumps(three))
  t=re.sub(r"from '(\.[^']+)'",lambda m:"from '"+m[1]+("' with { type: 'json' }" if m[1].endswith('.json') else ".js'" if not m[1].endswith('.js') else "'"),t)
  q.write_text(t,encoding='utf8')
 else:shutil.copy2(p,q)
(dst/'package.json').write_text('{"type":"module"}')
shutil.copy2(R/'第三方/ez-tree/LICENSE',dst/'LICENSE')
print('NODE_ADAPTER_READY')
