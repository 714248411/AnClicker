import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock, patch
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
from anclicker.instructions.窗口键鼠.窗口多坐标点击.executor import InstructionExecutor
from anclicker.instructions.common import actions
app = QApplication([])
spec = get_instruction_spec('窗口多坐标点击')
e = spec.create_editor()
e.target = {'窗口句柄':'12'}
e.add_point(10,20)
e.add_point(30,40)
e.move_row(-1)
assert e.get_draft().parameters['坐标列表'] == [[30,40],[10,20]]
draft = e.get_draft()
e.load_draft(draft)
assert e.get_draft().parameters == draft.parameters
e.remove_rows()
assert e.table.rowCount() == 1
e.close()
windows = Mock()
windows.size.return_value = (100,100)
windows.gui.ClientToScreen.side_effect = lambda hwnd,p: (p[0]+200,p[1]+300)
api = Mock()
context = SimpleNamespace(stop_requested=False)
p = {'坐标列表':[[10,20],[30,40]],'间隔':0.1,'操作':'左键单击'}
with patch.object(actions,'wait_interruptibly') as wait:
    InstructionExecutor.perform(api,windows,{'窗口句柄':'12'},p,context,True)
    assert [call.args for call in api.moveTo.call_args_list] == [(210,320),(230,340)]
    assert api.click.call_count == 2
    wait.assert_called_once_with(context,0.1)
api.reset_mock()
with patch.object(actions,'wait_interruptibly',side_effect=lambda *args:setattr(context,'stop_requested',True)):
    try: InstructionExecutor.perform(api,windows,{'窗口句柄':'12'},p,context)
    except RuntimeError: pass
    assert api.click.call_count == 1
context.stop_requested = False
api.reset_mock()
try:
    InstructionExecutor.perform(api,windows,{'窗口句柄':'12'},dict(p,坐标列表=[[10,20],[100,10]]),context)
    raise AssertionError('invalid points allowed')
except ValueError: pass
api.click.assert_not_called()
print('PASS: multi-point editor, reorder/delete, roundtrip, relative sequence, interval, cancellation and bounds')
