import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.instruction_helpers.window_trigger_wait import wait_for_trigger
app=QApplication([])
e=get_instruction_spec('窗口中键激活').create_editor()
assert e.operation.currentText()=='中键'
assert [e.operation.itemText(i) for i in range(e.operation.count())]==['左键','右键','中键','键盘按键','任意键盘按键']
e.operation.setCurrentText('键盘按键')
e.trigger_key.setText('f8')
d=e.get_draft();e.load_draft(d);assert e.get_draft().parameters==d.parameters
assert 'X' not in d.parameters and '次数' not in d.parameters and '窗口' not in d.parameters
e.close()
from pynput import mouse,keyboard
class Listener:
    def __init__(self,**kwargs):self.callbacks=kwargs;self.stopped=False
    def start(self):
        if 'on_click' in self.callbacks:self.callbacks['on_click'](0,0,selected,True)
        else:
            self.callbacks['on_press'](SimpleNamespace(vk=119))
            self.callbacks['on_release'](SimpleNamespace(vk=119))
    def stop(self):self.stopped=True
    def join(self,**kwargs):pass
    def is_alive(self):return True
for name,selected in [('左键',mouse.Button.left),('右键',mouse.Button.right),('中键',mouse.Button.middle),('键盘按键',None)]:
    with patch.object(mouse,'Listener',Listener),patch.object(keyboard,'Listener',Listener):
        assert wait_for_trigger(ExecutionContext(),{'触发按键':name,'触发键':'f8'})
print('PASS: default middle, five choices, settings roundtrip, wait-only UI, mouse and keyboard release triggers')
