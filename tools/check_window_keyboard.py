import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock, patch
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication, QDialog
from anclicker.platform.qt_compat.QtCore import QEvent, Qt
from anclicker.platform.qt_compat.QtGui import QKeyEvent
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_editors.窗口键鼠.窗口键盘 import InstructionEditor, KeyCapture
from anclicker.instructions.窗口键鼠.窗口键盘 import executor as module
app = QApplication.instance() or QApplication([])
target = {'窗口句柄': '12'}
for params in ({'操作':'输入内容', '内容':'中文测试\n{{name}}'}, {'操作':'组合键', '按键':'Ctrl + F12', '按键码':[162,123]}):
    params.update({'窗口':target, '模式':'后台'})
    editor = InstructionEditor(draft=InstructionDraft('窗口键盘', params))
    editor.show()
    app.processEvents()
    for key, value in params.items():
        assert editor.get_draft().parameters[key] == value
    assert editor.content.isVisible() == (params['操作'] == '输入内容')
    assert editor.record_button.isVisible() == (params['操作'] == '组合键')
    editor.keys.setCurrentText('enter')
    assert not editor.recorded_codes
    editor.close()
# Read a real native virtual-key sequence through Qt, with no global hook or external input.
for keys in ([(Qt.Key_Control,162),(Qt.Key_F12,123)], [(Qt.Key_Escape,27)], [(Qt.Key_Tab,9)], [(Qt.Key_Plus,107)]):
    dialog = KeyCapture()
    for key, vk in keys:
        app.sendEvent(dialog, QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, 0, vk, 0, ''))
    for key, vk in reversed(keys):
        app.sendEvent(dialog, QKeyEvent(QEvent.KeyRelease, key, Qt.NoModifier, 0, vk, 0, ''))
    assert dialog.result() == QDialog.Accepted
    assert dialog.codes == [vk for key,vk in keys]
    dialog.close()
context = SimpleNamespace(stop_requested=False, variables={'name':'Alice'})
api = Mock()
module.keyboard_input(api, {'按键码':[162,107]}, context)
assert [call.args[0] for call in api.keyDown.call_args_list] == ['win32:162','win32:107']
assert [call.args[0] for call in api.keyUp.call_args_list] == ['win32:107','win32:162']
api.reset_mock()
api.keyDown.side_effect = [None, RuntimeError('failed')]
try:
    module.keyboard_input(api, {'按键码':[162,123]}, context)
except RuntimeError:
    pass
assert api.keyUp.call_count == 2
with patch.object(module, 'native_key') as native:
    module.keyboard_input(api, {'按键码':[165,13]}, context, screen=True)
    assert [call.args for call in native.call_args_list] == [(165,False),(13,False),(13,True),(165,True)]
module.keyboard_input(api, {'操作':'输入内容','内容':'中文\n{{name}}'}, context)
api.write.assert_called_with('中文\nAlice')
with patch('pynput.keyboard.Controller') as factory:
    module.keyboard_input(api, {'操作':'输入内容','内容':'中文\n{{name}}'}, context, screen=True)
    assert ''.join(call.args[0] for call in factory.return_value.type.call_args_list) == '中文\nAlice'
print('PASS: native key capture, special keys, text and key roundtrip, foreground/background dispatch, Unicode variables, release after failure')

# This probe does not enter app.exec(); explicitly perform the normal aboutToQuit cleanup.
from anclicker.platform.background_preload import close_preload
close_preload()
