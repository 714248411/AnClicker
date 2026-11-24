import sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for _ in range(600):
 if 'V6_5_REGRESSION_COMPLETE' in (ROOT/'.local/cache/v6_5-regression.log').read_text(encoding='utf8'):break
 time.sleep(3)
else:raise TimeoutError('回归未完成')
subprocess.run([sys.executable,'-X','utf8','-u','tools/check_multi_task_v6_5.py','v6_5'],cwd=ROOT,check=True)

for args in [["tools/check_general_operations.py","v6_5","--model-version","v6_5"],["tools/check_general_operations.py","v6_5-unseen","--unseen","--model-version","v6_5"]]:
 subprocess.run([sys.executable,"-X","utf8","-u",*args],cwd=ROOT,check=True)
print("ALL_FINAL_CHECKS_COMPLETE",flush=True)
