import sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
deadline=time.time()+1800
while time.time()<deadline:
 if 'CANDIDATE_COMPARISON_COMPLETE' in (ROOT/'.local/cache/v6_5-comparison.log').read_text(encoding='utf8'):break
 time.sleep(3)
else:raise TimeoutError('Comparison timeout')
subprocess.run([sys.executable,'-X','utf8','-u','tools/run_v6_5_regression.py'],cwd=ROOT,check=True)
