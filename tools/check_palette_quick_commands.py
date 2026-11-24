import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMenu
from anclicker.platform.qt_compat.QtCore import QTimer
from anclicker.ui.node_editor.palette import InstructionPalette,TYPE_ID_ROLE
app=QApplication([])
specs={k:{'title':k,'category':'键鼠'} for k in ('图像点击','按下键盘','打开网页')}
p=InstructionPalette(specs);p.resize(240,500);p.show();app.processEvents()
saved=[];activated=[]
p.orderChanged.connect(lambda data:saved.append(json.loads(json.dumps(data))))
p.instructionActivated.connect(activated.append)
group=p.tree.topLevelItem(1);group.setExpanded(True);original=group.child(0);app.processEvents()
errors=[]
def choose_add():
 try:
  menu=app.activePopupWidget();assert isinstance(menu,QMenu)
  action=next(a for a in menu.actions() if a.text()=='添加到快捷功能栏')
  assert action.isEnabled();action.trigger();menu.close()
 except Exception as error:
  errors.append(error)
  if app.activePopupWidget():app.activePopupWidget().close()
QTimer.singleShot(30,choose_add)
p._show_settings_menu(p.tree.visualItemRect(original).center())
assert not errors,errors
assert original.parent() is group
assert p._quick_types==['图像点击'] and saved[-1]['quick_commands']==['图像点击']
p.add_quick_instruction('图像点击');p.add_quick_instruction('打开网页')
assert p._quick_types==['图像点击']
p.add_quick_instruction('按下键盘');p._pin_command(p._custom_quick_items['按下键盘'])
record=p.instruction_order()
q=InstructionPalette(specs);q.restore_instruction_order(record)
assert q.instruction_order()==record
q.search_edit.setText('图像');assert not q._custom_quick_items['图像点击'].isHidden()
q.tree._activate_item(q._custom_quick_items['图像点击'],0)
q.instructionActivated.connect(activated.append)
q.tree._activate_item(q._custom_quick_items['图像点击'],0)
assert activated==['图像点击']
assert q.quick_parameters('图像点击') is None
q.remove_quick_instruction('图像点击');assert '图像点击' not in q._custom_quick_items
q.set_specs(specs);assert '按下键盘' in q._custom_quick_items
q.restore_instruction_order({'groups':[]});assert not q._custom_quick_items
p.close();q.close()
print('PASS context menu add, deduplication, original entry preservation, saved order restore, search, activation, removal, rebuild and legacy settings')
