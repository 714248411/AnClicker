import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock, patch
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.窗口键鼠.窗口文本输入 import executor as m
app=QApplication([])
e=get_instruction_spec('窗口文本输入').create_editor()
e.target={'窗口句柄':'12'}
e.fields['X'].setValue(20); e.fields['Y'].setValue(30)
e.content.setPlainText('测试内容')
e.show();app.processEvents()
assert e.pick_start.isVisible()
assert e.fields['X'].mapTo(e,e.fields['X'].rect().topLeft()).y() < e.content.mapTo(e,e.content.rect().topLeft()).y()
d=e.get_draft();e.load_draft(d);assert e.get_draft().parameters==d.parameters
e.close()
for screen in (False,True):
    events=[];api=Mock();w=Mock();w.size.return_value=(500,500)
    w.gui.ClientToScreen.side_effect=lambda h,p:(p[0]+100,p[1]+200)
    api.click.side_effect=lambda **kw:events.append('click')
    c=ExecutionContext()
    with patch.object(m.actions,'wait_interruptibly'), patch.object(m,'keyboard_input',side_effect=lambda *a:events.append('text')):
        m.InstructionExecutor.perform(api,w,{'窗口句柄':'12'},d.parameters,c,screen)
    assert events==['click','text']
    api.moveTo.assert_called_with(*( (120,230) if screen else (20,30)))
c=ExecutionContext()
with patch.object(m.actions,'wait_interruptibly',side_effect=lambda *a:setattr(c,'stop_requested',True)),patch.object(m,'keyboard_input') as text:
    try:m.InstructionExecutor.perform(api,w,{'窗口句柄':'12'},d.parameters,c)
    except RuntimeError:pass
    text.assert_not_called()
print('PASS: input point UI/order/roundtrip, front and background click before text, cancellation')
