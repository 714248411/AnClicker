import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for args in [['tools/check_simple_language.py'],['tools/check_online_operations.py','simple-language'],['tools/check_multi_task_v6_5.py','v6_5']]:
 print('RUN',args,flush=True);subprocess.run([sys.executable,'-X','utf8','-u',*args],cwd=ROOT,check=True)
print('SIMPLE_REGRESSION_COMPLETE',flush=True)
