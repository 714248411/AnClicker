"""Stop/error regressions. All native input and hooks are mocked."""
import os
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from instructions.common import actions
from instructions.common.key_wait import wait_for_key
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec
from test.test_hidden_stop import host, pump_until, wait_for_finish


def execute(kind, context, params):
    return get_instruction_spec(kind).create_executor().execute(
        context, CommandRecord(1, kind, params))


@pytest.mark.parametrize('cancel_on', ['press', 'interval'])
@pytest.mark.parametrize('button', ['左键', '侧键1'])
def test_click_loop_stops_and_releases_inputs(cancel_on, button):
    context = ExecutionContext()
    events = []
    gui = SimpleNamespace(FAILSAFE=True, keyDown=Mock(), keyUp=Mock(),
                          mouseDown=Mock(), mouseUp=Mock(), failSafeCheck=Mock())
    positive_waits = []
    def wait(seconds, actual):
        assert actual is context
        if seconds:
            positive_waits.append(seconds)
            if len(positive_waits) == (1 if cancel_on == 'press' else 2):
                context.stop_requested = True
        return not context.stop_requested
    context.metadata['wait_interruptibly'] = wait
    with patch.object(actions, 'pyautogui_module', return_value=gui), \
         patch('recorded_input.button_event', side_effect=lambda ctx, btn, down, backend: events.append(down)):
        assert execute('鼠标点击', context, {
            '鼠标': button, '次数': 5, '按压': 100, '间隔': 100, '辅助键': 'ctrl'}) is False
    if button == '左键':
        gui.mouseDown.assert_called_once()
        gui.mouseUp.assert_called_once_with(button='left', _pause=False)
    else:
        assert events == [True, False]
    gui.keyUp.assert_called_once_with('ctrl', _pause=False)
    assert gui.FAILSAFE is True


def test_keyboard_combo_error_releases_all_attempted_keys():
    context = ExecutionContext()
    held = set()
    release_order = []
    def down(key):
        if key == 'a':
            raise RuntimeError('simulated fail-safe')
        held.add(key)
    def up(key, **kwargs):
        assert gui.FAILSAFE is False
        release_order.append(key)
        held.discard(key)
    gui = SimpleNamespace(FAILSAFE=True, keyDown=Mock(side_effect=down), keyUp=Mock(side_effect=up))
    with patch.object(actions, 'pyautogui_module', return_value=gui):
        with pytest.raises(RuntimeError, match='fail-safe'):
            execute('按下键盘', context, {'按键': 'ctrl+a'})
    assert not held
    assert release_order == ['a', 'ctrl']
    assert gui.FAILSAFE is True


def test_keyboard_long_hold_stops_and_releases():
    context = ExecutionContext()
    gui = SimpleNamespace(FAILSAFE=True, keyDown=Mock(), keyUp=Mock())
    entered = threading.Event()
    gui.keyDown.side_effect = lambda key: entered.set()
    with patch.object(actions, 'pyautogui_module', return_value=gui):
        worker = threading.Thread(target=lambda: execute('按下键盘', context, {
            '按键': 'ctrl', '按压时长': 3600000}), daemon=True)
        worker.start()
        try:
            assert entered.wait(2)
            context.stop_requested = True
            worker.join(1)
            assert not worker.is_alive()
        finally:
            context.stop_requested = True
    gui.keyUp.assert_called_once_with('ctrl', _pause=False)


def test_release_error_does_not_skip_other_keys():
    released = []
    def up(key, **kwargs):
        if key == 'a':
            raise OSError('simulated release error')
        released.append(key)
    gui = SimpleNamespace(FAILSAFE=True, keyUp=up)
    actions.release_inputs(ExecutionContext(), gui, keys=['ctrl', 'a'])
    assert released == ['ctrl'] and gui.FAILSAFE is True


def test_mouse_native_error_releases_button_and_modifier():
    context = ExecutionContext()
    gui = SimpleNamespace(FAILSAFE=True, keyDown=Mock(), keyUp=Mock(),
                          mouseDown=Mock(side_effect=RuntimeError('native mouse failure')), mouseUp=Mock())
    with patch.object(actions, 'pyautogui_module', return_value=gui):
        with pytest.raises(RuntimeError, match='native mouse failure'):
            execute('鼠标点击', context, {'辅助键': 'ctrl'})
    gui.mouseUp.assert_called_once_with(button='left', _pause=False)
    gui.keyUp.assert_called_once_with('ctrl', _pause=False)
    assert gui.FAILSAFE is True


