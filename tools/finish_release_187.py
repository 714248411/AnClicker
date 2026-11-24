import time,subprocess,sys,json,psutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.7'
while psutil.pid_exists(22020): time.sleep(2)
assert (ROOT/'artifacts/release/v1.8.7-qiniu/validation-publish.json').is_file(), 'Final validation failed'
for name,args in [('upgrade',['tools/smoke_qiniu_187_upgrade.py']),('source',['tools/package_source_187.py'])]:
 print('START '+name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
