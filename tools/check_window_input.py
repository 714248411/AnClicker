"""Safe regressions: mocked native input, real Qt editor and registry."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest.mock import Mock, patch
from anclicker.instructions.registry import get_instruction_spec
from anclicker.instructions.窗口键鼠.窗口键鼠 import executor as m
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.domain.instructions import InstructionDraft

app = QApplication.instance() or QApplication([])
spec = get_instruction_spec('窗口键鼠')
editor = spec.create_editor()
target = {'窗口句柄': '12', '窗口标题': 'test'}
editor.load_draft(InstructionDraft('窗口键鼠', {'窗口': target, '模式': '后台', '操作': '鼠标拖拽', 'X': 20, 'Y': 30, '结束X': 40, '结束Y': 50}))
assert editor.get_draft().parameters['窗口'] == target
assert editor.get_draft().parameters['结束Y'] == 50
assert not editor.pick_end.isHidden()
editor.operation.setCurrentText('组合键')
assert editor.pick_start.isHidden() and not editor.keys.isHidden()
editor.close()
from anclicker.ui.node_editor.palette import InstructionPalette
palette = InstructionPalette([spec, get_instruction_spec('窗口鼠标'), get_instruction_spec('窗口键盘')])
assert palette.tree.topLevelItem(1).text(0) == '窗口键鼠'
assert [palette.tree.topLevelItem(1).child(i).text(0) for i in range(2)] == ['窗口鼠标', '窗口键盘']
palette.close()

context = SimpleNamespace(metadata={'_background_session': object(), 'recorded_keys': {'a'}},
                          stop_requested=False, emit=Mock(), service=lambda key: None)
windows = Mock()
windows.resolve.return_value = target
windows.size.return_value = (500, 400)
windows.gui.ClientToScreen.side_effect = lambda hwnd, p: (p[0] + 100, p[1] + 200)
api = Mock()
p = {'操作': '左键双击', 'X': 20, 'Y': 30}
m.perform(api, windows, target, p, context, screen=True)
api.moveTo.assert_called_with(120, 230)
api.click.assert_called_with(button='left', clicks=2, interval=0.1)
windows.gui.ClientToScreen.side_effect = lambda hwnd, p: (p[0] + 300, p[1] + 500)
m.perform(api, windows, target, p, context, screen=True)
api.moveTo.assert_called_with(320, 530)
m.perform(api, windows, target, p, context)
api.moveTo.assert_called_with(20, 30)
api.reset_mock()
try:
    m.perform(api, windows, target, dict(p, X=500), context)
    raise AssertionError('outside allowed')
except ValueError:
    pass
api.moveTo.assert_not_called()
with patch.object(m.actions, 'wait_interruptibly', side_effect=RuntimeError('cancel')):
    try:
        m.perform(api, windows, target, dict(p, 操作='鼠标拖拽'), context)
    except RuntimeError:
        pass
api.mouseUp.assert_called_with(button='left')

# Finally restores state even if activation wait or operation fails.
gui = windows.gui
gui.GetAncestor.return_value = 12
gui.GetForegroundWindow.return_value = 99
gui.GetWindowPlacement.return_value = (0, 2, (0, 0), (0, 0), (10, 20, 510, 420))
gui.GetWindowLong.return_value = 0
gui.GetWindow.return_value = 77
gui.IsWindow.return_value = True
gui.IsIconic.return_value = True
with patch.object(m.actions, 'wait_interruptibly', side_effect=RuntimeError('cancel')):
    try:
        with m.foreground(windows, target, context):
            raise AssertionError('must not execute')
    except RuntimeError:
        pass
gui.SetWindowPlacement.assert_called_with(12, gui.GetWindowPlacement.return_value)
gui.SetForegroundWindow.assert_called_with(99)
assert any(call.args[1] == -2 for call in gui.SetWindowPos.call_args_list)
# A failed automatic binding releases its scope without changing the outer binding.
original = dict(context.metadata)
context.service = lambda key: (lambda: windows) if key == 'background_windows' else None
with patch.object(m, 'bind_background', side_effect=RuntimeError('bind failed')), patch.object(m, 'close_background') as close:
    try:
        spec.create_executor().execute_once(context, SimpleNamespace(parameters={'窗口': target, '模式': '后台'}))
        raise AssertionError('binding failure hidden')
    except RuntimeError:
        pass
    assert close.call_count == 1
    assert close.call_args.args[0].metadata.get('_background_session') is None
assert context.metadata == original
with patch.object(m, 'bind_background'), patch.object(m, 'close_background') as close, patch.object(m, 'current_backend', return_value=api):
    spec.create_executor().execute_once(context, SimpleNamespace(parameters=dict(p, 窗口=target, 模式='后台')))
    close.assert_called_once()
assert context.metadata == original
print('PASS: editor roundtrip, registry, relative coordinates, bounds, drag cleanup, foreground restore, scoped background binding')

for kind in ('窗口鼠标', '窗口键盘'):
    separate = get_instruction_spec(kind).create_editor()
    separate.show()
    app.processEvents()
    draft = separate.get_draft()
    assert draft.type_id == kind
    if kind == '窗口键盘':
        assert separate.operation.count() == 2
        assert separate.pick_start.isHidden()
        assert separate.fields['X'].isHidden()
        assert 'X' not in draft.parameters
        assert draft.parameters['操作'] == '组合键'
    else:
        assert separate.operation.findText('组合键') == -1
        assert '按键' not in draft.parameters
        assert separate.pick_start.mapTo(separate, separate.pick_start.rect().topLeft()).y() < separate.fields['X'].mapTo(separate, separate.fields['X'].rect().topLeft()).y()
    separate.load_draft(draft)
    assert separate.get_draft().parameters == draft.parameters
    separate.close()
print('PASS: split palette, operation isolation, keyboard hides coordinates, upper picker placement, draft roundtrip')
