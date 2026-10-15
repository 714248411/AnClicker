"""Exercise an actual portable upgrade against an isolated local feed."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tempfile
import uuid
import zipfile

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'APP_ID_APP_NAME_EXECUTABLE_NAME_UPDATE_CONFIG': ('from', 'info', ('APP_ID', 'APP_NAME', 'EXECUTABLE_NAME', 'UPDATE_CONFIG'), 0),
    '发布门槛_ReleaseContext_etc': ('from', 'tools.packaging.发布门槛', ('ReleaseContext', 'validate_archive', 'validate_portable_release', '_validate_delta'), 0),
    'CURRENT_VERSION': ('from', 'info', ('CURRENT_VERSION',), 0),
})


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
APP_ID, APP_NAME, EXECUTABLE_NAME, UPDATE_CONFIG = _module_imports.load('APP_ID_APP_NAME_EXECUTABLE_NAME_UPDATE_CONFIG')
ReleaseContext, validate_archive, validate_portable_release, _validate_delta = _module_imports.load('发布门槛_ReleaseContext_etc')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=ROOT / 'artifacts/dist/velopack' / APP_ID)
    args = parser.parse_args()
    sandbox = Path(tempfile.mkdtemp(prefix='ac-upgrade-'))
    feed = sandbox / 'feed'
    portable = sandbox / 'portable'
    feed.mkdir(parents=True)
    for version in ('0.0.1', '0.0.2'):
        subprocess.run(['dotnet', 'tool', 'run', 'vpk', 'pack', '--packId', UPDATE_CONFIG['pack_id'],
            '--packVersion', version, '--packDir', str(args.app.resolve()),
            '--mainExe', EXECUTABLE_NAME, '--channel', UPDATE_CONFIG['runtime'], '--runtime', UPDATE_CONFIG['runtime'],
            '--packTitle', APP_NAME, '--outputDir', str(feed), '--noInst'], cwd=ROOT, check=True)
        if version == '0.0.1':
            with zipfile.ZipFile(feed / UPDATE_CONFIG['portable_name']) as archive:
                archive.extractall(portable)
    for package in feed.glob('*.nupkg'):
        validate_archive(package)
    # Delta reconstruction must be byte-for-byte identical to the target full.
    # The executable retains the production application version; package metadata is test-only.
    context = ReleaseContext(ROOT, args.app.resolve(), feed, feed / UPDATE_CONFIG['portable_name'],
                             APP_ID, UPDATE_CONFIG['pack_id'], '0.0.2', UPDATE_CONFIG['runtime'])
    validate_portable_release(context)
    # Check delta payloads separately from the application's version assertion.
    CURRENT_VERSION = _module_imports.load('CURRENT_VERSION')
    _validate_delta(context, sandbox / 'delta-check', app_version=CURRENT_VERSION.removeprefix('v'))
    data = portable / 'data'
    env = dict(os.environ, ANCLICKER_SMOKE_FEED=str(feed),
               ANCLICKER_SINGLETON_KEY='upgrade-' + uuid.uuid4().hex)
    env.pop('ANCLICKER_DATA_DIR', None)
    result = data / 'velopack-smoke-result.json'
    process = subprocess.Popen([str(portable / UPDATE_CONFIG['launcher_name']), '--velopack-local-smoke'], env=env)
    try:
        process.wait(timeout=180)
        deadline = time.monotonic() + 180
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(1)
        if not result.is_file():
            raise RuntimeError(f'Upgrade did not produce a restart report; inspect {sandbox}')
        report = json.loads(result.read_text(encoding='utf-8'))
        assert report == {'from': '0.0.1', 'downloaded': True, 'to': '0.0.2',
                          'restarted': True, 'data_preserved': True}, report
        assert not (portable / 'current/data').exists()
        print(f'Local upgrade passed: {result}\n{report}')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


if __name__ == '__main__':
    main()
