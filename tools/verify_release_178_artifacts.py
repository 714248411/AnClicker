import sys,json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'artifacts/release/v1.7.8'
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
results=json.loads((ROOT/'artifacts/validation/v1.7.8/regressions.json').read_text())
assert len(results)==72 and all(x['returncode']==0 for x in results)
assert json.loads((ROOT/'artifacts/validation/v1.7.8/smoke-passed.json').read_text())['passed']
print('PASS final artifact hashes, source consistency and release gates')

with zipfile.ZipFile(base/'public/AnClicker-v1.7.8-win.zip') as binary, zipfile.ZipFile(base/'public/AnClicker-v1.7.8-win-DaiMa.zip') as source:
 config=json.loads(binary.read('AnClicker/models/dual_model.json'))
 assert all(config.get(k) is True for k in ('embedding_enabled','correction_memory_enabled','serial_models'))
 identity=json.loads(binary.read('AnClicker/ai-build-manifest.json'))
 for name,expected in identity['sources'].items():assert hashlib.sha256(source.read('AnClicker-v1.7.8/'+name)).hexdigest()==expected,name
 for name,expected in identity['resources'].items():assert hashlib.sha256(binary.read('AnClicker/'+name)).hexdigest()==expected,name
 assert binary.read('AnClicker/models/correction_cases.json')==source.read('AnClicker-v1.7.8/models/correction_cases.json')
 assert not any('/.dual-runtime/' in n or n.startswith('AnClicker/data/') for n in binary.namelist())
print('PASS portable AI resources, enabled switches and binary/source identity')

with zipfile.ZipFile(base/'public/AnClicker-v1.7.8-win.zip') as z:
 for name in ('ch_PP-OCRv4_det_infer.onnx', 'ch_ppocr_mobile_v2.0_cls_infer.onnx', 'ch_PP-OCRv4_rec_infer.onnx'):
  entry='AnClicker/ocr_models/rapidocr/'+name
  assert z.getinfo(entry).file_size > 100000
  assert hashlib.sha256(z.read(entry)).digest()==hashlib.sha256((ROOT/'.local/models/rapidocr'/name).read_bytes()).digest()
 for name in ('runtime/crawl4ai/python/python.exe','runtime/crawl4ai/python/python310.dll','runtime/crawl4ai/python/Lib/site-packages/crawl4ai/__init__.py','integrations/crawl4ai/extraction.py','integrations/crawl4ai/browser.js','integrations/yingdao/src/ac-region.js'):
  assert z.getinfo('AnClicker/'+name).file_size > 0
 assert not any(n.endswith('pyvenv.cfg') or '/litellm/proxy/_experimental/' in n for n in z.namelist())
print('PASS offline OCR model hashes and portable extraction runtime')
