"""Stop on any failure; publishing remains a separate verified action."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.5'
steps=[('build',['tools/build_release_185.py']),('stage',['tools/package_release_185.py','--stage']),('frozen-data',['tools/check_frozen_data_migration_185.py']),('frozen-legacy',['tools/check_frozen_legacy_185.py']),('native',['tools/check_native_185.py']),('pack',['tools/qiniu_release_185.py','pack']),('export',['tools/export_qiniu_185.py']),('validation',['tools/qiniu_release_185.py','validate']),('upgrade',['tools/smoke_qiniu_185_upgrade.py']),('source',['tools/package_source_185.py'])]
for name,args in steps:
 print('START '+name,flush=True)
 with (OUT/(name+'-pipeline.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
