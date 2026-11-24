"""Assemble the full public 1.8.8 application with verified v8 models."""
import hashlib,json,shutil,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BASE=ROOT/'artifacts/release/v1.8.8'
DIST=ROOT/'artifacts/dist/v1.8.8/AnClicker'
VALIDATION=ROOT/'artifacts/validation/v1.8.8'
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def stage():
 from tools.packaging.ai_bundle import verify
 verify(ROOT,DIST)
 records=json.loads((VALIDATION/'models.json').read_text(encoding='utf8'))['models']
 assert json.loads((VALIDATION/'build.json').read_text())['passed']
 assert (DIST/'AnClicker.exe').is_file() and not (DIST/'data').exists()
 modeldir=DIST/'models';modeldir.mkdir(exist_ok=True)
 for role,record in records.items():
  source=ROOT/'models'/record['file'];assert digest(source)==record['sha256']
  target=modeldir/source.name
  if not target.exists():shutil.copy2(source,target)
  assert digest(target)==record['sha256']
 for runtime in ('llama-cpu','llama-vulkan'):
  source=ROOT/'models'/runtime;target=modeldir/runtime
  target.mkdir(exist_ok=True)
  for path in source.iterdir():
   if path.is_file() and (path.suffix in ('.exe','.dll') or path.name.startswith('LICENSE')):
    shutil.copy2(path,target/path.name)
 for path in (ROOT/'models').glob('LICENSE-*'):shutil.copy2(path,modeldir/path.name)
 config={'enabled':True,'splitter_mode':'pairwise','serial_models':True,'embedding_enabled':True,'correction_memory_enabled':True,**{role:record['file'] for role,record in records.items()}}
 (modeldir/'dual_model.json').write_text(json.dumps(config),encoding='utf8')
 (modeldir/'recommended_dual_model.json').write_text(json.dumps({'verified':True,**config}),encoding='utf8')
 (modeldir/'active_model.json').write_text(json.dumps({'file':records['converter']['file'],'name':'AnClicker v8 指令转换'},ensure_ascii=False),encoding='utf8')
 (modeldir/'bundle-manifest.json').write_text(json.dumps({'version':'1.8.8','models':records},indent=2),encoding='utf8')
 from tools.packaging.crawl_runtime import stage as stage_crawl
 stage_crawl(ROOT,DIST)
 print('PASS staged verified models and CPU/Vulkan runtimes',flush=True)
def package():
 from tools.packaging.ai_bundle import verify,smoke_identity
 verify(ROOT,DIST)
 proof=json.loads((VALIDATION/'smoke-passed.json').read_text(encoding='utf8'))
 if proof.get('passed') is not True or proof.get('identity')!=smoke_identity(DIST):raise RuntimeError('Smoke proof does not match current executable/resources/configuration')
 BASE.mkdir(parents=True,exist_ok=True);public=BASE/'public';public.mkdir(exist_ok=True)
 notes=(ROOT/'tools/packaging/RELEASE_NOTES.md').read_text(encoding='utf8')
 notes+='\n完整 Windows 程序包，请解压到新目录后运行 AnClicker/AnClicker.exe。内含 v8 双模型与 CPU/Vulkan 运行库。\n'
 (BASE/'RELEASE_NOTES.md').write_text(notes,encoding='utf8')
 target=public/'AnClicker-v1.8.8-win.zip';partial=target.with_suffix('.zip.partial')
 assert not target.exists(),'Never overwrite a release artifact'
 if partial.exists() and '--finish-existing' not in sys.argv:raise RuntimeError('Existing partial requires explicit validation')
 if not partial.exists():
  with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
   for path in sorted(DIST.rglob('*')):
    if path.is_file() and '.dual-runtime' not in path.relative_to(DIST).parts and path.relative_to(DIST).parts[0].casefold() not in ('data', 'date'):archive.write(path,'AnClicker/'+path.relative_to(DIST).as_posix())
   archive.writestr('AnClicker/Data/', b'')
   archive.writestr('RELEASE_NOTES.md',notes)
   archive.write(VALIDATION/'models.json','MODEL-VALIDATION.json')
   archive.writestr('BUILD-MANIFEST.json',json.dumps({'version':'v1.8.8','entry':'AnClicker/AnClicker.exe','package_type':'full-application'}))
 with zipfile.ZipFile(partial) as archive:
  assert archive.testzip() is None
  names=archive.namelist();assert len(names)==len(set(names))
  assert 'AnClicker/Data/' in names
  assert not any(n.startswith('AnClicker/Data/') and n != 'AnClicker/Data/' for n in names)
  assert len([n for n in names if n.endswith('.gguf')])==2
  assert not any(n.startswith('AnClicker/data/') or '/.dual-runtime/' in n or '/.private' in n or '/training/' in n or n.endswith('.log') or (n.endswith('.db') and '/defaults/' not in n) for n in names)
 partial.rename(target)
 assets=[]
 for path in [target,public/'AnClicker-v1.8.8-win-DaiMa.zip']:
  sha=digest(path);path.with_suffix('.zip.sha256').write_text(sha+'  '+path.name+'\n',encoding='ascii')
  assets.append({'scope':'public','path':path.relative_to(BASE).as_posix(),'sha256':sha,'bytes':path.stat().st_size})
 (BASE/'release-manifest.json').write_text(json.dumps({'version':'1.8.8','repository':'714248411/AnClicker','published':False,'assets':assets},indent=2),encoding='utf8')
 print('PASS full public release archive and source hashes',flush=True)
if __name__=='__main__':
 if '--stage' in sys.argv:
  stage()
 else:
  raise SystemExit('1.8.8 必须使用 qiniu_release_188.py pack 和 export_qiniu_188.py，禁止输出不支持更新的普通 ZIP。')
