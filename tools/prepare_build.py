import os, sys, subprocess, urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ)
for k in list(env):
    if k.lower().endswith('_proxy'): env.pop(k)
cache=root/'.runtime-tools';cache.mkdir(exist_ok=True)
installer=cache/'python-3.10.11-amd64.exe'
if not installer.exists():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe',timeout=90) as r: installer.write_bytes(r.read())
target=root/'.build-python'
if not (target/'python.exe').exists():
    result=subprocess.run([str(installer),'/quiet','InstallAllUsers=0','TargetDir='+str(target),'Include_launcher=0','InstallLauncherAllUsers=0','PrependPath=0','Include_test=0','Include_doc=0','Include_tcltk=1','AssociateFiles=0','Shortcuts=0'],env=env)
    if result.returncode not in (0,3010): raise RuntimeError(result.returncode)
env['PYTHONPATH']=str(cache)
env['UV_PROJECT_ENVIRONMENT']=str(root/'.venv-build')
subprocess.run([sys.executable,'-m','uv','sync','--python',str(target/'python.exe'),'--group','release','--frozen'],cwd=root,env=env,check=True)
