import sys,subprocess,time,psutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
try:
 p=psutil.Process(6092)
 if 'tools/regress_long_sentences.py' not in p.cmdline():raise RuntimeError('Wrong PID')
 while p.is_running():time.sleep(2)
except psutil.NoSuchProcess:pass
for args in [('final',),('additional','--additional'),('plain','--plain')]:
 subprocess.run([sys.executable,'-X','utf8','-u','tools/check_long_sentences.py',*args],cwd=ROOT,check=True)
print('ALL_LONG_COMPLETE',flush=True)
