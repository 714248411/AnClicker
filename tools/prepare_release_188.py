"""Stop on any failure; publishing remains a separate verified action."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.8'
steps=[('build',['tools/build_release_188.py']),('stage',['tools/package_release_188.py','--stage']),('frozen-v8',['tools/check_frozen_v8_188.py']),('frozen-data',['tools/check_frozen_data_migration_188.py']),('frozen-legacy',['tools/check_frozen_legacy_188.py']),('native',['tools/check_native_188.py']),('pack',['tools/qiniu_release_188.py','pack']),('export',['tools/export_qiniu_188.py']),('validation',['tools/qiniu_release_188.py','validate']),('upgrade',['tools/smoke_qiniu_188_upgrade.py']),('source',['tools/package_source_188.py'])]
for name,args in steps:
 print('START '+name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
