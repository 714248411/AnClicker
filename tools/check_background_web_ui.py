import sys,time,threading
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import QTimer
from anclicker.instructions.registry import iter_instruction_specs
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_editors import background_web as ui
app=QApplication.instance() or QApplication([])
pages=[{'id':'b2','cdpKey':'saved','title':'测试网页','url':'https://example.test','session':'new','engine':'内置'}]
class Bridge:
 def __init__(self): self.calls=[]
 def execute(self,cmd,**kw):
  self.calls.append(cmd);time.sleep(.12);return {'result':pages}
bridge=Bridge()
def pump(predicate):
 end=time.monotonic()+3
 while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.01)
 assert predicate()
with patch.object(ui,'get_bridge',return_value=bridge), patch.object(ui,'discover_endpoints',return_value=[]):
 for spec in iter_instruction_specs('网页后台操作'):
  old=dict(pages[0],id='b1',session='old')
  params={'browserWindow':old,'points':'40,50'} if '点击' in spec.type_id else {'browserWindow':old}
  before_construct=len(bridge.calls)
  e=spec.create_editor(draft=InstructionDraft(spec.type_id,params))
  assert len(bridge.calls)==before_construct, "refresh must be deferred until the event loop"
  if spec.type_id == "后台网页按键":
   assert e.get_draft().parameters["interval"] == .1
   e._controls["interval"].setValue(.25)
   assert e.get_draft().parameters["interval"] == .25
  before=len(bridge.calls);pump(lambda:len(bridge.calls)>before and not e._refreshing)
  assert len(bridge.calls)==before+1
  assert e.get_draft().parameters['browserWindow']==pages[0]
  before=len(bridge.calls)
  with patch.object(ui.QInputDialog,'getText',return_value=('https://example.test',True)):e.open_web()
  pump(lambda:len(bridge.calls)>before and not e._refreshing)
  assert bridge.calls[-1]['id']=='acOpenCdpPage'
  e.show();app.processEvents()
  folder=Path('artifacts/validation/background-web');folder.mkdir(parents=True,exist_ok=True)
  e.grab().save(str(folder/(spec.type_id+'.png')))
  e.refresh_windows();e.close();e.deleteLater();app.processEvents();time.sleep(.15);app.processEvents()
 print('PASS async single refresh, persisted selection, open web button, closing during refresh, screenshots')
