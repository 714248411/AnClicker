import os, sys, subprocess, json, uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
app=root/'dist/local-test/AnClicker/AnClicker.exe'
folder=root/'validation/packaged-smoke';folder.mkdir(exist_ok=True)
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
