import sys,json,tempfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from info import UPDATE_CONFIG
from anclicker.app.updates.自动更新 import is_velopack_managed
proof=json.loads((ROOT/'artifacts/validation/v1.8.5/upgrade.json').read_text())
exe=Path(proof['sandbox'])/'portable/current/AnClicker.exe'
assert is_velopack_managed(exe,frozen=True)
with tempfile.TemporaryDirectory(prefix='ac-public-feed-') as td:
 folder=Path(td)
 (folder/'request.json').write_text(json.dumps({'action':'check','source':UPDATE_CONFIG['url'],'update':None}))
 subprocess.run([str(exe),'--update-worker',td],check=True,timeout=25)
 result=json.loads((folder/'result.json').read_text())
 assert result=={'event':'none','value':None},result
 (ROOT/'artifacts/validation/v1.8.5/public-client-check.json').write_text(json.dumps({'passed':True,'source':UPDATE_CONFIG['url'],'managed':True,'result':result},indent=2))
 print('PASS packaged managed client checks public Qiniu feed; current 1.8.5 is latest')
