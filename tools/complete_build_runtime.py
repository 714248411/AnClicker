import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run([str(root/'.local/cache/python-3.10.11-amd64.exe'),'/modify','/quiet','Include_tcltk=1'],check=True)
