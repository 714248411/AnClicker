"""Offline Velopack acceptance using two package versions of the current binary.
The older package is a synthetic updater baseline, not a previous product build.
No Qiniu calls are made, no tracked version is changed.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from info import CURRENT_VERSION


def wait_for_processes(root):
    # Portable launchers return before their child/bootloader processes exit.
    import psutil
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        active = []
        for process in psutil.process_iter(['exe']):
            try:
                if process.info['exe'] and Path(process.info['exe']).resolve().is_relative_to(root.resolve()):
                    active.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue
        if not active:
            time.sleep(0.5)  # let Windows release image sections before cleanup
            return
        psutil.wait_procs(active, timeout=1)
    raise RuntimeError('隔离验收程序尚未退出，保留临时目录等待检查')


def main():
    spec = importlib.util.spec_from_file_location('local_publisher', ROOT / 'packaging/发布Velopack.py')
    publisher = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = publisher
    spec.loader.exec_module(publisher)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse', action='store_true', help='Reuse local acceptance packages after fixing a validator')
    parser.add_argument('--output', type=Path, default=ROOT / '.release-validation' / 'releases')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and not args.reuse:
        raise ValueError('验收目录必须尚不存在，避免混入旧产物')
    output.mkdir(parents=True, exist_ok=True)
    baseline_portable = output.parent / 'baseline-Portable.zip'
    target = CURRENT_VERSION.removeprefix('v')
    major, minor, patch = map(int, target.split('.'))
    if patch < 1:
        raise ValueError('此验收脚本需要 patch >= 1 以生成低版本基线')
    baseline = f'{major}.{minor}.{patch - 1}'
    config = json.loads((publisher.APP / 'update-source.json').read_text(encoding='utf-8'))
    from urllib.parse import urlsplit
    parsed = urlsplit(config['url'])
    publish_config = publisher.PublishConfig('offline-test', 'z0', f'{parsed.scheme}://{parsed.netloc}', parsed.path.strip('/'))
    for version in (() if args.reuse else (baseline, target)):
        publisher.run(['dotnet', 'tool', 'run', 'vpk', 'pack', '--packId', 'AnClicker',
            '--packVersion', version, '--packDir', str(publisher.APP), '--mainExe', 'AnClicker.exe',
            '--packTitle', 'An Clicker', '--packAuthors', 'An Clicker contributors',
            '--channel', 'win-x64', '--runtime', 'win-x64', '--noInst',
            '--outputDir', str(output)], publisher.isolated_environment())
        if version == baseline:
            # Copy the initial portable before vpk overwrites it in the second pack.
            baseline_portable = output.parent / 'baseline-Portable.zip'
            __import__('shutil').copy2(next(output.glob('*-Portable.zip')), baseline_portable)
    feed_path = output / 'releases.win-x64.json'
    feed = json.loads(feed_path.read_text(encoding='utf-8-sig'))
    feed['Assets'] = publisher.current_assets(feed, target)
    feed_path.write_text(json.dumps(feed, indent=2), encoding='utf-8')
    publisher.RELEASE = output
    publisher.validate_local(publish_config)
    with tempfile.TemporaryDirectory(prefix='anclicker-portable-upgrade-', ignore_cleanup_errors=True) as directory:
        portable = Path(directory)
        with zipfile.ZipFile(baseline_portable) as archive:
            archive.extractall(portable)
        environment = publisher.isolated_environment()
        environment.update(ANCLICKER_DATA_DIR='', ANCLICKER_LOCAL_UPDATE_SOURCE=str(output))
        environment['TEMP'] = str(portable / 'temp')
        environment['TMP'] = environment['TEMP']
        (portable / 'temp').mkdir()
        process = subprocess.Popen([str(portable / 'An Clicker.exe'), '--release-update-smoke'],
            env=environment, cwd=portable)
        report = portable / 'data/update-after.json'
        try:
            deadline = time.monotonic() + 180
            while not report.is_file() and time.monotonic() < deadline:
                time.sleep(1)
            if not report.is_file():
                raise RuntimeError('Portable 实际入口本地升级没有生成完成报告')
            before = json.loads((portable / 'data/update-before.json').read_text(encoding='utf-8'))
            after = json.loads(report.read_text(encoding='utf-8'))
            if (before['version'] != baseline or after['version'] != target
                    or not after['database_preserved'] or not after['file_preserved']):
                raise RuntimeError('本地升级版本或数据保留验证失败')
            print('本地 Portable 升级通过:', before['version'], '->', after)
            # Re-launch the formal root entry for live GUI smoke readiness after upgrade.
            environment['ANCLICKER_DATA_DIR'] = str(portable / 'data')
            environment['ANCLICKER_SINGLETON_KEY'] = 'local-upgrade-' + __import__('uuid').uuid4().hex
            gui = subprocess.Popen([str(portable / 'An Clicker.exe'), '--release-smoke'],
                env=environment, cwd=portable)
            ready = portable / 'data/startup-ready.json'
            deadline = time.monotonic() + 90
            while not ready.is_file() and time.monotonic() < deadline:
                time.sleep(1)
            if not ready.is_file() or not json.loads(ready.read_text(encoding='utf-8'))['window_visible']:
                raise RuntimeError('升级后正式入口 GUI 未就绪')
            gui.wait(timeout=15)
        finally:
            process.wait(timeout=15)
            wait_for_processes(portable)
    (output.parent / 'local-update-evidence.json').write_text(json.dumps({
        'baseline_kind': 'synthetic-current-binary', 'from': baseline, 'to': target,
        'database_preserved': True, 'user_file_preserved': True,
        'portable_root_gui_ready': True, 'qiniu_published': False}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
