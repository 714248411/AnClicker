"""Stop on any failure; publishing remains a separate verified action."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.6'
steps=[('build',['tools/build_release_186.py']),('stage',['tools/package_release_186.py','--stage']),('frozen-data',['tools/check_frozen_data_migration_186.py']),('frozen-legacy',['tools/check_frozen_legacy_186.py']),('native',['tools/check_native_186.py']),('pack',['tools/qiniu_release_186.py','pack']),('export',['tools/export_qiniu_186.py']),('validation',['tools/qiniu_release_186.py','validate']),('upgrade',['tools/smoke_qiniu_186_upgrade.py']),('source',['tools/package_source_186.py'])]
for name,args in steps:
 print('START '+name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
