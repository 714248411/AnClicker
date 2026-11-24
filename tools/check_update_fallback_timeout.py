"""Regression: source ordering, bounded checks, retry and stale signals."""
import os, sys, time, subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.app.updates import 自动更新 as worker
from anclicker.app.updates import github_check, process_worker
from anclicker.app.updates.自动更新接入 import AutoUpdateManager
from anclicker.platform.qt_compat.QtCore import QObject, Signal
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget
app=QApplication.instance() or QApplication([])
for outcomes, expected, signal in [
 ([('none',None)], ['check'], 'none'),
 ([('found','qiniu')], ['check'], 'found'),
 ([TimeoutError(),('found','github')], ['check','github-check'], 'found'),
 ([RuntimeError(),('none',None)], ['check','github-check'], 'none'),
 ([RuntimeError(),RuntimeError()], ['check','github-check'], 'failed'),
 ([worker.UpdateCancelled()], ['check'], None),
]:
 t=worker.CheckUpdateThread(source_url='https://example.test', managed_checker=lambda:True)
 seen=[]
 t.no_update.connect(lambda:seen.append('none'))
 t.update_found.connect(lambda _:seen.append('found'))
 t.check_failed.connect(lambda _:seen.append('failed'))
 with patch.object(worker,'run_isolated',side_effect=outcomes) as run:
  t.run()
  assert [c.args[1] for c in run.call_args_list]==expected
  assert [c.kwargs['timeout'] for c in run.call_args_list]==[6,6][:len(expected)]
 assert seen==([signal] if signal else [])
for tag, newer in [('v1.9.0',True),('v1.10.0',True),('v1.8.8',False),('v1.7.1',False)]:
 response=MagicMock();response.__enter__.return_value=response
 response.json.return_value={'tag_name':tag,'body':'notes'}
 with patch.object(github_check,'VERSION','1.8.8'),patch.object(github_check.requests,'get',return_value=response):
  result=github_check.check_latest()
  assert bool(result)==newer
  if newer: assert result['ReleaseUrl'].endswith('/releases/tag/'+tag)
# Real hanging subprocess must be terminated on timeout.
original_popen=subprocess.Popen
children=[]
def hanging(*args,**kwargs):
 p=original_popen([sys.executable,'-c','import time; time.sleep(60)'],**kwargs)
 children.append(p);return p
started=time.monotonic()
with patch.object(process_worker.subprocess,'Popen',side_effect=hanging):
 try: process_worker.run_isolated(SimpleNamespace(isInterruptionRequested=lambda:False),'check','https://example.test',timeout=.2)
 except TimeoutError: pass
 else: raise AssertionError('missing timeout')
assert time.monotonic()-started<5 and children[0].poll() is not None
class Worker(QObject):
 pending_update_found=Signal(object);update_found=Signal(object);no_update=Signal();check_skipped=Signal(str);check_failed=Signal(str);finished=Signal()
 def __init__(self,parent):super().__init__(parent);self.running=False;self.cancelled=False
 def start(self):self.running=True
 def isRunning(self):return self.running
 def requestInterruption(self):self.cancelled=True
 def finish(self):self.running=False;self.finished.emit()
w=QWidget();m=AutoUpdateManager(w,check_thread_factory=Worker)
m.check_on_startup();a=m.check_thread;deadline=m._startup_deadline
m.check_for_updates(True)
assert m._startup_timer.isActive() and m._startup_deadline==deadline
m._expire_startup_check()
assert a.cancelled and m._last_progress[1]==-2
assert m._progress_dialog.progress_bar.isHidden() and not m._progress_dialog.retry_button.isHidden()
a.update_found.emit('late');assert m._available_update_info is None
a.finish()
m._progress_dialog.retry_button.click();b=m.check_thread
assert b is not a and m._startup_timer.isActive() and not m._check_result_handled
b.finish();assert m._last_progress[1]==-2 and m._check_result_handled
m.check_for_updates(True);c=m.check_thread
b.finished.emit();b.check_failed.emit('stale')
assert m.check_thread is c and not m._check_result_handled
c.check_failed.emit('offline');c.finish()
assert m._last_progress==('offline',-2)
m.cancel_for_exit()
print('PASS Qiniu priority, GitHub fallback, cancellation, version ordering, subprocess deadline/cleanup, manual deadline, retry, late/empty/stale results')


# Successful checks are reused briefly; expiration and failures recheck online.
created=[]
def factory(parent):
 instance=Worker(parent);created.append(instance);return instance
cached=AutoUpdateManager(w,check_thread_factory=factory)
cached._show_progress_dialog=lambda:None
notices=[]
cached.show_manual_update_message=lambda value,ready:notices.append(value)
cached.check_on_startup();first=created[-1]
first.update_found.emit('new-version');first.finish()
started=time.monotonic();cached.check_for_updates(True)
assert len(created)==1 and notices==['new-version','new-version']
assert time.monotonic()-started<.1
cached._successful_check_at=time.monotonic()-31
cached.check_for_updates(True);assert len(created)==2
with patch('anclicker.app.updates.自动更新接入.QMessageBox.information'):
 created[-1].no_update.emit();created[-1].finish()
 cached.check_for_updates(True);assert len(created)==2
 cached._successful_check_at=time.monotonic()-31
 cached.check_for_updates(True);assert len(created)==3
 created[-1].check_failed.emit('offline');created[-1].finish()
 cached.check_for_updates(True);assert len(created)==4
 created[-1].check_failed.emit('offline');created[-1].finish()
cached.cancel_for_exit()
print('PASS 30-second success cache, instant reuse, expiry and uncached failure retry')

if '--live' in sys.argv:
 from anclicker.platform.qt_compat.QtCore import QThread
 class Hanging(QThread):
  pending_update_found=Signal(object);update_found=Signal(object);no_update=Signal();check_skipped=Signal(str);check_failed=Signal(str)
  def run(self):
   while not self.isInterruptionRequested(): time.sleep(.01)
 live=AutoUpdateManager(w,check_thread_factory=Hanging)
 started=time.monotonic();live.check_for_updates(True)
 while live.check_thread is not None and time.monotonic()-started<24:
  app.processEvents();time.sleep(.01)
 elapsed=time.monotonic()-started
 assert live.check_thread is None and live._check_expired and 19<=elapsed<=23,elapsed
 assert live._progress_dialog.progress_bar.isHidden()
 assert not live._progress_dialog.retry_button.isHidden()
 live.cancel_for_exit()
 print('PASS real manual timeout and spinner stopped:',round(elapsed,2),'seconds')
