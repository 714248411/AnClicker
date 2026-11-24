"""Stage a relocatable Python runtime, never a machine-bound virtualenv."""
import shutil
from pathlib import Path

def stage(root, dist):
    root, dist = Path(root), Path(dist)
    source = root / '.local/portable-python'
    packages = root / '.local/runtimes/crawl4ai/venv/Lib/site-packages'
    target = dist / 'runtime/crawl4ai/python'
    assert (source / 'python.exe').is_file()
    assert (packages / 'crawl4ai/__init__.py').is_file()
    target.mkdir(parents=True, exist_ok=True)
    def ignore(folder, names):
        return [n for n in names if n in ('__pycache__', 'site-packages', 'test', 'tests', 'idlelib', 'tkinter', 'ensurepip') or n.endswith(('.pyc', '.pyo', '.pdb'))]
    for name in ('python.exe', 'python3.dll', 'python310.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt'):
        shutil.copy2(source / name, target / name)
    for name in ('Lib', 'DLLs'):
        shutil.copytree(source / name, target / name, ignore=ignore, dirs_exist_ok=True)
    shutil.copytree(packages, target / 'Lib/site-packages', dirs_exist_ok=True,
        ignore=lambda folder, names: [n for n in names if n in ('__pycache__',) or (Path(folder).name == 'proxy' and n == '_experimental') or n.endswith(('.pyc', '.pyo', '.pdb'))])
    assert not (target / 'pyvenv.cfg').exists()
    print('PASS staged portable Crawl4AI Python and dependencies', flush=True)
