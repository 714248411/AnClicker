import json,hashlib,zipfile,requests,subprocess,os,psutil,concurrent.futures
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in psutil.process_iter(['cmdline']):
 if p.pid!=os.getpid() and any(str(a).replace('\\','/').endswith('tools/restore_update_toolchain.py') for a in p.info['cmdline'] or []):p.terminate();p.wait(5)
f=next(f for f in json.loads((root/'artifacts/validation/dotnet8-metadata.json').read_text())['releases'][0]['sdk']['files'] if f['rid']=='win-x64' and f['name'].endswith('.zip'))
u=f['url'].replace('builds.dotnet.microsoft.com','dotnetcli.blob.core.windows.net')
size=int(requests.head(u,timeout=30).headers['Content-Length']);chunk=8*1024*1024
folder=root/'.local/cache/sdk-parts';folder.mkdir(exist_ok=True)
def fetch(start):
 end=min(start+chunk,size)-1;p=folder/str(start)
 if p.exists() and p.stat().st_size==end-start+1:return p
 with requests.get(u,headers={'Range':f'bytes={start}-{end}'},timeout=(15,90)) as r:
  r.raise_for_status();assert r.status_code==206
  p.write_bytes(r.content);assert p.stat().st_size==end-start+1
 print('Downloaded chunk',start,flush=True);return p
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:parts=list(pool.map(fetch,range(0,size,chunk)))
p=root/'.local/cache/dotnet8-verified.zip'
with p.open('wb') as w:
 for part in parts:w.write(part.read_bytes())
assert hashlib.sha512(p.read_bytes()).hexdigest()==f['hash'].lower()
dest=root/'.local/cache/dotnet';dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(p) as z:z.extractall(dest)
env=dict(os.environ,DOTNET_ROOT=str(dest),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1');env['PATH']=str(dest)+os.pathsep+env.get('PATH','')
subprocess.run([str(dest/'dotnet.exe'),'tool','restore'],cwd=root,env=env,check=True)
print('PASS SDK hash and pinned vpk restore')
