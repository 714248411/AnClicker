import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.8.8'
assert json.loads((OUT/'upgrade.json').read_text())['passed']
assert (ROOT/'artifacts/source/v1.8.8/AnClicker-v1.8.8-win-DaiMa.zip.sha256').is_file()
credential=sys.argv[1]
steps=[('publish-feed',['tools/qiniu_release_188.py','publish',credential]),('publish-downloads',['tools/publish_qiniu_delivery_188.py',credential]),('public-client',['tools/check_public_update_188.py'])]
for name,args in steps:
 print('START '+name,flush=True)
 with (OUT/(name+'.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
