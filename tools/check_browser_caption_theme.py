"""Verify visible theme/focus colors, then real bridge browser navigation."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
electron = root / '.local/runtimes/electron/electron.exe'
subprocess.run([str(electron), 'tools/check_browser_window_theme.cjs'], cwd=root, check=True)
subprocess.run([sys.executable, '-B', '-X', 'utf8', 'tools/check_browser_titles.py'], cwd=root, check=True)
