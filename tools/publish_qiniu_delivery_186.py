"""Upload versioned, verified portable/source downloads without replacing prior files."""
import os,sys,json,hashlib
sys.excepthook=lambda kind,value,tb: print("Publication failed: "+kind.__name__,file=sys.stderr)
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from info import UPDATE_CONFIG
from tools.publishing_credentials import publishing_environment
os.environ.update(publishing_environment(sys.argv[1],os.environ,UPDATE_CONFIG))
from tools.packaging.发布Velopack import PublishConfig,QiniuUploader,verify_public
out=ROOT/'artifacts/release/v1.8.6-qiniu'
assert json.loads((ROOT/'artifacts/validation/v1.8.6/upgrade.json').read_text())['passed']
config=PublishConfig.from_environment();uploader=QiniuUploader(config)
files=[out/'delivery/AnClicker-v1.8.6-win.zip',ROOT/'artifacts/source/v1.8.6/AnClicker-v1.8.6-win-DaiMa.zip']
records=[]
for path in files:
 digest=hashlib.file_digest(path.open('rb'),'sha256').hexdigest() if hasattr(hashlib,'file_digest') else None
 if digest is None:
  h=hashlib.sha256()
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
  digest=h.hexdigest()
 assert path.with_suffix('.zip.sha256').read_text().split()[0]==digest
 print('UPLOAD '+path.name,flush=True)
 uploader.upload(path);verify_public(config,path.name,path.stat().st_size,digest)
 uploader.upload(path.with_suffix('.zip.sha256'))
 records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':digest,'url':config.url(path.name)})
 print('PASS public download '+path.name,flush=True)
(out/'public-downloads.json').write_text(json.dumps(records,indent=2))
