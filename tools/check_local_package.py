import os, sys, subprocess, json, uuid
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'APP_ID_EXECUTABLE_NAME': ('from', 'info', ('APP_ID', 'EXECUTABLE_NAME'), 0),
})

root=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
APP_ID, EXECUTABLE_NAME = _module_imports.load('APP_ID_EXECUTABLE_NAME')
app=root/'artifacts/dist/local-test'/APP_ID/EXECUTABLE_NAME
folder=root/'artifacts/validation/packaged-smoke';folder.mkdir(parents=True, exist_ok=True)
env=dict(os.environ,ANCLICKER_DATA_DIR=str(folder),ANCLICKER_SINGLETON_KEY=uuid.uuid4().hex,QT_QPA_PLATFORM='windows')
report=folder/'startup-ready.json'
report.unlink(missing_ok=True)
process=subprocess.run([str(app),'--startup-smoke-test'],env=env,cwd=folder,timeout=150)
report=folder/'startup-ready.json'
if process.returncode or not report.exists():
    error=folder/'logs/startup-error.log'
    raise RuntimeError(error.read_text(encoding='utf-8') if error.exists() else str(process.returncode))
ready=json.loads(report.read_text(encoding='utf-8'))
assert ready['ready'] and ready['rpa_validation']['excel'] and ready['rpa_validation']['browser']
assert ready['ocr_validation']['rapidocr']
print(json.dumps(ready,ensure_ascii=True,indent=2))
