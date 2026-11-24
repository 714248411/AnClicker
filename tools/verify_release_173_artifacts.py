import sys,json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'artifacts/release/v1.7.3'
manifest=json.loads((base/'release-manifest.json').read_text())
for asset in manifest['assets']:
 path=base/asset['path']; h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 assert h.hexdigest()==asset['sha256']
 if 'DaiMa' in path.name:
  with zipfile.ZipFile(path) as z:
   for entry in z.namelist():
    rel=Path(*Path(entry).parts[1:]);assert z.read(entry)==(ROOT/rel).read_bytes(),str(rel)
    assert not any(p in {'.private','data','.local','.venv-build','__pycache__'} for p in rel.parts),str(rel)
results=json.loads((ROOT/'artifacts/validation/v1.7.3/regressions.json').read_text())
assert len(results)==46 and all(x['returncode']==0 for x in results)
assert json.loads((ROOT/'artifacts/validation/v1.7.3/smoke-passed.json').read_text())['passed']
print('PASS final artifact hashes, source consistency and release gates')
