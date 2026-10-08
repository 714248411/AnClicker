"""Execution follows stable command IDs without stealing editing selections."""
import time
from threading import Event
from unittest.mock import patch

from PySide6.QtCore import QThread
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from instructions.models import InstructionDraft
from test.test_hidden_stop import host


def pump_until(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
        time.sleep(.005)
    assert predicate()


def test_start_follows_real_worker_and_keeps_table_log_after_completion(host):
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

    def record(command_id):
        threads.append(QThread.currentThread())
        follow(command_id)

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
