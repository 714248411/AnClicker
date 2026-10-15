import os, json, hashlib, urllib.request, zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
print('Publishing credentials configured:',all(os.environ.get(key) for key in ('QINIU_ACCESS_KEY','QINIU_SECRET_KEY')))
cache=root/'.local/cache';target=cache/'dotnet'
if not (target/'dotnet.exe').exists():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json',timeout=60) as response:
        metadata=json.load(response)
    version=metadata['latest-sdk']
    sdk=next(s for r in metadata['releases'] for s in r.get('sdks',[r['sdk']]) if s['version']==version)
    asset=next(f for f in sdk['files'] if f['rid']=='win-x64' and f['url'].endswith('.zip'))
    archive=cache/'dotnet-sdk.zip'
    with opener.open(asset['url'],timeout=120) as response, archive.open('wb') as out:
        while data:=response.read(1024*1024):out.write(data)
    assert hashlib.sha512(archive.read_bytes()).hexdigest().lower()==asset['hash'].lower()
    with zipfile.ZipFile(archive) as z:z.extractall(target)
    print('Installed local .NET SDK',version)
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('https://updates.ytsoftware.cn/an-clicker/win-x64/releases.win-x64.json',timeout=30) as response:
    data=response.read();(root/'artifacts/validation/remote-feed.json').write_bytes(data)
    feed=json.loads(data);print('Public versions:',[a.get('Version') for a in feed.get('Assets',[])])
