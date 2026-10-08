"""Build and validate local Windows releases. This entry point never uploads."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from info import CURRENT_VERSION, APP_ID, APP_NAME, EXECUTABLE_NAME, UPDATE_CONFIG
from 发布门槛 import ReleaseContext, validate_release
from release_timing import run_stage


def build_environment():
    env = os.environ.copy()
    windows = Path(env.get('SystemRoot', r'C:\Windows'))
    # Exclude unrelated application DLL directories from PyInstaller analysis.
    env['PATH'] = os.pathsep.join(map(str, [Path(sys.executable).parent,
        Path(sys.base_prefix), windows / 'System32', windows]))
    return env


def export_portable(source: Path, version: str) -> Path:
    """Keep Velopack's internal asset names and export a versioned user ZIP."""
    version = version.removeprefix('v')
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z._-]*', version):
        raise ValueError('Invalid portable version')
    destination = source.parent / 'delivery' / f'{APP_ID}-v{version}-Portable.zip'
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    partial = destination.with_suffix(destination.suffix + '.partial')
    def digest(path):
        result = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                result.update(chunk)
        return result.digest()
    # Exclusive creation avoids overwriting an interrupted export.
    with source.open('rb') as reader, partial.open('xb') as writer:
        shutil.copyfileobj(reader, writer)
    if partial.stat().st_size != source.stat().st_size or digest(partial) != digest(source):
        raise RuntimeError('Portable export size/hash mismatch')
    partial.rename(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'release/velopack')
    parser.add_argument('--base', type=Path, help='Optional previous matching full.nupkg')
    parser.add_argument('--clean', action='store_true', help='Discard PyInstaller cache for troubleshooting')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Build Windows releases on Windows.')
    version = CURRENT_VERSION.removeprefix('v')
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('Output must be empty; choose a fresh directory to avoid mixing releases.')
    output.mkdir(parents=True, exist_ok=True)
    if args.base:
        base = args.base.resolve()
        if not base.is_file() or not base.name.startswith(f"{UPDATE_CONFIG['pack_id']}-") or not base.name.endswith(f"-{UPDATE_CONFIG['runtime']}-full.nupkg"):
            parser.error('Base must be an AnClicker win-x64 full package.')
        shutil.copy2(base, output / base.name)
    subprocess.run(['dotnet', 'tool', 'restore'], cwd=ROOT, check=True)
    dist = ROOT / 'dist/velopack'
    run_stage('PyInstaller 增量构建' if not args.clean else 'PyInstaller 清理构建', subprocess.run, [sys.executable, '-m', 'PyInstaller', *(['--clean'] if args.clean else []), '-y',
        '--distpath', str(dist), '--workpath', str(ROOT / 'build/velopack'),
        str(ROOT / 'packaging/main.spec')], cwd=ROOT, env=build_environment(), check=True)
    app = dist / APP_ID
    run_stage('Velopack 打包', subprocess.run, ['dotnet', 'tool', 'run', 'vpk', 'pack', '--packId', UPDATE_CONFIG['pack_id'],
        '--packVersion', version, '--packDir', str(app), '--mainExe', EXECUTABLE_NAME,
        '--channel', UPDATE_CONFIG['runtime'], '--runtime', UPDATE_CONFIG['runtime'], '--packTitle', APP_NAME, '--noInst',
        '--icon', str(ROOT / 'clicker.ico'), '--releaseNotes', str(ROOT / 'packaging/RELEASE_NOTES.md'),
        '--outputDir', str(output)], cwd=ROOT, check=True)
    context = ReleaseContext(ROOT, app, output, output / UPDATE_CONFIG['portable_name'],
        APP_ID, UPDATE_CONFIG['pack_id'], version, UPDATE_CONFIG['runtime'])
    run_stage('产物与启动验收', validate_release, context)
    for name in (UPDATE_CONFIG['portable_name'], UPDATE_CONFIG['feed_name']):
        if not (output / name).is_file():
            raise RuntimeError(f'Missing release artifact: {name}')
    portable = export_portable(context.portable_zip, version)
    print(f'Validated portable delivery: {portable}. Nothing was uploaded.')


if __name__ == '__main__':
    main()
