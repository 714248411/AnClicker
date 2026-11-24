import os, sys, ast, random, tempfile
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='offscreen'
source=Path('anclicker/app/scheduled_tasks.py').read_text(encoding='utf-8')
tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
validate=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TaskScheduler')
method=next(n for n in validate.body if isinstance(n,ast.FunctionDef) and n.name=='_validate_task')
functions.append(method)
ns=dict(datetime=datetime,timedelta=timedelta,random=random,Path=Path)
exec(compile(ast.Module(body=functions,type_ignores=[]),'scheduler','exec'),ns)
start=datetime(2030,1,4,23,0);end=start+timedelta(hours=2)
for repeat in ['每天','工作日','每周','自定义','仅一次']:
 task=dict(repeat=repeat,interval_minutes=180,random_enabled=True,random_start=start.isoformat(),random_end=end.isoformat(),next_run=(start+timedelta(minutes=10)).isoformat())
 for i in range(100):
  result=ns['next_occurrence'](task,datetime.fromisoformat(task['next_run']))
  if repeat=='仅一次':
   assert result is None;break
  a,b=map(datetime.fromisoformat,(task['random_start'],task['random_end']))
  assert a<=datetime.fromisoformat(result)<=b
  assert a.hour==23 if repeat!='自定义' else True
  if repeat=='工作日':assert a.weekday()<5
  task['next_run']=result
 task['repeat']='每天'
 result=ns['next_occurrence'](task,datetime(2035,1,1))
 assert datetime.fromisoformat(result)>datetime(2035,1,1)
# Midnight and missed-cycle handling uses today's clock window, not old dates.
for repeat, now, expected in [
 ('每天', datetime(2030,1,8,0,0), datetime(2030,1,8,10)),
 ('每天', datetime(2030,1,8,13), datetime(2030,1,9,10)),
 ('工作日', datetime(2030,1,5,0), datetime(2030,1,7,10)),
 ('每周', datetime(2030,1,8,0), datetime(2030,1,11,10)),
]:
 task=dict(repeat=repeat,random_start='2029-12-28T10:00:00',random_end='2029-12-28T12:00:00')
 a,b=ns['calendar_random_window'](task,now)
 assert a==expected and b==expected+timedelta(hours=2), (repeat,a,b)
# A stale random occurrence is resampled rather than executed outside its window.
tick=next(n for n in validate.body if isinstance(n,ast.FunctionDef) and n.name=='tick')
release_pause=next(n for n in validate.body if isinstance(n,ast.FunctionDef) and n.name=='_release_main_pause')
exec(compile(ast.Module(body=[tick,release_pause],type_ignores=[]),'scheduler','exec'),ns)
from types import SimpleNamespace
task=dict(id='expired',enabled=True,random_enabled=True,repeat='每天',random_start='2030-01-07T10:00:00',random_end='2030-01-07T12:00:00',next_run='2030-01-07T11:00:00')
saves=[]
owner=SimpleNamespace(window=SimpleNamespace(_closing=False),tasks=[task],queue=[],active=None,worker=None,save=lambda:saves.append(1))
ns['tick'](owner,datetime(2030,1,8,0,0))
assert not owner.queue and len(saves)==1
sample=task['next_run']
assert datetime(2030,1,8,10)<=datetime.fromisoformat(sample)<=datetime(2030,1,8,12)
ns['tick'](owner,datetime(2030,1,8,0,1))
assert task['next_run']==sample and len(saves)==1
# Completion advances from the range anchor, never the random sampled time.
for repeat, expected in [('每天',datetime(2030,1,5,10)),('每周',datetime(2030,1,11,10)),('工作日',datetime(2030,1,7,10))]:
 task=dict(random_enabled=True,repeat=repeat,random_start='2030-01-04T10:00:00',random_end='2030-01-04T12:00:00',next_run='2030-01-04T11:13:09')
 result=ns['next_occurrence'](task,datetime(2030,1,4,11,13,9))
 assert datetime.fromisoformat(task['random_start'])==expected
 assert expected<=datetime.fromisoformat(result)<=expected+timedelta(hours=2)
