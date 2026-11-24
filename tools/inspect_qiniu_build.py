import requests, json, shutil, os
from pathlib import Path
r=Path.cwd()
print('Disk free GB:',round(shutil.disk_usage(r).free/1024**3,1))
print('External credentials present:',Path('F:/下载/开机安装/AnClicker七牛云环境变量配置.txt').is_file())
for mod in ('qiniu','velopack'):
 try:__import__(mod);print(mod,'available')
 except ImportError:print(mod,'missing')
s=requests.Session()
for url in ['https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json','https://api.nuget.org/v3-flatcontainer/vpk/1.2.0/vpk.nuspec']:
 x=s.get(url,timeout=45);x.raise_for_status()
 if url.endswith('json'):
  d=x.json(); sdk=d['releases'][0]['sdk'];print('SDK',sdk['version']);print([f for f in sdk['files'] if f['rid']=='win-x64' and f['name'].endswith('.zip')]);(r/'artifacts/validation/dotnet8-metadata.json').write_text(x.text)
 else:print(x.text[:3500])
