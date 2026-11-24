import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['check_long_sentences_v2.py','check_online_operations.py']:
 subprocess.run([sys.executable,'-X','utf8','-u','tools/'+name,'repair'],cwd=ROOT,check=True)
