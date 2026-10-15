import os,sys,subprocess,time
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'psutil': ('import', 'psutil', (), False),
    'APP_ID_UPDATE_CONFIG_CURRENT_VERSION': ('from', 'info', ('APP_ID', 'UPDATE_CONFIG', 'CURRENT_VERSION'), 0),
    'ReleaseContext_validate_release': ('from', '发布门槛', ('ReleaseContext', 'validate_release'), 0),
    'export_portable': ('from', 'build_velopack', ('export_portable',), 0),
})

root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'tools/packaging')]
psutil = _module_imports.load('psutil')
for p in psutil.process_iter():
 try:
  if p.environ().get('ANCLICKER_DATA_DIR','')==r'C:\Users\Administrator\AppData\Local\Temp\velopack-release-gate-dmwcnjp4\onedir\data':
   p.kill()
 except (psutil.Error,OSError):pass
APP_ID, UPDATE_CONFIG, CURRENT_VERSION = _module_imports.load('APP_ID_UPDATE_CONFIG_CURRENT_VERSION')
ReleaseContext, validate_release = _module_imports.load('ReleaseContext_validate_release')
export_portable = _module_imports.load('export_portable')
out=root/'artifacts/release/win-1.4.7-20261012-navigation'
c=ReleaseContext(root,root/'artifacts/dist/velopack/AnClicker',out,out/UPDATE_CONFIG['portable_name'],APP_ID,APP_ID,CURRENT_VERSION.removeprefix('v'),'win-x64')
start=time.monotonic()
validate_release(c)
print('Verified elapsed:',time.monotonic()-start,flush=True)
print(export_portable(c.portable_zip,c.version),flush=True)
