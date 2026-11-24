import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('package_source_177','package_release_177','verify_release_177_artifacts'):
 print('START',name,flush=True)
 subprocess.run([sys.executable,'-X','utf8',str(root/'tools'/(name+'.py'))],cwd=root,check=True)
 print('PASS',name,flush=True)
