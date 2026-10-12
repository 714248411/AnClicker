import os,sys,subprocess,winreg
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('QINIU_ACCESS_KEY','QINIU_SECRET_KEY'):
    found=bool(os.environ.get(name))
    for hive,key in [(winreg.HKEY_CURRENT_USER,'Environment'),(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')]:
        try:
            with winreg.OpenKey(hive,key) as k:found=found or bool(winreg.QueryValueEx(k,name)[0])
        except OSError:pass
    print(name+' configured: '+str(found),flush=True)
env=dict(os.environ)
for k in list(env):
    if k.lower().endswith('_proxy'):env.pop(k)
env['PYTHONPATH']=str(root/'.runtime-tools')
subprocess.run([sys.executable,'-m','uv','pip','install','--target',str(root/'.runtime-tools'),'PySocks'],env=env,check=True)
