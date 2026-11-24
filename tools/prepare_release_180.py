import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.8.0'
steps=[('regressions','check_release_180.py',[]),('models','check_release_models_180.py',[]),('build','build_release_180.py',[]),('stage','package_release_180.py',['--stage']),('smoke','smoke_release_180.py',[]),('source','package_source_180.py',[]),('package','package_release_180.py',[]),('verify','verify_release_180_artifacts.py',[])]
if '--resume-after-regressions' in sys.argv:steps=steps[1:]
rows=[]
for name,script,args in steps:
 print('START',name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  result=subprocess.run([sys.executable,'-X','utf8','tools/'+script,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 rows.append({'step':name,'exit_code':result.returncode})
 (OUT/'pipeline.json').write_text(json.dumps(rows,indent=2))
 if result.returncode:raise SystemExit(result.returncode)
 print('PASS',name,flush=True)