# Expired queued or safely-pausing work cannot start after its random window.
expired=dict(id='old',random_enabled=True,random_end='2030-01-04T12:00:00')
for mode in (True, False):
 for active in (True, False):
  pauses=[];statuses=[]
  main=SimpleNamespace(pause_for_schedule=pauses.append)
  owner=SimpleNamespace(window=SimpleNamespace(_closing=False,command_thread=main),tasks=[],queue=[dict(expired,pause_main=mode)],active=dict(expired,pause_main=mode) if active else None,worker=None,_paused_main=main if mode and active else None,_set_status=lambda *args:statuses.append(args))
  owner._release_main_pause=lambda:ns['_release_main_pause'](owner)
  ns['tick'](owner,datetime(2030,1,4,12,0,1))
  assert owner.active is None and not owner.queue and pauses==([False] if mode and active else []) and statuses
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'test.xlsx';p.touch()
 from types import SimpleNamespace
 owner=SimpleNamespace(tasks=[])
 task=dict(path=str(p),repeat='每天',random_enabled=True,random_start=start.isoformat(),random_end=end.isoformat(),next_run=start.isoformat(),enabled=True)
 saved=ns['_validate_task'](owner,task);saved['id']='test';owner.tasks=[saved]
 assert ns['_validate_task'](owner,saved)['next_run']==saved['next_run']
 for changes in [dict(random_end=start.isoformat()),dict(random_end=(start+timedelta(days=2)).isoformat())]:
  try:ns['_validate_task'](owner,dict(task,**changes))
  except ValueError:pass
  else:raise AssertionError('invalid range accepted')
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtCore import QObject,Signal
from anclicker.ui.scheduled_tasks_ui import ScheduleDialog
from anclicker.ui.theme import THEMES
app=QApplication.instance() or QApplication([])
class Scheduler(QObject):
 changed=Signal()
 def __init__(self):
  super().__init__();self.window=QMainWindow();self.window.view_workspace=SimpleNamespace(theme_mode='light',THEMES=THEMES);self.tasks=[];self.active=None
s=Scheduler();dialog=ScheduleDialog(s)
assert not dialog.random_enabled.isChecked()
dialog.random_enabled.setChecked(True)
assert dialog.random_range.isEnabled() and dialog.when.isEnabled()
assert dialog.when.isHidden()
assert dialog.time_form.labelForField(dialog.when).isHidden()
dialog.random_enabled.setChecked(False)
assert not dialog.when.isHidden()
assert not dialog.time_form.labelForField(dialog.when).isHidden()
dialog.random_enabled.setChecked(True)
for repeat in ['每天', '每周', '仅一次', '工作日', '自定义']:
 dialog.repeat.setCurrentText(repeat)
 for editor in (dialog.when, dialog.random_start, dialog.random_end):
  assert editor.sections['年'].isHidden() == (repeat in ('每天', '工作日', '每周'))
  assert editor.calendar_button.isHidden() == (repeat in ('每天', '工作日', '每周'))
  assert editor.weekday.isHidden() == (repeat != '每周')
  assert not editor.sections['时'].isHidden()
 assert f'跟随重复方式：{repeat}' in dialog.random_tip.text()
dialog.repeat.setCurrentText('每周')
dialog.random_start.weekday.setCurrentIndex(4)
assert dialog.random_start.dateTime().date().dayOfWeek()==5
assert dialog.when.weekday.currentIndex()==4
dialog.repeat.setCurrentText('自定义')
dialog.interval.setValue(120)
assert '120 分钟' in dialog.random_tip.text()
dialog.advanced_button.setChecked(True)
dialog.show()
app.processEvents()
for editor in (dialog.when, dialog.random_start, dialog.random_end):
 assert 'QLineEdit#scheduleDateSection' in editor.styleSheet()
 assert editor.sections['年'].width() >= editor.sections['年'].fontMetrics().horizontalAdvance('2030')+10
Path('artifacts/validation/schedule-random').mkdir(parents=True,exist_ok=True)
dialog.grab().save('artifacts/validation/schedule-random/light.png')
old_start=dialog.random_start.dateTime()
old_end=dialog.random_end.dateTime()
dialog.when.setDateTime(old_start.addDays(1))
assert dialog.random_start.dateTime()==dialog.when.dateTime()
assert dialog.random_end.dateTime()==old_end.addDays(1)
dialog.random_start.setDateTime(old_start.addDays(2))
assert dialog.when.dateTime()==dialog.random_start.dateTime()
assert dialog.random_end.dateTime()==old_end.addDays(2)
dialog.new_task();assert not dialog.random_enabled.isChecked() and dialog.when.isEnabled()
dialog._set_editable(False)
assert not dialog.random_enabled.isEnabled() and not dialog.random_range.isEnabled()
dialog.deleteLater()
s.window.view_workspace.theme_mode='dark'
dark_dialog=ScheduleDialog(s)
dark_dialog.random_enabled.setChecked(True)
assert dark_dialog.random_range.isEnabled()
dark_dialog.deleteLater()
from anclicker.ui.generated.windows.mainwindow_ui import Ui_MainWindow
window=QMainWindow();ui=Ui_MainWindow();ui.setupUi(window)
assert ui.menu_4.title()=='设置'
window.deleteLater()
print('PASS: random windows, recurrence, weekdays, missed periods, persistence, invalid ranges and UI controls')
