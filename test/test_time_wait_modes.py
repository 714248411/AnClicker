import gc
import importlib
import os
import time
import weakref
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from instructions.models import InstructionDraft, ExecutionContext, CommandRecord
from instructions.registry import get_instruction_spec
from instruction_workspace import InstructionWorkspace
from instructions.common.test_runner import CancellableTestDialog
from node_editor.items import NodeItem, EdgeItem
from test.test_hidden_stop import host


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_modes_are_exclusive_and_ignore_inactive_target_time(app):
    spec = get_instruction_spec('时间等待')
    editor = spec.create_editor(draft=InstructionDraft('时间等待', {
        '类型': '时间等待', '时长': 5, '单位': '秒', '时间': '旧的无效值'}))
    assert editor.mode_buttons['时间等待'].isChecked()
    assert editor._controls['时间'].isHidden()
    assert editor.get_draft().parameters['时长'] == 5
    editor.mode_buttons['定时等待'].click()
    assert sum(b.isChecked() for b in editor.mode_buttons.values()) == 1
    assert editor._controls['时长'].isHidden()
    assert not editor._controls['时间'].isHidden()
    with pytest.raises(ValueError):
        editor.get_draft()
    editor._controls['时间'].setText('23:59:59')
    assert editor.get_draft().parameters['类型'] == '定时等待'
    editor.mode_buttons['随机等待'].click()
    assert editor._controls['最小'].isEnabled()
    assert not editor._controls['时长'].isEnabled()
    editor.deleteLater()


def test_five_seconds_passes_only_duration_to_wait_service():
    module = importlib.import_module('instructions.等待.时间等待.时间等待')
    wait = Mock(return_value=True)
    context = ExecutionContext(metadata={'wait_interruptibly': wait})
    module.InstructionExecutor().execute_once(context, CommandRecord(1, '时间等待', {
        '类型': '时间等待', '时长': 5, '单位': '秒', '时间': '10:54:00'}))
    wait.assert_called_once_with(5, context)


@pytest.mark.parametrize('cancel', [False, True])
def test_wait_editor_test_is_responsive_and_safe_at_completion(app, cancel):
    spec = get_instruction_spec('时间等待')
    editor = spec.create_editor(draft=InstructionDraft('时间等待', {'类型': '时间等待', '时长': 5 if cancel else .1}))
    context = ExecutionContext()
    owner = SimpleNamespace(_editor_context=lambda: context, statusMessage=Mock(), _show_error=Mock())
    InstructionWorkspace._connect_editor_test(owner, editor, spec)
    ticks = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start(10)
    if cancel:
        QTimer.singleShot(80, lambda: app.activeModalWidget().reject())
    start = time.monotonic()
    editor.test_requested.emit(editor.get_draft())
    timer.stop()
    assert time.monotonic() - start < 2
    assert len(ticks) >= 2
    assert context.stop_requested == cancel
    owner._show_error.assert_not_called()
    editor.deleteLater()


def test_real_five_second_wait_then_next_command_and_visible_window(host):
    repo = host.workspace.repository
    repo.clear()
    repo.add_command(InstructionDraft('时间等待', {'类型': '时间等待', '时长': 5, '单位': '秒', '时间': '23:59:59'}))
    repo.add_command(InstructionDraft('文本输入', {'内容': '测试不发送真实输入'}))
    called = []
    host.execution_services = {'文本输入': lambda **_: called.append(time.monotonic())}
    start = time.monotonic()
    assert host.start()
    while host.command_thread.isRunning() and time.monotonic() - start < 8:
        QApplication.processEvents()
        time.sleep(.01)
    QApplication.processEvents()
    assert not host.command_thread.isRunning()
    assert len(called) == 1 and 4.9 <= called[0] - start < 8
    assert host.isVisible()


def test_stop_during_wait_never_runs_next_instruction(host):
    repo = host.workspace.repository
    repo.clear()
    repo.add_command(InstructionDraft('时间等待', {'类型': '时间等待', '时长': 5, '单位': '秒'}))
    repo.add_command(InstructionDraft('文本输入', {'内容': '不应执行'}))
    called = []
    host.execution_services = {'文本输入': lambda **_: called.append(1)}
    assert host.start()
    time.sleep(.1)
    assert host.command_thread.stop_and_wait()
    QApplication.processEvents()
    assert not called
    assert host.isVisible()


def test_graph_backrefs_do_not_own_nodes_or_edges(app):
    for _ in range(100):
        node = NodeItem('one', 1, '时间等待', '等待', QColor('#555555'))
        other = NodeItem('two', 2, '时间等待', '等待', QColor('#555555'))
        edge = EdgeItem(node, other)
        node_ref, edge_ref = weakref.ref(node), weakref.ref(edge)
        assert node.output_port.edges == [edge]
        del edge
        assert edge_ref() is None
        assert node.output_port.edges == []
        del node, other
        gc.collect()
        assert node_ref() is None
