"""Guard fresh startup: other tests must not initialize image support for us."""
import os
from pathlib import Path
import subprocess
import sys


def test_image_execution_in_fresh_process():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, str(root/'image_validation.py')],
                            cwd=root, env=env, text=True, encoding='utf-8',
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"count": 12' in result.stdout
