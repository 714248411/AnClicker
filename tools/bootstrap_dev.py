import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ)
for k in list(env):
    if k.lower().endswith('_proxy'): env.pop(k)
subprocess.run([sys.executable,'-m','pip','install','uv','--target',str(root/'.local/cache')],env=env,check=True)
env['PYTHONPATH']=str(root/'.local/cache')
subprocess.run([sys.executable,'-m','uv','sync','--python','3.10','--group','release'],cwd=root,env=env,check=True)
