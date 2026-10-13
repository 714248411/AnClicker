"""Upload verified native archives to an existing draft; never publish it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from info import CURRENT_VERSION


def api(path):
    request = urllib.request.Request('https://api.github.com/repos/'+os.environ['GH_REPO']+path,
        headers={'Authorization': 'Bearer '+os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    releases = api('/releases?per_page=30')
    candidates = [r for r in releases if r['name'] == 'AnClicker '+CURRENT_VERSION or r['tag_name'] == CURRENT_VERSION]
    assert len(candidates) == 1, 'Expected exactly one version draft'
    release = candidates[0]
    assert release['draft'] and release['target_commitish'] == os.environ['GITHUB_SHA']
    folder = Path('delivery')
    expected = json.loads((folder/'SHA256.json').read_text())
    results = []
    for platform in ('linux', 'mac'):
        package = folder/f'AnClicker-{CURRENT_VERSION}-{platform}.zip'
        with zipfile.ZipFile(package) as archive:
            assert archive.testzip() is None
        with package.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert digest == expected[package.name]
        assets = api('/releases/'+str(release['id'])+'/assets')
        asset = next((item for item in assets if item['name'] == package.name), None)
        if asset is None:
            url = release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(package.name)
            result = subprocess.run(['gh', 'api', '--method', 'POST', url, '--input', str(package),
                '-H', 'Content-Type: application/octet-stream'], capture_output=True, text=True, check=True, timeout=900)
            asset = json.loads(result.stdout)
        assert asset['size'] == package.stat().st_size and asset['digest'] == 'sha256:'+digest
        results.append({'name':package.name, 'size':asset['size'], 'sha256':digest})
        print('Uploaded and verified '+package.name, flush=True)
    Path('native-upload.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
