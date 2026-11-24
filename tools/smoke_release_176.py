import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.packaging.ai_bundle import smoke_identity
OUT=ROOT/'artifacts/validation/v1.7.6'
DIST=ROOT/'artifacts/dist/v1.7.6/AnClicker'
identity_before=smoke_identity(DIST)
start=time.time()
with (OUT/'smoke.log').open('w',encoding='utf8') as log:
 result=subprocess.run([sys.executable,'-X','utf8','tools/packaging/smoke_release.py','--dist','artifacts/dist/v1.7.6'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:raise SystemExit(result.returncode)
assert identity_before==smoke_identity(DIST),'Build changed during smoke test'
(OUT/'smoke-passed.json').write_text(json.dumps({'passed':True,'identity':identity_before,'version':'1.7.6','seconds':time.time()-start}),encoding='utf8')
print('PASS packaged 1.7.6 smoke')
