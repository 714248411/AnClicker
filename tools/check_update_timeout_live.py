import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QThread,Signal
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
from anclicker.app.updates.自动更新接入 import AutoUpdateManager
class Offline(QThread):
 pending_update_found=Signal(object);update_found=Signal(object);no_update=Signal();check_skipped=Signal(str);check_failed=Signal(str)
 def run(self):
  while not self.isInterruptionRequested():time.sleep(.01)
app=QApplication([]);window=QWidget();m=AutoUpdateManager(window,check_thread_factory=Offline)
start=time.monotonic();m.check_on_startup()
while m.check_thread is not None and time.monotonic()-start<24:
 app.processEvents();time.sleep(.01)
elapsed=time.monotonic()-start
assert m.check_thread is None and m._check_expired and m._update_prompt is None and m.download_thread is None
assert 19<=elapsed<=23,elapsed
print('PASS real timer cancels offline check silently after',round(elapsed,2),'seconds')
(Path(__file__).resolve().parents[1]/f'artifacts/validation/v{__import__("info").VERSION}/live-timeout.json').write_text(json.dumps({'passed':True,'seconds':elapsed}))
