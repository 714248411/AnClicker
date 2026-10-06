"""No real input is sent: listeners and clicks are controlled test doubles."""
import os
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from instruction_workspace import InstructionWorkspace
from instructions.common import actions
from instructions.common.middle_wait import wait_for_middle
from instructions.common.test_runner import CancellableTestDialog
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec


@pytest.fixture
def backend(monkeypatch):
    instances = []
    class Listener:
        def __init__(self, on_click):
            self.callback = on_click
            self.alive = False
            self.stopped = False
            self.joined = False
            instances.append(self)
        def start(self):
            self.alive = True
        def is_alive(self):
            return self.alive
        def stop(self):
            self.alive = False
            self.stopped = True
        def join(self, timeout):
            self.joined = True
    mouse = SimpleNamespace(Listener=Listener, Button=SimpleNamespace(middle='middle', left='left'))
    monkeypatch.setitem(sys.modules, 'pynput.mouse', mouse)
    return instances


def test_wait_cancel_removes_listener_without_click(backend):
    ctx = ExecutionContext()
    timer = threading.Timer(.06, lambda: setattr(ctx, 'stop_requested', True))
    timer.start()
    try:
        started = time.monotonic()
        assert wait_for_middle(ctx) is False
        assert time.monotonic() - started < 1
        assert backend[0].stopped and backend[0].joined
    finally:
        timer.join()


def test_only_middle_release_activates_and_unhooks(backend):
    ctx = ExecutionContext()
    def trigger():
        while not backend:
            time.sleep(.001)
        listener = backend[0]
        listener.callback(0, 0, 'left', False)
        listener.callback(0, 0, 'middle', True)
        time.sleep(.06)
        listener.callback(0, 0, 'middle', False)
    thread = threading.Thread(target=trigger)
    thread.start()
    try:
        assert wait_for_middle(ctx) is True
        assert backend[0].stopped and backend[0].joined
    finally:
        thread.join()


@pytest.mark.parametrize('mode,clicks', [('模拟点击', 3), ('结束等待', 0)])
def test_execution_modes(mode, clicks):
    gui = SimpleNamespace(click=Mock())
    with patch('instructions.common.middle_wait.wait_for_middle', return_value=True), \
            patch.object(actions, 'pyautogui_module', return_value=gui):
        result = get_instruction_spec('中键激活').create_executor().execute(
            ExecutionContext(), CommandRecord(1, '中键激活', {'类型': mode, '次数': 3}))
    assert result == 3
    assert gui.click.call_count == clicks


def test_cancellation_does_not_send_synthetic_click():
    with patch('instructions.common.middle_wait.wait_for_middle', return_value=False), \
            patch.object(actions, 'pyautogui_module') as gui:
        assert get_instruction_spec('中键激活').create_executor().execute(
            ExecutionContext(), CommandRecord(1, '中键激活', {})) is None
    gui.assert_not_called()


@pytest.mark.parametrize('cancel', ['button', 'escape', 'close'])
def test_editor_test_keeps_event_loop_responsive_and_cancels(backend, cancel):
    app = QApplication.instance() or QApplication([])
    spec = get_instruction_spec('中键激活')
    editor = spec.create_editor()
    ctx = ExecutionContext()
    owner = SimpleNamespace(_editor_context=lambda: ctx, statusMessage=Mock(), _show_error=Mock())
    InstructionWorkspace._connect_editor_test(owner, editor, spec)
    ticks = []
    observed = []
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: ticks.append(1))
    heartbeat.start(10)
    def stop():
        dialog = app.activeModalWidget()
        if isinstance(dialog, CancellableTestDialog):
            observed.append(dialog)
            if cancel == 'escape':
                QTest.keyClick(dialog, Qt.Key_Escape)
            elif cancel == 'close':
                dialog.close()
            else:
                dialog.cancel_button.click()
    QTimer.singleShot(150, stop)
    started = time.monotonic()
    try:
        editor.test_requested.emit(editor.get_draft())
        assert time.monotonic() - started < 2
        assert len(ticks) >= 3
        assert observed and not observed[0].worker.isRunning()
        assert ctx.stop_requested
        assert backend[0].stopped and backend[0].joined
        owner._show_error.assert_not_called()
        owner.statusMessage.emit.assert_called_with('中键激活测试已取消')
    finally:
        heartbeat.stop()
        editor.close()
        editor.deleteLater()


def test_listener_failure_returns_error_without_hanging_editor(backend, monkeypatch):
    app = QApplication.instance() or QApplication([])
    spec = get_instruction_spec('中键激活')
    editor = spec.create_editor()
    owner = SimpleNamespace(_editor_context=ExecutionContext, statusMessage=Mock(), _show_error=Mock())
    InstructionWorkspace._connect_editor_test(owner, editor, spec)
    monkeypatch.setattr(sys.modules['pynput.mouse'].Listener, 'is_alive', lambda self: False)
    try:
        editor.test_requested.emit(editor.get_draft())
        assert backend[0].stopped and backend[0].joined
        owner._show_error.assert_called_once()
    finally:
        editor.close()
        editor.deleteLater()
