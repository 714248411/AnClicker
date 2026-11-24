import os,sys,tempfile
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QHBoxLayout,QLabel
from anclicker.ui.flow_tips import FlowTips,TIPS
app=QApplication([])
window=Mock()
window.db.get_setting_value.return_value='True'
panel=QWidget()
row=QHBoxLayout(panel)
row.addWidget(QLabel('指令表格'))
tips=FlowTips(window,compact=True,setting='显示表格操作提示',tips=('第一条提示','第二条提示'))
row.addWidget(tips,1)
row.addWidget(QLabel('共 2 条指令'))
panel.resize(700,40)
panel.show()
app.processEvents()
assert tips.label.fontMetrics().height()<20
assert tips.next.width()==16
tips.advance()
assert tips.label.full_text=='第二条提示'
tips.advance()
assert tips.label.full_text=='第一条提示'
tips.set_expanded(False)
window.db.set_setting_value.assert_called_with('显示表格操作提示','False')
assert not tips.timer.isActive()
normal=FlowTips(window)
assert normal.tips==TIPS
assert normal.next.width()==22
assert normal.setting=='显示流程图操作提示'
for p in ('anclicker/ui/flow_tips.py','anclicker/ui/instruction_table.py'):
    compile((Path(__file__).resolve().parents[1]/p).read_text(encoding='utf8'),p,'exec')
print('PASS compact table tips, cycling, independent preference, hide timer, unchanged flow tips')

from unittest.mock import patch
from anclicker.platform.qt_compat.QtCore import QPoint
import anclicker.ui.flow_tips as tip_module
class Menu:
    def __init__(self,*args): pass
    def addAction(self,text,callback):
        self.text=text
        self.callback=callback
    def exec(self,position):
        assert self.text==('收起提示' if tips.expanded else '展开提示')
        self.callback()
    def deleteLater(self): pass
with patch.object(tip_module,'QMenu',Menu), patch.object(tip_module._module_imports,'load',return_value=lambda *a:None):
    tips.show_toggle_menu(QPoint())
    assert tips.expanded and not tips.isHidden()
    tips.show_toggle_menu(QPoint())
    assert not tips.expanded and tips.isHidden()
assert not tips.menu_open
print('PASS right-click expand from hidden, collapse from visible, persisted state')
