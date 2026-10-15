"""Check dependency lock consistency using the available uv installation."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
uv = shutil.which('uv')
command = [uv] if uv else [sys.executable, '-m', 'uv']
env = dict(os.environ, UV_PYTHON=sys.executable)
raise SystemExit(subprocess.run([*command, 'lock', '--check', '--offline'], cwd=root, env=env).returncode)
