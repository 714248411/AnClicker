import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='offscreen'
from unittest.mock import patch
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QLabel
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.ui.agent_view import AgentView
class Database:
 def __init__(self):self.values={}
 def get_setting_value(self,key):return self.values.get(key)
 def set_setting_value(self,key,value):self.values[key]=value
class Session:
 def __init__(self):self.drafts=[];self.history=[];self.pending_plan_text=''
 def close(self):pass
app=QApplication([])
w=QWidget();w.db=Database()
with patch('anclicker.ui.agent_view.create_agent_session',Session),patch.object(AgentView,'_activate_local_model'),patch.object(AgentView,'refresh_resources'):
 v=AgentView(w);v.resize(720,650);w.resize(720,650);w.show();v.show()
 def bottom():
  QTest.qWait(120)
  bar=v.scroll.verticalScrollBar()
  assert bar.maximum()>0
  assert bar.value()==bar.maximum(),(bar.value(),bar.maximum())
 for i in range(8):v.add_message('user','用户输入 '+str(i)+'，请生成操作。'*20)
 bottom()
 v.on_event('assistant','生成完成，这是回复内容。'*160)
 bottom()
 label=v._cards[-1].findChildren(QLabel)[-1]
 label.setText(label.text()*3)
 bottom()
 bar=v.scroll.verticalScrollBar();bar.setValue(0);QTest.qWait(30)
 label.setText(label.text()+'追加布局变化'*50);QTest.qWait(120)
 assert bar.value()==0,'manual reading position was lost'
 v.on_event('assistant','新的生成结果。'*100)
 bottom()
 v.resize(500,650);bottom()
 v.hide();v.add_message('assistant','隐藏期间生成的回复。'*100);QTest.qWait(30);v.show();bottom()
 print('PASS long reply, delayed layout, manual history reading, new reply, narrow viewport and hidden-page restore',flush=True)
 os._exit(0)
