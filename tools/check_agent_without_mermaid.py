import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide2.QtWidgets import QApplication,QWidget,QPushButton
from anclicker.ui.agent_view import AgentView
class MemoryDB:
 def get_setting_value(self,key):return None
 def set_setting_value(self,key,value):pass
app=QApplication([]);window=QWidget();window.db=MemoryDB()
view=AgentView(window);view.update_buttons()
labels=[button.text() for button in view.findChildren(QPushButton)]
assert not any('mermaid' in label.lower() for label in labels)
assert '导出标准 JSON' in labels and '导入 API / JSON 草稿' in labels
assert not hasattr(view,'mermaid_import_button') and not hasattr(view,'mermaid_export_button')
print('PASS isolated Qt interface: Mermaid removed; JSON and draft controls remain')
