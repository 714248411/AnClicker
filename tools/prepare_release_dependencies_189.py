"""Restore public build tools and the locked WebSocket dependency locally."""
import base64, hashlib, io, json, os, subprocess, tarfile, urllib.request, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.local/cache'; CACHE.mkdir(parents=True,exist_ok=True)
def download(url, target):
 print('DOWNLOAD '+url, flush=True)
 with urllib.request.urlopen(url, timeout=90) as response, target.open('wb') as output:
  while True:
   block=response.read(1024*1024)
   if not block: break
   output.write(block)
 return target
sdk=CACHE/'dotnet'
if not (sdk/'dotnet.exe').is_file():
 metadata=json.load(urllib.request.urlopen('https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json',timeout=90))
 version=metadata['latest-sdk']
 release=next(sdk for release in metadata['releases'] for sdk in release.get('sdks',[release.get('sdk',{})]) if sdk.get('version')==version)
 asset=next(f for f in release['files'] if f.get('rid')=='win-x64' and f['name'].endswith('.zip'))
 archive=download(asset['url'],CACHE/('dotnet-sdk-'+version+'-win-x64.zip'))
 assert hashlib.sha512(archive.read_bytes()).hexdigest().lower()==asset['hash'].lower()
 sdk.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  assert all((sdk/n).resolve().is_relative_to(sdk.resolve()) for n in z.namelist())
  z.extractall(sdk)
 print('PASS verified .NET SDK '+version,flush=True)
lock=json.loads((ROOT/'integrations/yingdao/package-lock.json').read_text())
record=lock['packages']['node_modules/ws']; target=ROOT/'integrations/yingdao/node_modules/ws'
if not (target/'index.js').exists():
 archive=download(record['resolved'],CACHE/'ws-8.22.1.tgz')
 assert 'sha512-'+base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()==record['integrity']
 target.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar.getmembers():
   if not member.isfile(): continue
   relative=Path(member.name).relative_to('package'); dest=target/relative
   assert dest.resolve().is_relative_to(target.resolve())
   dest.parent.mkdir(parents=True,exist_ok=True)
   dest.write_bytes(tar.extractfile(member).read())
 print('PASS locked ws dependency',flush=True)
env=dict(os.environ,DOTNET_ROOT=str(sdk),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
env['PATH']=str(sdk)+os.pathsep+env.get('PATH','')
for key,value in {'ProgramFiles':'C:/Program Files','ProgramFiles(x86)':'C:/Program Files (x86)','ProgramData':'C:/ProgramData','APPDATA':'C:/Users/Administrator/AppData/Roaming','LOCALAPPDATA':'C:/Users/Administrator/AppData/Local','USERPROFILE':'C:/Users/Administrator','SystemRoot':'C:/Windows'}.items(): env.setdefault(key,value)
subprocess.run([str(sdk/'dotnet.exe'),'tool','restore'],cwd=ROOT,env=env,check=True,timeout=300)
print('PASS local Velopack build tools ready',flush=True)
