import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.7.2'
start=time.time()
with (OUT/'smoke.log').open('w',encoding='utf8') as log:
 result=subprocess.run([sys.executable,'-X','utf8','tools/packaging/smoke_release.py','--dist','artifacts/dist/v1.7.2-r2'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:raise SystemExit(result.returncode)
(OUT/'smoke-passed.json').write_text(json.dumps({'passed':True,'version':'1.7.2','seconds':time.time()-start}),encoding='utf8')
print('PASS packaged 1.7.2 smoke')
