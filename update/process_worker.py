"""Cancellable SDK checks/downloads, isolated from the UI and installed files."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import velopack

ASSET_FIELDS = ('PackageId', 'Version', 'Type', 'FileName', 'SHA1', 'SHA256', 'Size', 'NotesMarkdown', 'NotesHtml')


def encode(value):
    if value is None:
        return None
    if hasattr(value, 'TargetFullRelease'):
        return {'info': True, 'target': encode(value.TargetFullRelease),
                'deltas': [encode(v) for v in value.DeltasToTarget],
                'downgrade': value.IsDowngrade, 'base': encode(value.BaseRelease)}
    return {key: getattr(value, key) for key in ASSET_FIELDS}


def decode(value):
    if value is None:
        return None
    if value.get('info'):
        return velopack.UpdateInfo(decode(value['target']), [decode(v) for v in value['deltas']], value['downgrade'], decode(value['base']))
    return velopack.VelopackAsset(**value)


class UpdateCancelled(Exception):
    pass


def run_isolated(thread, action, source, update=None, progress=None):
    with tempfile.TemporaryDirectory(prefix='ac-update-') as directory:
        root = Path(directory)
        (root / 'request.json').write_text(json.dumps({'action': action, 'source': source, 'update': encode(update)}), encoding='utf-8')
        args = [sys.executable]
        if not getattr(sys, 'frozen', False):
            args.append(str(Path(__file__).resolve().parents[1] / 'main.py'))
        args.extend(['--update-worker', directory])
        if thread.isInterruptionRequested():
            raise UpdateCancelled()
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        offset = 0
        try:
            while True:
                if thread.isInterruptionRequested():
                    raise UpdateCancelled()
                if progress and (root / 'progress.txt').exists():
                    with (root / 'progress.txt').open('r', encoding='ascii') as handle:
                        handle.seek(offset)
                        for line in handle:
                            if line.endswith('\n'):
                                progress(int(line.strip()))
                                offset += len(line)
                try:
                    process.wait(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    pass
            if thread.isInterruptionRequested():
                raise UpdateCancelled()
            if not (root / 'result.json').is_file():
                raise RuntimeError('更新子进程意外退出，未应用更新')
            result = json.loads((root / 'result.json').read_text(encoding='utf-8'))
            if 'error' in result:
                raise RuntimeError(result['error'])
            return result['event'], decode(result.get('value'))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def main():
    root = Path(sys.argv[sys.argv.index('--update-worker') + 1])
    request = json.loads((root / 'request.json').read_text(encoding='utf-8'))
    try:
        manager = velopack.UpdateManager(request['source'])
        if request['action'] == 'check':
            value = manager.get_update_pending_restart()
            event = 'pending'
            if value is None:
                value = manager.check_for_updates()
                event = 'found' if value is not None else 'none'
        elif request['action'] == 'download':
            value = decode(request['update'])
            def progress(percent):
                with (root / 'progress.txt').open('a', encoding='ascii', newline='\n') as handle:
                    handle.write(str(int(percent)) + '\n')
            manager.download_updates(value, progress_callback=progress)
            event = 'downloaded'
        else:
            raise ValueError('未知更新动作')
        result = {'event': event, 'value': encode(value)}
    except Exception as error:
        result = {'error': f'{type(error).__name__}: {error}'}
    (root / 'result.json').write_text(json.dumps(result), encoding='utf-8')
