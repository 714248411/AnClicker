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
@pytest.mark.parametrize('compact', [False, True])
def test_hidden_global_stop_restores_main_window(host, stop, compact):
    observed = []
    def run(context, command):
        observed.append(context)
        while not context.stop_requested:
            time.sleep(.005)
    host.execution_services = {'悬停后点击':run}
    host.view_workspace.compact.set_active(compact)
    assert host.checkBox_2.isChecked() and host.checkBox_2.isEnabled()
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
    assert host.view_workspace.compact.active == compact
    assert host.pushButton_5.isVisible()


def test_compact_completion_restores_small_window_and_setting(host):
    host.view_workspace.compact.set_active(True)
    host.execution_services = {'悬停后点击':lambda **kwargs:None}
    host.start()
    wait_for_finish(host)
    assert host.view_workspace.compact.active
    assert host.checkBox_2.isChecked() and host.checkBox_2.isEnabled()
    assert host.pushButton_5.isVisible()


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


def test_single_view_menu_keeps_toolbar_toggle(host):
    menus = [action.menu() for action in host.menubar.actions() if action.menu() is not None]
    views = [menu for menu in menus if menu.title().replace('&','') == '视图']
    assert len(views) == 1
    assert host.actiong in views[0].actions()
    host.actiong.setChecked(False)
    assert host.toolBar.isHidden()
    host.actiong.setChecked(True)
    assert not host.toolBar.isHidden()


def test_worker_cache_cleanup_is_queued_to_gui_thread(host):
    from PySide6.QtCore import QThread
    import gc
    observed = []
    with patch.object(gc, 'collect', side_effect=lambda: observed.append(QThread.currentThread())):
        host.command_thread.number = 25
        host.command_thread._release_runtime_cache()
        host.command_thread._release_runtime_cache(notify=False)
        assert observed == []
        QApplication.processEvents()
        assert len(observed) == 2
        assert all(thread == QApplication.instance().thread() for thread in observed)
