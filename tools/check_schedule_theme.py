import os,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='schedule-theme-')
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtCore import QObject,Signal
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.ui.scheduled_tasks_ui import ScheduleDialog
from anclicker.ui.theme import THEMES
app=QApplication([])
class Scheduler(QObject):
 changed=Signal()
 def __init__(self,mode):
  super().__init__();self.window=QMainWindow();self.window.view_workspace=SimpleNamespace(theme_mode=mode,THEMES=THEMES);self.tasks=[];self.active=None
out=Path('artifacts/validation/schedule-theme');out.mkdir(parents=True,exist_ok=True)
for mode in ('light','dark'):
 s=Scheduler(mode);d=ScheduleDialog(s);d.resize(960,720);d.show();d.random_enabled.setChecked(True);d.repeat.setCurrentText('每周');QTest.qWait(150)
 for editor in (d.when,d.random_start,d.random_end):
  assert 'scheduleWeekday' in editor.styleSheet()
  assert editor.weekday.view().palette().base().color().name()==('#242424' if mode=='dark' else '#f5f6fa')
 d.grab().save(str(out/(mode+'.png')))
 d.random_start.weekday.showPopup();QTest.qWait(100);d.random_start.weekday.view().window().grab().save(str(out/(mode+'-popup.png')));d.random_start.weekday.hidePopup()
 d._set_editable(False);QTest.qWait(80);d.grab().save(str(out/(mode+'-readonly.png')))
 d.hide();s.window.hide()
print('PASS schedule light/dark, weekday popup, time fields and readonly styles',flush=True)
os._exit(0)
