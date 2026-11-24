import sys,time,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
log=ROOT/'.local/cache/train-v6_5.log'
deadline=time.time()+1800
while time.time()<deadline:
 text=log.read_text(encoding='utf8',errors='replace')
 if 'V6_5_TRAINING_COMPLETE' in text:break
 if 'Traceback (most recent call last)' in text:raise RuntimeError(text[-4000:])
 time.sleep(3)
else:raise TimeoutError('训练没有在期限内完成')
while 'MULTI_TASK_COMPLETE' not in (ROOT/'.local/cache/multi-task-v6_4.log').read_text(encoding='utf8'):time.sleep(2)
for args in [['tools/check_multi_task_v6_5.py','v6_5'],['models/training/compare_v6_5_splitter.py']]:
 print('RUN',args,flush=True)
 result=subprocess.run([sys.executable,'-X','utf8','-u',*args],cwd=ROOT)
 print('RETURN',result.returncode,flush=True)
print('CANDIDATE_COMPARISON_COMPLETE',flush=True)