@pytest.mark.parametrize('signal', ['stop', 'target'])
def test_windows_key_wait_removes_only_its_hook(monkeypatch, signal):
    context = ExecutionContext()
    entered = threading.Event()
    callbacks = []
    token = object()
    def add(key, callback, **kwargs):
        assert key == 'ctrl+enter'
        callbacks.append(callback)
        entered.set()
        return token
    keyboard = SimpleNamespace(add_hotkey=Mock(side_effect=add), remove_hotkey=Mock())
    monkeypatch.setitem(sys.modules, 'keyboard', keyboard)
    monkeypatch.setattr('instructions.common.key_wait.sys.platform', 'win32')
    result = []
    worker = threading.Thread(target=lambda: result.append(wait_for_key(context, 'ctrl+enter')), daemon=True)
    worker.start()
    try:
        assert entered.wait(2)
        if signal == 'stop':
            context.stop_requested = True
        else:
            callbacks[0]()
        worker.join(1)
        assert not worker.is_alive()
        assert result == [signal == 'target']
        keyboard.remove_hotkey.assert_called_once_with(token)
    finally:
        context.stop_requested = True
        worker.join(1)


@pytest.mark.parametrize('signal', ['stop', 'target', 'dead'])
def test_mac_key_wait_cleans_listener(monkeypatch, signal):
    context = ExecutionContext()
    instances = []
    class Listener:
        def __init__(self, on_press):
            self.on_press = on_press
            self.stopped = self.joined = False
            instances.append(self)
        def start(self):
            if signal == 'stop': context.stop_requested = True
            elif signal == 'target': self.on_press('enter')
        def is_alive(self): return signal != 'dead'
        def stop(self): self.stopped = True
        def join(self, timeout): self.joined = True
    backend = SimpleNamespace(Listener=Listener, Key=SimpleNamespace(enter='enter'))
    monkeypatch.setitem(sys.modules, 'pynput', SimpleNamespace(keyboard=backend))
    monkeypatch.setattr('instructions.common.key_wait.sys.platform', 'darwin')
    if signal == 'dead':
        with pytest.raises(RuntimeError, match='键盘监听已停止'):
            wait_for_key(context, 'enter')
    else:
        assert wait_for_key(context, 'enter') is (signal == 'target')
    assert instances[0].stopped and instances[0].joined


@pytest.mark.parametrize('kind', ['鼠标点击', '按下键盘', '按键等待'])
def test_cancelled_context_sends_no_input(kind):
    with patch.object(actions, 'pyautogui_module') as gui:
        execute(kind, ExecutionContext(stop_requested=True), {})
    gui.assert_not_called()


@pytest.mark.parametrize('kind', ['鼠标点击', '按下键盘', '按键等待'])
def test_editor_uses_cancellable_worker(kind):
    from instruction_workspace import InstructionWorkspace
    from qt_compat.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    spec = get_instruction_spec(kind)
    editor = spec.create_editor()
    context = ExecutionContext()
    owner = SimpleNamespace(_editor_context=lambda: context,
                            statusMessage=Mock(), _show_error=Mock())
    InstructionWorkspace._connect_editor_test(owner, editor, spec)
    with patch('instructions.common.test_runner.run_cancellable_test',
               side_effect=lambda *args: setattr(context, 'stop_requested', True)) as run:
        editor.test_requested.emit(editor.get_draft())
    run.assert_called_once()
    owner._show_error.assert_not_called()
    owner.statusMessage.emit.assert_called_with(f'{kind}测试已取消')
    editor.deleteLater()
    app.processEvents()


@pytest.mark.parametrize('kind', ['鼠标点击', '按下键盘', '按键等待'])
def test_main_window_stop_finishes_native_instruction(host, monkeypatch, kind):
    entered = threading.Event()
    gui = SimpleNamespace(FAILSAFE=True, mouseDown=Mock(side_effect=lambda **kw: entered.set()),
                          mouseUp=Mock(), keyDown=Mock(side_effect=lambda key: entered.set()), keyUp=Mock())
    keyboard = SimpleNamespace(add_hotkey=Mock(side_effect=lambda *a, **kw: entered.set() or 'owned'),
                               remove_hotkey=Mock())
    monkeypatch.setitem(sys.modules, 'keyboard', keyboard)
    monkeypatch.setattr(actions, 'pyautogui_module', lambda: gui)
    params = {'鼠标点击': {'次数': 5, '按压': 3600000},
              '按下键盘': {'按键': 'ctrl', '按压时长': 3600000},
              '按键等待': {'按键': 'enter'}}[kind]
    host.execution_services = {'悬停后点击': lambda context, command: execute(kind, context, params)}
    assert host.start()
    pump_until(entered.is_set)
    host.global_shortcut_key('终止线程')
    wait_for_finish(host)
    assert host._runtime_error_box is None
    if kind == '鼠标点击':
        gui.mouseDown.assert_called_once()
        gui.mouseUp.assert_called_once()
    elif kind == '按下键盘':
        gui.keyUp.assert_called_once_with('ctrl', _pause=False)
    else:
        keyboard.remove_hotkey.assert_called_once_with('owned')
