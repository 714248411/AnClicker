import os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ);env.pop('ELECTRON_RUN_AS_NODE',None)
raise SystemExit(subprocess.run([str(root/'.local/runtimes/electron/electron.exe'),str(root/'tools/check_toolbar.cjs')],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30).returncode)
