import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from qt_compat.QtCore import QCoreApplication, QEvent, QThread, Qt
from qt_compat.QtWidgets import QApplication, QComboBox, QLineEdit
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec, INSTRUCTION_SPECS


def test_start_shortcut_cannot_overlap_parameter_test(host):
    host.workspace._instruction_test_active = True
    try:
        with patch.object(host.command_thread, 'start') as start:
            assert host.start() is False
            start.assert_not_called()
    finally:
        host.workspace._instruction_test_active = False


def test_global_stop_cancels_parameter_test(host):
    context = ExecutionContext()
    host.workspace._instruction_test_active = True
    host.workspace._instruction_test_context = context
    try:
        host.global_shortcut_key('终止线程')
        assert context.stop_requested
    finally:
        host.workspace._instruction_test_active = False
        host.workspace._instruction_test_context = None


@pytest.mark.parametrize('busy', ['main', 'test', 'recording', 'web'])
def test_test_button_cannot_overlap_other_execution(host, busy):
    spec = get_instruction_spec('时间等待')
    editor = spec.create_editor()
    host.workspace._connect_editor_test(editor, spec)
    with patch.object(host.command_thread, 'isRunning', return_value=busy == 'main'), \
         patch.object(type(host.view_workspace.recording_page), 'busy', property(lambda self: busy == 'recording')), \
         patch.object(type(host.view_workspace.web_recording_page), 'busy', property(lambda self: busy == 'web')), \
         patch('instructions.common.test_runner.run_cancellable_test') as run:
        host.workspace._instruction_test_active = busy == 'test'
        try:
            editor.test_requested.emit(InstructionDraft('时间等待', {'时长': 0}))
            run.assert_not_called()
        finally:
            host.workspace._instruction_test_active = False
            editor.deleteLater()


@pytest.mark.parametrize('kind', ['多坐标点击', '移动鼠标', '滚轮滑动', '文本输入', '鼠标拖拽', '悬停后点击', '图像等待', '窗口焦点等待'])
def test_long_parameter_tests_use_cancellable_worker(kind):
    from instruction_workspace import InstructionWorkspace
    app = QApplication.instance() or QApplication([])
    spec = get_instruction_spec(kind)
    editor = spec.create_editor()
    context = ExecutionContext()
    owner = SimpleNamespace(_editor_context=lambda: context, statusMessage=Mock(), _show_error=Mock())
    InstructionWorkspace._connect_editor_test(owner, editor, spec)
    with patch('instructions.common.test_runner.run_cancellable_test',
               side_effect=lambda *args: setattr(context, 'stop_requested', True)) as run, \
         patch.object(type(spec), 'create_executor', return_value=Mock()):
        editor.test_requested.emit(InstructionDraft(kind, {}))
        run.assert_called_once()
    owner._show_error.assert_not_called()
    assert not owner._instruction_test_active
    editor.deleteLater()
    app.processEvents()


def test_close_during_parameter_test_cancels_and_waits(host):
    context = ExecutionContext()
    host.workspace._instruction_test_active = True
    host.workspace._instruction_test_context = context
    event = Mock()
    try:
        host.closeEvent(event)
        event.ignore.assert_called_once()
        event.accept.assert_not_called()
        assert context.stop_requested
    finally:
        host.workspace._instruction_test_active = False
        host.workspace._instruction_test_context = None


def test_all_parameter_editors_survive_fast_close_and_pending_callbacks(host, monkeypatch):
    errors = []
    monkeypatch.setattr(sys, 'excepthook', lambda kind, error, tb: errors.append(repr(error)))
    host.view_workspace.interface_scale.change(1)
    docking = host.view_workspace.docking
    for index, spec in enumerate(INSTRUCTION_SPECS):
        editor = spec.create_editor(parent=host, context=host.workspace._editor_context())
        key = 'parameters_stress_' + str(index)
        host.workspace._run_parameter_editor(editor, lambda draft: None, key)
        advanced = getattr(editor, 'advanced_button', None)
        if advanced is not None and advanced.isCheckable():
            advanced.setChecked(True)
            advanced.setChecked(False)
        fields = editor.findChildren(QLineEdit)
        if fields:
            fields[0].setFocus()
            QTest.keyClick(fields[0], Qt.Key_Tab)
        combos = editor.findChildren(QComboBox)
        if combos:
            combos[0].showPopup()
            combos[0].hidePopup()
        editor.reject()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()
        assert key not in docking.parameters
    assert not errors, errors


@pytest.mark.parametrize('stage', ['inputs', 'background', 'both'])
def test_resource_release_attempts_all_steps_after_failure(stage):
    from instructions.common.actions import release_execution_resources
    first = RuntimeError('input cleanup') if stage in ('inputs', 'both') else None
    second = RuntimeError('native cleanup') if stage in ('background', 'both') else None
    context = ExecutionContext()
    with patch('instructions.common.actions.release_recorded_inputs', side_effect=first) as inputs, \
         patch('background_runtime.close_background', side_effect=second) as background:
        error = release_execution_resources(context)
        inputs.assert_called_once_with(context)
        background.assert_called_once_with(context)
        assert error is (first or second)


def test_parameter_worker_reports_cleanup_failure_and_restores_output():
    from instructions.common.test_runner import _TestWorker
    output = Mock()
    context = ExecutionContext(output=output)
    worker = _TestWorker(Mock(), Mock(), context, None)
    with patch('background_runtime.close_background', side_effect=RuntimeError('native cleanup')):
        worker.run()
    assert str(worker.error) == 'native cleanup'
    assert context.output is output


def test_main_worker_cleanup_failure_still_finishes(host):
    worker = host.command_thread
    completed, messages = [], []
    worker.finished_signal.connect(completed.append)
    worker.send_message.connect(messages.append)
    worker.prepare_for_start()
    with patch.object(worker, '_commands_for_mode', return_value=[Mock()]), \
         patch.object(worker, '_load_variables', return_value={}), \
         patch.object(worker, '_persist_variables'), \
         patch.object(worker, '_execute_commands'), \
         patch('background_runtime.close_background', side_effect=RuntimeError('native cleanup')):
        worker.run()
    assert worker._active_context is None
    assert completed == ['任务已终止']
    assert any('native cleanup' in message for message in messages)


def test_variable_database_failure_is_reported_without_escaping_worker(host):
    worker = host.command_thread
    completed, messages = [], []
    worker.finished_signal.connect(completed.append)
    worker.send_message.connect(messages.append)
    worker.prepare_for_start()
    with patch.object(worker, '_commands_for_mode', return_value=[Mock()]), \
         patch.object(worker, '_load_variables', side_effect=RuntimeError('database locked')):
        worker.run()
    assert completed == ['任务未启动']
    assert any('database locked' in message for message in messages)


def test_schedule_worker_cleanup_failure_reports_completion(host):
    from scheduled_tasks import ScheduledWorker
    worker = ScheduledWorker(host, {'id': 'cleanup-test', 'path': 'unused.xlsx'})
    completed = []
    worker.completed.connect(lambda *args: completed.append(args))
    with patch.object(worker, '_run_project'), \
         patch('background_runtime.close_background', side_effect=RuntimeError('native cleanup')):
        worker.run()
    assert worker._active_context is None
    assert completed == [('cleanup-test', '运行资源释放失败：native cleanup')]
    worker.deleteLater()
