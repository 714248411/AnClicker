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

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'CURRENT_VERSION': ('from', 'info', ('CURRENT_VERSION',), 0),
})


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
CURRENT_VERSION = _module_imports.load('CURRENT_VERSION')


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
    folder = Path('artifacts/delivery')
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
        if asset is not None and (asset['size'] != package.stat().st_size or asset.get('digest') != 'sha256:'+digest):
            # Only replace stale assets in the draft bound to this verified commit.
            subprocess.run(['gh', 'release', 'upload', CURRENT_VERSION, str(package), '--clobber',
                '--repo', os.environ['GH_REPO']], check=True, timeout=900)
            asset = next(item for item in api('/releases/'+str(release['id'])+'/assets') if item['name'] == package.name)
        if asset is None:
            url = release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(package.name)
            result = subprocess.run(['gh', 'api', '--method', 'POST', url, '--input', str(package),
                '-H', 'Content-Type: application/octet-stream'], capture_output=True, text=True, check=True, timeout=900)
            asset = json.loads(result.stdout)
        assert asset['size'] == package.stat().st_size and asset['digest'] == 'sha256:'+digest
        results.append({'name':package.name, 'size':asset['size'], 'sha256':digest})
        print('Uploaded and verified '+package.name, flush=True)
    Path('artifacts/validation').mkdir(parents=True, exist_ok=True)
    Path('artifacts/validation/native-upload.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
