import zipfile,os,shutil,json,hashlib
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'artifacts/debug/v173-retest';source=OUT/'source'
archive=ROOT/'artifacts/release/v1.7.3/public/AnClicker-v1.7.3-win-DaiMa.zip'
with zipfile.ZipFile(archive) as z:
 for item in z.infolist():
  target=(source/item.filename).resolve()
  assert target.is_relative_to(source.resolve())
 z.extractall(source)
runtime=OUT/'release-runtime';original=ROOT/'artifacts/dist/v1.7.3/AnClicker/models'
for file in original.rglob('*'):
 if not file.is_file():continue
 dest=runtime/file.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():continue
 if file.suffix.lower() in ('.gguf','.dll','.exe'):os.link(file,dest)
 else:shutil.copy2(file,dest)
checks={}
with zipfile.ZipFile(ROOT/'artifacts/release/v1.7.3/public/AnClicker-v1.7.3-win.zip') as z:
 for rel in ['AnClicker.exe','models/dual_model.json','models/anclicker-v6_5-splitter-q4_0.gguf','models/anclicker-v6_5-converter-q4_0.gguf']:
  h=hashlib.sha256()
  with z.open('AnClicker/'+rel) as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  remote=h.hexdigest();h=hashlib.sha256()
  with (ROOT/'artifacts/dist/v1.7.3/AnClicker'/rel).open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  checks[rel]={'matches_zip':h.hexdigest()==remote,'sha256':remote}
assert all(x['matches_zip'] for x in checks.values())
(OUT/'dist-identity.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print('PREPARED',source/'AnClicker-v1.7.3',flush=True)
