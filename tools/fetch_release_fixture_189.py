"""Fetch public prior source/portable fixtures for migration checks, never publish."""
import json, urllib.request, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.8.9'
for version in ('1.7.8','1.8.8'):
 request=urllib.request.Request('https://api.github.com/repos/714248411/AnClicker/releases/tags/v'+version,headers={'User-Agent':'AnClicker-release-validation'})
 with urllib.request.urlopen(request,timeout=60) as response: metadata=json.load(response)
 (OUT/('prior-'+version+'.json')).write_text(json.dumps(metadata),encoding='utf8')
 print(version,[(a['name'],a['size']) for a in metadata['assets']],flush=True)
 if version=='1.7.8':
  asset=next(a for a in metadata['assets'] if a['name']=='AnClicker-v1.7.8-win-DaiMa.zip')
  dest=ROOT/'artifacts/release/v1.7.8/public'/asset['name'];dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():
   with urllib.request.urlopen(asset['browser_download_url'],timeout=90) as response,dest.open('xb') as output:
    while True:
     chunk=response.read(1024*1024)
     if not chunk: break
     output.write(chunk)
  assert dest.stat().st_size==asset['size']
  if asset.get('digest'): assert asset['digest']=='sha256:'+hashlib.sha256(dest.read_bytes()).hexdigest()
  print('PASS public historical source fixture',flush=True)
