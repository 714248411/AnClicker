"""Stop on any failure; publishing remains a separate verified action."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.7'
steps=[('build',['tools/build_release_187.py']),('stage',['tools/package_release_187.py','--stage']),('frozen-v8',['tools/check_frozen_v8_187.py']),('frozen-data',['tools/check_frozen_data_migration_187.py']),('frozen-legacy',['tools/check_frozen_legacy_187.py']),('native',['tools/check_native_187.py']),('pack',['tools/qiniu_release_187.py','pack']),('export',['tools/export_qiniu_187.py']),('validation',['tools/qiniu_release_187.py','validate']),('upgrade',['tools/smoke_qiniu_187_upgrade.py']),('source',['tools/package_source_187.py'])]
for name,args in steps:
 print('START '+name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
