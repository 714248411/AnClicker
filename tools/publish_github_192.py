"""Publish the validated 1.9.2 delivery and reviewed source archive."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['PATH'] = str(ROOT / '.local/tools/gh-2.105.0/bin') + os.pathsep + os.environ.get('PATH', '')
from tools.publish_github_171 import authenticate, api, digest

BASE = Path('C:/Users/Administrator/Desktop/AnClicker-release/v1.9.2-qiniu')
REPO = '714248411/AnClicker'
TAG = 'v1.9.2'

def main():
    results = json.loads((ROOT / 'artifacts/validation/v1.9.2/regressions.json').read_text())
    assert len(results) == 154 and all(not r['returncode'] and not r['traceback'] for r in results)
    receipt = json.loads((BASE / 'validation-publish.json').read_text(encoding='utf8'))
    delivery = json.loads((BASE / 'delivery-manifest.json').read_text())
    binary = BASE / 'delivery' / delivery['file']
    assert digest(binary) == delivery['sha256']
    assert receipt['files']['artifacts/release/delivery/' + binary.name] == [binary.stat().st_size, delivery['sha256']]
    source_script = ROOT / 'tools/package_source_192.py'
    if not source_script.exists():
        source_script.write_text((ROOT / 'tools/package_source_191.py').read_text(encoding='utf8').replace('1.9.1', '1.9.2'), encoding='utf8')
    source = ROOT / 'artifacts/source/v1.9.2/AnClicker-v1.9.2-win-DaiMa.zip'
    if not source.exists():
        subprocess.run([sys.executable, '-X', 'utf8', str(source_script)], cwd=ROOT, check=True)
    files = [binary, binary.with_suffix('.zip.sha256'), source, source.with_suffix('.zip.sha256')]
    client = authenticate()
    assert api(client, 'GET', '/user')['login'] == '714248411'
    metadata = api(client, 'GET', '/repos/' + REPO)
    assert not metadata['private'] and metadata['permissions']['push']
    releases = api(client, 'GET', '/repos/' + REPO + '/releases?per_page=100')
    release = next((r for r in releases if r['tag_name'] == TAG), None)
    notes = (ROOT / 'tools/packaging/RELEASE_NOTES.md').read_text(encoding='utf8').split('## v1.9.1')[0].strip()
    notes += '\n\n完整运行包请下载 AnClicker-v1.9.2-win.zip，完整解压到新目录后运行根目录 AnClicker.exe。DaiMa 为源码包。\n\n已通过 154 项回归及发布包启动、数据保留验收。'
    if release is None:
        release = api(client, 'POST', '/repos/' + REPO + '/releases', json={
            'tag_name': TAG, 'name': 'AnClicker 1.9.2', 'body': notes, 'draft': True})
    existing = api(client, 'GET', f"/repos/{REPO}/releases/{release['id']}/assets?per_page=100")
    for path in files:
        sha = digest(path)
        old = next((a for a in existing if a['name'] == path.name), None)
        if old:
            assert old.get('digest') == 'sha256:' + sha, 'Existing asset differs'
            continue
        print('Uploading ' + path.name, flush=True)
        with path.open('rb') as stream:
            response = client.post(release['upload_url'].split('{')[0],
                params={'name': path.name}, data=stream,
                headers={'Content-Type': 'application/octet-stream'}, timeout=(30, 1800))
        assert response.status_code == 201, f'Upload HTTP {response.status_code}'
        asset = response.json()
        assert asset['size'] == path.stat().st_size and asset.get('digest') == 'sha256:' + sha
        print('Verified ' + path.name, flush=True)
    release = api(client, 'PATCH', f"/repos/{REPO}/releases/{release['id']}",
                  json={'draft': False, 'make_latest': 'true', 'body': notes})
    verified = api(client, 'GET', f'/repos/{REPO}/releases/tags/{TAG}')
    assert not verified['draft']
    for path in files:
        asset = next(a for a in verified['assets'] if a['name'] == path.name)
        assert asset['digest'] == 'sha256:' + digest(path)
    print('PUBLISHED ' + verified['html_url'], flush=True)

if __name__ == '__main__':
    main()
