import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.7.4'
steps=[('build','tools/build_release_174.py',[]),('stage','tools/package_release_174.py',['--stage']),('smoke','tools/smoke_release_174.py',[]),('language','tools/run_release_language_174.py',[]),('source','tools/package_source_174.py',[]),('package','tools/package_release_174.py',[]),('verify','tools/verify_release_174_artifacts.py',[])]
rows=[]
for name,script,args in steps:
 print('START',name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  result=subprocess.run([sys.executable,'-X','utf8',script,*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 rows.append({'step':name,'exit_code':result.returncode});(OUT/'pipeline.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
 if result.returncode:raise SystemExit(result.returncode)
 print('PASS',name,flush=True)
