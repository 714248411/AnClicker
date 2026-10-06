import os
import time
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from instructions.models import InstructionDraft
from 数据库操作 import DatabaseOperation


class Hotkeys:
    supported = True
    def __init__(self):
        self.callbacks = {}
    def register(self, keys, callback, **kwargs):
        self.callbacks[tuple(keys)] = callback
    def unregister(self, keys):
        self.callbacks.pop(tuple(keys), None)


@pytest.fixture
def host(tmp_path):
    app = QApplication.instance() or QApplication([])
    db = DatabaseOperation(str(tmp_path / 'run.db'))
    with patch('Start_Win.DatabaseOperation', return_value=db), patch('main_work.DatabaseOperation',return_value=db), \
         patch('Start_Win.SystemHotkey',Hotkeys), patch('Start_Win.is_hotkey_valid',return_value=True), \
         patch.object(db,'system_prompt_tone'), patch.object(db,'show_normal_window_with_specified_title'):
        from Start_Win import Main_window
        window = Main_window()
        window.show()
        window.checkBox_2.setChecked(True)
        window.workspace.repository.add_command(InstructionDraft('悬停后点击', {}))
        yield window
        if window.command_thread.isRunning():
            window.command_thread.stop_and_wait()
        app.processEvents()
        window.hide()
        window.deleteLater()
        app.processEvents()


def wait_for_finish(window):
    deadline = time.monotonic()+3
    while window.command_thread.isRunning() and time.monotonic()<deadline:
        QApplication.processEvents()
        time.sleep(.01)
    QTest.qWait(30)
    assert not window.command_thread.isRunning()
    assert window.isVisible()
    assert window.tabWidget.currentIndex() == 0
    assert not window.escape_stop.isEnabled()
    assert ('escape',) not in window.hk_stop.callbacks


@pytest.mark.parametrize('stop', ['escape', '结束运行'])
def test_hidden_global_stop_restores_main_window(host, stop):
    observed = []
    def run(context, command):
        observed.append(context)
        while not context.stop_requested:
            time.sleep(.005)
    host.execution_services = {'悬停后点击':run}
    assert host.start()
    assert not host.isVisible()
    deadline = time.monotonic()+2
    while not observed and time.monotonic()<deadline:
        QApplication.processEvents()
        time.sleep(.01)
    keys = ('escape',) if stop == 'escape' else tuple(host.db.get_global_shortcut()['结束运行'])
    host.hk_stop.callbacks[keys](None)
    wait_for_finish(host)
    assert observed and observed[0].stop_requested


def test_normal_completion_restores_hidden_window(host):
    host.execution_services = {'悬停后点击':lambda **kwargs:None}
    host.start()
    wait_for_finish(host)


def test_unavailable_global_escape_keeps_window_visible(host):
    host.hk_stop.supported = False
    host.execution_services = {'悬停后点击':lambda **kwargs:None}
    host.start()
    assert host.isVisible()
    wait_for_finish(host)
