import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for args in [('final',),('additional','--additional')]:
 subprocess.run([sys.executable,'-X','utf8','-u','tools/check_long_sentences.py',*args],cwd=ROOT,check=True)
