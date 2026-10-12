import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ)
env['ANCLICKER_DATA_DIR']=str(root/'validation'/'startup-data')
env['ANCLICKER_SMOKE_LIGHTWEIGHT']='1'
env['ANCLICKER_SINGLETON_KEY']='rpa-rebuild-smoke'
result=subprocess.run([sys.executable,str(root/'main.py'),'--release-smoke'],cwd=root,env=env,timeout=60)
raise SystemExit(result.returncode)
