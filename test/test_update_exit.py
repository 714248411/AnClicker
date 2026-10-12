import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import velopack
from qt_compat.QtCore import QThread
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication, QMainWindow
from update.process_worker import encode, decode, run_isolated, UpdateCancelled
from update.自动更新接入 import AutoUpdateManager


def test_sdk_roundtrip_preserves_assets():
    asset = velopack.VelopackAsset('AnClicker', '1.4.9', 'Full', 'a.nupkg', 'a', 'b', 42, 'notes', 'html')
    value = velopack.UpdateInfo(asset, [], False)
    assert encode(decode(encode(value))) == encode(value)
    assert encode(decode(encode(asset))) == encode(asset)


def test_cancel_stops_real_child_and_never_marks_ready(tmp_path, monkeypatch):
    import update.process_worker as worker
    app = QApplication.instance() or QApplication([])
    child = tmp_path / 'slow.py'
    child.write_text('import time\ntime.sleep(30)\n', encoding='utf-8')
    original = worker.subprocess.Popen
    processes = []
    def spawn(args, **kwargs):
        process = original([sys.executable, str(child)], **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(worker.subprocess, 'Popen', spawn)
    class Task(QThread):
        def run(self):
            try:
                run_isolated(self, 'check', 'unused')
            except UpdateCancelled:
                pass
    window = QMainWindow()
    manager = AutoUpdateManager(window)
    task = Task(window)
    manager.check_thread = task
    task.start()
    deadline = time.monotonic() + 3
    while not processes and time.monotonic() < deadline:
        QTest.qWait(10)
    assert processes and not manager.shutdown()
    started = time.monotonic()
    assert manager.cancel_for_exit()
    assert time.monotonic() - started < 3
    assert not task.isRunning()
    assert processes[0].poll() is not None
    manager.handle_update_info(object())
    assert manager.download_thread is None
    assert manager.ready_update_info is None
    window.close()


@pytest.mark.parametrize('choice', ['等待', '继续结束'])
def test_close_dialog_choices_save_only_on_exit(tmp_path, choice):
    from Start_Win import Main_window
    from 数据库操作 import DatabaseOperation
    app = QApplication.instance() or QApplication([])
    database = DatabaseOperation(str(tmp_path / 'close.db'))
    with patch('Start_Win.DatabaseOperation', return_value=database), patch('main_work.DatabaseOperation', return_value=database), patch('Start_Win.SystemHotkey', return_value=Mock()), patch('Start_Win.is_hotkey_valid', return_value=True):
        window = Main_window()
    window.auto_update = Mock()
    window.auto_update.shutdown.return_value = False
    window.auto_update.cancel_for_exit.return_value = True
    event = Mock()
    buttons = {}
    with patch('Start_Win.QMessageBox') as message, patch.object(window.view_workspace, '_save_code') as save, patch.object(database, 'get_bool_setting', return_value=False):
        box = message.return_value
        def add(label, role):
            buttons[label] = object()
            return buttons[label]
        box.addButton.side_effect = add
        box.clickedButton.side_effect = lambda: buttons[choice]
        window.closeEvent(event)
        assert set(buttons) == {'继续结束', '等待'}
        if choice == '等待':
            event.ignore.assert_called_once()
            window.auto_update.cancel_for_exit.assert_not_called()
            save.assert_not_called()
        else:
            event.accept.assert_called_once()
            window.auto_update.cancel_for_exit.assert_called_once()
            save.assert_called_once()
    window.deleteLater()
