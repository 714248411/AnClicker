"""Check clean portable startup in fresh interpreters, before Qt is imported."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import importlib
import json
import os
from pathlib import Path
import sys
install, order, frozen, override = sys.argv[1:]
sys.path.insert(0, os.environ['STARTUP_PROBE_ROOT'])
sys.frozen = frozen == '1'
sys.executable = str(Path(install) / 'AnClicker.exe')
os.environ.pop('ANCLICKER_DATA_DIR', None)
if override:
    os.environ['ANCLICKER_DATA_DIR'] = override
for name in order.split(','):
    importlib.import_module('anclicker.app.' + name)
from anclicker.app import paths, startup_environment
expected = Path(override) if override else (
    paths.storage_install_folder(Path(install)) / 'Data' if sys.frozen
    else Path(paths.get_install_folder()) / 'Data')
assert Path(paths.DATA_FOLDER) == expected, (paths.DATA_FOLDER, expected)
if sys.frozen:
    prepared = startup_environment.prepare_environment()
    assert prepared == expected, (prepared, expected)
    assert all((prepared / folder).is_dir() for folder in ('images', 'exports', 'logs', 'temp'))
assert not any(name.startswith(('PySide', 'qt_compat', 'anclicker.ui')) for name in sys.modules)
print(json.dumps({'ready': True, 'data': str(expected)}))
'''


READONLY_PROBE = r'''
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,os.environ['STARTUP_PROBE_ROOT'])
with tempfile.TemporaryDirectory() as folder:
    base=Path(folder); install=base/'readonly'; install.mkdir()
    sys.frozen=True; sys.executable=str(install/'AnClicker.exe')
    os.environ.pop('ANCLICKER_DATA_DIR',None)
    os.environ['LOCALAPPDATA']=str(base/'local')
    from anclicker.app import startup_environment
    assert 'anclicker.app.paths' not in sys.modules
    original=startup_environment.tempfile.TemporaryFile
    def probe(*args,**kwargs):
        if Path(kwargs.get('dir',''))==install/'Data':raise PermissionError('test readonly install')
        return original(*args,**kwargs)
    startup_environment.tempfile.TemporaryFile=probe
    target=startup_environment.prepare_environment()
    from anclicker.app import paths
    assert Path(paths.DATA_FOLDER)==target
    assert target==base/'local'/'AnClicker'
    print('PASS: read-only install falls back before cached paths are initialized')
'''

def main():
    with tempfile.TemporaryDirectory(prefix='anclicker-path-check-') as folder:
        base = Path(folder)
        portable = base / '便携版 首次启动'
        portable.mkdir()
        current = base / 'velopack/current'
        current.mkdir(parents=True)
        (current / 'sq.version').touch()
        (current.parent / 'Update.exe').touch()
        cases = [
            (portable, 'startup_environment,paths', True, ''),
            (portable, 'paths,startup_environment', True, ''),
            (current, 'startup_environment,paths', True, ''),
            (portable, 'startup_environment,paths', True, str(base / '用户数据')),
            (portable, 'startup_environment,paths', False, ''),
            (portable, 'paths,startup_environment', False, ''),
        ]
        for install, order, frozen, override in cases:
            result = subprocess.run(
                [sys.executable, '-I', '-c', PROBE, str(install), order, str(int(frozen)), override],
                cwd=folder, env=dict(os.environ, STARTUP_PROBE_ROOT=str(ROOT)),
                capture_output=True, text=True, encoding='utf-8', timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr)
            assert json.loads(result.stdout)['ready']
            print(f'PASS frozen={frozen}; order={order}; override={bool(override)}; install={install.name}')
        result = subprocess.run(
            [sys.executable, '-I', '-c', READONLY_PROBE], cwd=folder,
            env=dict(os.environ, STARTUP_PROBE_ROOT=str(ROOT)),
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr)
        print(result.stdout.strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
