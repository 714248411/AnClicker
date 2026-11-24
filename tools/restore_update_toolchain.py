import json,hashlib,zipfile,requests,subprocess,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
f=next(f for f in json.loads((root/'artifacts/validation/dotnet8-metadata.json').read_text())['releases'][0]['sdk']['files'] if f['rid']=='win-x64' and f['name'].endswith('.zip'))
dest=root/'.local/cache/dotnet';dest.mkdir(parents=True,exist_ok=True)
p=root/'.local/cache/dotnet8.zip'
if not p.exists():
 with requests.get(f['url'],stream=True,timeout=(20,90)) as r:
  r.raise_for_status()
  with p.open('wb') as w:
   for chunk in r.iter_content(1024*1024):w.write(chunk)
assert hashlib.sha512(p.read_bytes()).hexdigest()==f['hash'].lower()
with zipfile.ZipFile(p) as z:z.extractall(dest)
env=dict(os.environ,DOTNET_ROOT=str(dest),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1');env['PATH']=str(dest)+os.pathsep+env.get('PATH','')
subprocess.run([str(dest/'dotnet.exe'),'tool','restore'],cwd=root,env=env,check=True)
print('PASS SDK hash and pinned vpk restore')
