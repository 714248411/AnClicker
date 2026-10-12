import os,sys,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'packaging')]
import psutil
for p in psutil.process_iter():
 try:
  if p.environ().get('ANCLICKER_DATA_DIR','')==r'C:\Users\Administrator\AppData\Local\Temp\velopack-release-gate-dmwcnjp4\onedir\data':
   p.kill()
 except (psutil.Error,OSError):pass
from info import APP_ID,UPDATE_CONFIG,CURRENT_VERSION
from 发布门槛 import ReleaseContext,validate_release
from build_velopack import export_portable
out=root/'release/win-1.4.7-20261012-navigation'
c=ReleaseContext(root,root/'dist/velopack/AnClicker',out,out/UPDATE_CONFIG['portable_name'],APP_ID,APP_ID,CURRENT_VERSION.removeprefix('v'),'win-x64')
start=time.monotonic()
validate_release(c)
print('Verified elapsed:',time.monotonic()-start,flush=True)
print(export_portable(c.portable_zip,c.version),flush=True)
