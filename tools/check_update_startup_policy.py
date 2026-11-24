import sys,time,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QObject,Signal
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
from anclicker.app.updates.自动更新接入 import AutoUpdateManager
from anclicker.app.updates.自动更新 import is_velopack_managed
from anclicker.ui.dialogs.update_notice import UpdatePrompt
app=QApplication.instance() or QApplication([])
class Worker(QObject):
 pending_update_found=Signal(object);update_found=Signal(object);no_update=Signal();check_skipped=Signal(str);check_failed=Signal(str);finished=Signal()
 def __init__(self,parent):super().__init__(parent);self.running=False;self.cancelled=False
 def start(self):self.running=True
 def isRunning(self):return self.running
 def requestInterruption(self):self.cancelled=True
 def finish(self):self.running=False;self.finished.emit()
window=QWidget();workers=[]
def factory(parent):
 w=Worker(parent);workers.append(w);return w
m=AutoUpdateManager(window,check_thread_factory=factory,download_thread_factory=lambda *a: (_ for _ in ()).throw(AssertionError('automatic download')))
notices=[];m.show_manual_update_message=lambda info,ready:notices.append((info,ready,m.show_check_message))
m._show_progress_dialog=lambda:None
with patch('anclicker.app.updates.自动更新接入.QMessageBox.warning') as warn,patch('anclicker.app.updates.自动更新接入.QMessageBox.information') as info:
 m.check_on_startup();m.check_on_startup();assert len(workers)==1
 assert m._startup_timer.interval()==20000
 m._startup_deadline=time.monotonic()-1
 workers[0].update_found.emit(SimpleNamespace(Version='99.0.0'))
 assert workers[0].cancelled and not notices and m._available_update_info is None
 workers[0].check_failed.emit('offline');assert not warn.called and not info.called
 m.check_on_startup();assert len(workers)==1
 m.check_for_updates(True);assert m._manual_check_pending
 workers[0].finish();assert len(workers)==2 and m.show_check_message
 workers[1].update_found.emit('manual');assert notices==[('manual',False,True)]
 workers[1].finish()
# A successful startup only notifies, without initiating download.
n=AutoUpdateManager(window,check_thread_factory=factory)
seen=[];n.show_manual_update_message=lambda info,ready:seen.append((info,ready,n.show_check_message))
n.check_on_startup();workers[-1].update_found.emit('startup');workers[-1].finish();n.check_on_startup()
assert seen==[('startup',False,False)] and n.download_thread is None
# No startup retry after failure; a manual click is still allowed.
f=AutoUpdateManager(window,check_thread_factory=factory);f._show_progress_dialog=lambda:None
f.check_on_startup();w=workers[-1]
with patch('anclicker.app.updates.自动更新接入.QMessageBox.warning') as warning:
 w.check_failed.emit('offline');w.finish();count=len(workers);f.check_on_startup()
 assert len(workers)==count and not warning.called
 f.check_for_updates(True);assert len(workers)==count+1;workers[-1].finish()
for dark in (False,True):
 window.view_workspace=SimpleNamespace(theme_mode='dark' if dark else 'light')
 prompt=UpdatePrompt(window,'9.0.0',notice_only=True)
 assert prompt.update_button.text()=='检查更新';prompt.close()
with tempfile.TemporaryDirectory() as td:
 root=Path(td);current=root/'current';current.mkdir();exe=current/'AnClicker.exe'
 assert not is_velopack_managed(exe,frozen=True)
 (current/'sq.version').write_text('version');(root/'Update.exe').write_bytes(b'updater')
 assert is_velopack_managed(exe,frozen=True)
 assert not is_velopack_managed(exe,frozen=False)
print('PASS startup once, 20-second deadline, silent offline/late results, manual retry, no automatic download, managed packaging')
