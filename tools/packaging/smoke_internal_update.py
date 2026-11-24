"""Verify channel HTTP checks and upgrade a verified legacy portable copy."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import time
from urllib.parse import urlsplit
from uuid import uuid4

from check_internal_update import verify
from info import EXECUTABLE_NAME, UPDATE_CONFIG, VERSION, update_source_config


def worker_check(exe, source):
    with tempfile.TemporaryDirectory(prefix='ac-update-check-') as folder:
        root = Path(folder)
        (root / 'request.json').write_text(json.dumps({
            'action': 'check', 'source': source, 'update': None,
        }), encoding='utf-8')
        subprocess.run([str(exe), '--update-worker', folder], check=True, timeout=30)
        return json.loads((root / 'result.json').read_text(encoding='utf-8'))


def await_migration(portable, feed, sandbox):
    environment = dict(os.environ, ANCLICKER_SMOKE_FEED=str(feed),
                       ANCLICKER_DATA_DIR=str(sandbox / 'data'),
                       ANCLICKER_SINGLETON_KEY='migration-' + uuid4().hex)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    report_path = sandbox / 'data' / 'velopack-smoke-result.json'
    launcher = portable / UPDATE_CONFIG['launcher_name']
    with subprocess.Popen([str(launcher), '--velopack-local-smoke'], env=environment) as process:
        process.wait(timeout=30)
        deadline = time.monotonic() + 360
        while not report_path.is_file() and time.monotonic() < deadline:
            failure = report_path.parent / 'logs/startup-error.log'
            if failure.is_file():
                raise RuntimeError(f'Upgrade probe reported a startup error. Inspect {failure}')
            time.sleep(1)
        if not report_path.is_file():
            raise RuntimeError(f'Upgrade failed to restart and save a report. Inspect {sandbox}')
    return json.loads(report_path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', type=Path, required=True)
    parser.add_argument('--stable', type=Path, required=True)
    parser.add_argument('--beta', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sandbox = args.output.resolve()
    sandbox.mkdir()
    portable = sandbox / 'portable'
    shutil.copytree(args.legacy.resolve(), portable)
    exe = portable / 'current' / EXECUTABLE_NAME
    snapshot_name = UPDATE_CONFIG['snapshot_name']
    original_source = json.loads((exe.parent / snapshot_name).read_text(encoding='utf-8'))['url']
    assert original_source.rstrip('/') == UPDATE_CONFIG['url']
    stable = verify(args.stable, 'stable', VERSION)
    beta = verify(args.beta, 'beta', VERSION)
    assert stable['SHA256'] != beta['SHA256']
    channel_assets = {'stable': [stable], 'beta': [beta]}
    served = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlsplit(self.path).path
            for channel in channel_assets:
                prefix = urlsplit(update_source_config(channel)['url']).path
                if route == prefix + UPDATE_CONFIG['feed_name']:
                    body = json.dumps({'Assets': channel_assets[channel]}).encode()
                    served.append(route)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            self.send_error(404)

        def log_message(self, *_args):
            pass

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = 'http://127.0.0.1:' + str(server.server_port)
            for channel, assets in channel_assets.items():
                source = origin + urlsplit(update_source_config(channel)['url']).path
                result = worker_check(exe, source)
                assert result['event'] == 'found', result
                assert result['value']['target']['SHA256'] == assets[0]['SHA256'], result
            # The previous release's existing local smoke entry exercises its real
            # worker, download, title-button confirmation and updater restart.
            legacy_feed = sandbox / 'legacy-feed'
            legacy_feed.mkdir()
            package = args.stable.resolve() / stable['FileName']
            os.link(package, legacy_feed / package.name)
            (legacy_feed / UPDATE_CONFIG['feed_name']).write_text(
                json.dumps({'Assets': [stable]}), encoding='utf-8')
            report = await_migration(portable, legacy_feed, sandbox)
            assert report == {
                'from': '1.9.2', 'downloaded': True, 'to': VERSION,
                'restarted': True, 'data_preserved': True,
                'next_source': update_source_config()['url'],
            }, report
            source = origin + urlsplit(report['next_source']).path
            assert worker_check(exe, source)['event'] == 'none'
            channel_assets['stable'] = []
            assert worker_check(exe, source)['event'] == 'none'
            # A retracted channel can expose an older valid version again.
            channel_assets['stable'] = [dict(stable, Version='1.9.2',
                                             FileName=stable['FileName'].replace(VERSION, '1.9.2'))]
            assert worker_check(exe, source)['event'] == 'none'
            missing = worker_check(exe, origin + '/missing/')
            assert 'error' in missing and 'event' not in missing, missing
        finally:
            server.shutdown()
            thread.join()
    report.update(legacy_source=original_source, requests=served, beta_isolated=True,
                  empty_feed=True, no_downgrade=True, unavailable_feed=True)
    result = sandbox / 'internal-update-smoke.json'
    result.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(result)


if __name__ == '__main__':
    main()
