import os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ,PYTHONPATH=str(root/'.runtime-tools'),UV_PYTHON=sys.executable)
raise SystemExit(subprocess.run([sys.executable,'-m','uv','lock','--check'],cwd=root,env=env).returncode)
