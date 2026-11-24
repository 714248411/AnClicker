import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock, patch
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext,CommandRecord
app = QApplication([])
names = ['窗口滚轮滑动','窗口按下键盘','窗口文本输入','窗口中键激活','窗口鼠标拖拽','窗口悬停后点击','窗口OCR点击']
for name in names:
    spec = get_instruction_spec(name)
    assert spec.category == '窗口键鼠'
    e = spec.create_editor()
    e.target = {'窗口句柄':'12'}
    draft = e.get_draft()
    assert draft.type_id == name
    e.load_draft(draft)
    assert e.get_draft().parameters == draft.parameters
    if name == '窗口文本输入': assert draft.parameters['操作'] == '输入内容'
    if name == '窗口按下键盘': assert draft.parameters['操作'] == '组合键'
    spec.create_executor()
    e.close()
from anclicker.instructions.窗口键鼠.窗口悬停后点击.executor import InstructionExecutor as Hover
from anclicker.instructions.common import actions
w = Mock(); w.size.return_value = (500,500)
api = Mock(); c = ExecutionContext()
with patch.object(actions,'wait_interruptibly') as wait:
    Hover.perform(api,w,{'窗口句柄':'12'},{'X':10,'Y':20,'结束X':30,'结束Y':40},c)
    assert [call.args for call in api.moveTo.call_args_list] == [(10,20),(30,40)]
    wait.assert_called_once_with(c,1.5)
from anclicker.instructions.窗口键鼠.窗口OCR点击.executor import InstructionExecutor as OCR, RelativeInput
w.gui.ClientToScreen.side_effect = lambda h,p:(p[0]+100,p[1]+200)
relative = RelativeInput(api,w,{'窗口句柄':'12'})
relative.screenshot((0,0,500,500))
api.screenshot.assert_called_with(region=(100,200,500,500))
relative.moveTo(10,20)
api.moveTo.assert_called_with(110,220)
with patch('anclicker.instructions.窗口键鼠.窗口OCR点击.executor.OcrExecutor') as ocr:
    OCR.perform(api,w,{'窗口句柄':'12'},{'目标文字':'确定'},c)
    p = ocr.return_value.execute_once.call_args.args[1].parameters
    assert p['点击来源'] == '重新识别' and p['区域'] == '(0, 0, 500, 500)'
from anclicker.instructions.窗口键鼠.窗口中键激活.executor import InstructionExecutor as Middle
with patch('anclicker.instructions.窗口键鼠.窗口中键激活.executor.wait_for_middle',return_value=False):
    assert Middle().execute_once(c,CommandRecord(None,'窗口中键激活')) is None
print('PASS: seven independent editors and schemas, roundtrip, hover sequence, OCR relative screenshot/click, middle cancellation')
