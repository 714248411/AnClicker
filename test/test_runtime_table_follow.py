"""Execution follows stable command IDs without stealing editing selections."""
import time
from threading import Event
from unittest.mock import patch

from qt_compat.QtCore import QThread
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication

from instructions.models import InstructionDraft
from test.test_hidden_stop import host


def pump_until(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
        time.sleep(.005)
    assert predicate()


def test_start_follows_real_worker_and_keeps_table_log_after_completion(host):
    host.view_workspace.show_table()
    host.checkBox_2.setChecked(False)
    host.radioButton_2.setChecked(True)
    host.spinBox.setValue(1)
    host.run_unconnected_checkbox.setChecked(True)
    host.workspace.repository.add_command(InstructionDraft('悬停后点击', {}))
    host.workspace.reload_graph()
    commands = host.workspace.repository.list_commands()
    released = [Event() for _ in commands]
    observed = []

    def execute(context, command):
        index = len(observed)
        observed.append(command.id)
        while not released[index].wait(.005) and not context.stop_requested:
            pass

    host.execution_services = {'悬停后点击': execute}
    threads = []
    follow = host.view_workspace.highlight_running_command

    def record(command_id, **kwargs):
        threads.append(QThread.currentThread())
        follow(command_id, **kwargs)

    with patch.object(host.view_workspace, 'highlight_running_command', side_effect=record):
        assert host.start()
        assert host.tabWidget.currentIndex() == 1
        for row, command in enumerate(commands):
            pump_until(lambda: host.view_workspace.running_command_id == command.id)
            assert host.view_workspace.command_table.runtime_row == row
            assert host.textEdit.isVisible()
            released[row].set()
        pump_until(lambda: not host.command_thread.isRunning())
        QTest.qWait(50)
    assert observed == [command.id for command in commands]
    assert all(thread == QApplication.instance().thread() for thread in threads)
    assert host.tabWidget.currentIndex() == 1
    assert host.view_workspace.running_command_id == commands[-1].id
    assert host.textEdit.toPlainText()


def test_jump_scroll_refresh_and_selection_preserved(host):
    for _ in range(60):
        host.workspace.repository.add_command(InstructionDraft('时间等待', {'时长': 0}))
    host.workspace.reload_graph()
    views = host.view_workspace
    views.show_table()
    QApplication.processEvents()
    table = views.command_table
    commands = host.workspace.repository.list_commands()
    table.setCurrentCell(1, 3)
    selected = table.selected_command_ids()
    for row in (60, 0, 47, 2):
        host.command_thread.send_type_and_id.emit(commands[row].type_id, str(commands[row].id))
        QApplication.processEvents()
        assert table.runtime_row == row
        assert table.visualItemRect(table.item(row, 0)).intersects(table.viewport().rect())
        assert table.selected_command_ids() == selected
        # Exercise the translucent row marker without native input.
        table.viewport().grab()
    views.refresh_table()
    assert table.runtime_row == 2
    views.highlight_running_command(None)
    assert table.runtime_row == -1


def test_stop_keeps_visible_table_and_last_command(host):
    host.view_workspace.show_table()
    host.checkBox_2.setChecked(False)
    host.execution_services = {'悬停后点击': lambda context, command: context.metadata['wait_interruptibly'](10, context)}
    assert host.start()
    pump_until(lambda: host.view_workspace.running_command_id is not None)
    host.global_shortcut_key('终止线程')
    pump_until(lambda: not host.command_thread.isRunning())
    QTest.qWait(30)
    assert host.isVisible()
    assert host.tabWidget.currentIndex() == 1
    assert host.view_workspace.command_table.runtime_row == 0


def test_flow_runtime_log_highlight_and_restore(host):
    host.checkBox_2.setChecked(False)
    host.radioButton_2.setChecked(True)
    host.spinBox.setValue(1)
    host.run_unconnected_checkbox.setChecked(True)
    host.workspace.repository.add_command(InstructionDraft('悬停后点击', {}))
    host.workspace.reload_graph()
    views = host.view_workspace
    views.show_flow()
    QApplication.processEvents()
    assert views.flow_log_panel.isHidden()
    editor = host.workspace.editor
    original_height = editor.height()
    commands = host.workspace.repository.list_commands()
    released = [Event() for _ in commands]
    observed = []
    def execute(context, command):
        index = len(observed)
        observed.append(command.id)
        context.emit('流程图测试日志')
        while not released[index].wait(.005) and not context.stop_requested:
            pass
    host.execution_services = {'悬停后点击': execute}
    assert host.start()
    assert host.tabWidget.currentIndex() == 2
    for index, command in enumerate(commands):
        pump_until(lambda: views.running_command_id == command.id)
        assert views.flow_log.isVisible()
        marked = [node.command_id for node in editor.scene.nodes_by_id.values() if node.runtime_active]
        assert marked == [command.id]
        editor.view.viewport().grab()
        released[index].set()
    pump_until(lambda: not host.command_thread.isRunning())
    QTest.qWait(80)
    assert views.flow_log_panel.isHidden()
    assert host.tabWidget.currentIndex() == 2
    assert not any(node.runtime_active for node in editor.scene.nodes_by_id.values())
    assert editor.height() == original_height
    assert '流程图测试日志' in host.textEdit.toPlainText()
    assert views.flow_log.document() == host.textEdit.document()


def test_flow_stop_hides_log_and_clears_outline(host):
    host.checkBox_2.setChecked(False)
    host.workspace.reload_graph()
    host.view_workspace.show_flow()
    host.execution_services = {'悬停后点击': lambda context, command: context.metadata['wait_interruptibly'](10, context)}
    assert host.start()
    pump_until(lambda: host.view_workspace.running_command_id is not None)
    assert host.view_workspace.flow_log.isVisible()
    host.global_shortcut_key('终止线程')
    pump_until(lambda: not host.command_thread.isRunning())
    QTest.qWait(50)
    assert host.view_workspace.flow_log_panel.isHidden()
    assert host.tabWidget.currentIndex() == 2
    assert not any(node.runtime_active for node in host.workspace.editor.scene.nodes_by_id.values())


def test_run_keeps_current_page_and_allows_switching(host):
    host.checkBox_2.setChecked(False)
    host.workspace.reload_graph()
    views = host.view_workspace
    views.show_main()
    host.execution_services = {'悬停后点击': lambda context, command: context.metadata['wait_interruptibly'](10, context)}
    assert host.start()
    assert host.tabWidget.currentIndex() == 0
    pump_until(lambda: views.running_command_id is not None)
    current = views.running_command_id
    for show, index in [(views.show_flow, 2), (views.show_table, 1), (views.show_flow, 2)]:
        show()
        QApplication.processEvents()
        assert host.tabWidget.currentIndex() == index
        assert views.running_command_id == current
        if index == 2:
            assert views.flow_log.isVisible()
            assert host.workspace.editor.scene.nodes_by_command_id[current].runtime_active
        else:
            assert views.command_table.runtime_row >= 0
    host.global_shortcut_key('终止线程')
    pump_until(lambda: not host.command_thread.isRunning())
    QTest.qWait(50)
    assert host.tabWidget.currentIndex() == 2
    assert views.flow_log_panel.isHidden()
