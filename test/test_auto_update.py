import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
pytest.importorskip('velopack', reason='Windows 自更新依赖仅在 Windows 安装')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QMessageBox
from update.自动更新 import CheckUpdateThread, DownloadUpdateThread
from update.自动更新接入 import AutoUpdateManager
from startup_environment import storage_install_folder

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_managed_directory_preserves_data(tmp_path):
    current = tmp_path / 'current'
    current.mkdir()
    assert storage_install_folder(current) == current
    (current / 'sq.version').touch()
    (tmp_path / 'Update.exe').touch()
    assert storage_install_folder(current) == tmp_path


def test_unmanaged_skips_network(app):
    factory = Mock()
    worker = CheckUpdateThread(source_url='https://test.invalid', managed_checker=lambda: False, manager_factory=factory)
    skipped = []
    worker.check_skipped.connect(skipped.append)
    worker.run()
    assert skipped and not factory.called


def test_check_pending_failure_and_new_version(app):
    manager = Mock()
    worker = CheckUpdateThread(source_url='https://test.invalid', managed_checker=lambda: True, manager_factory=lambda u: manager)
    found, pending, failed = [], [], []
    worker.update_found.connect(found.append)
    worker.pending_update_found.connect(pending.append)
    worker.check_failed.connect(failed.append)
    manager.get_update_pending_restart.return_value = 'pending'
    worker.run()
    assert pending == ['pending'] and not manager.check_for_updates.called
    manager.get_update_pending_restart.return_value = None
    manager.check_for_updates.return_value = 'new'
    worker.run()
    assert found == ['new']
    manager.check_for_updates.side_effect = RuntimeError('offline')
    worker.run()
    assert len(failed) == 1


def test_download_failure_and_delta_fallback(app):
    manager = Mock()
    manager.download_updates.side_effect = RuntimeError('hash mismatch')
    worker = DownloadUpdateThread(SimpleNamespace(DeltasToTarget=['delta']), source_url='https://test.invalid', manager_factory=lambda u: manager)
    failed, fallback, patching = [], [], []
    worker.download_failed.connect(failed.append)
    worker.full_download_fallback_started.connect(lambda: fallback.append(True))
    worker.delta_patch_started.connect(lambda: patching.append(True))
    worker._handle_velopack_progress(80)
    worker._handle_velopack_progress(10)
    worker.run()
    assert failed and fallback == [True] and patching == [True]


def test_apply_cancel_and_busy_do_not_restart(app):
    manager = AutoUpdateManager(None, apply_update=Mock())
    manager.main_window = SimpleNamespace(prepare_for_update=lambda: (False, '取消'))
    manager._ready_update_info = 'ready'
    with patch.object(QMessageBox, 'warning'):
        assert not manager.apply_ready_update()
    manager.apply_update.assert_not_called()
    manager.check_thread = SimpleNamespace(isRunning=lambda: True)
    assert not manager.shutdown()
    manager.check_thread = None
    assert manager.shutdown()


def test_silent_auto_errors(app):
    manager = AutoUpdateManager(None)
    with patch.object(QMessageBox, 'warning') as warning:
        manager.handle_check_failure('offline')
        manager.handle_download_failure('checksum failed')
        warning.assert_not_called()
        manager.show_check_message = True
        manager.handle_check_failure('offline')
        assert warning.called










def test_prepare_blocks_task_and_save_cancel(app):
    from Start_Win import Main_window
    window = SimpleNamespace(command_thread=SimpleNamespace(isRunning=lambda: True),
        view_workspace=SimpleNamespace(recording_page=SimpleNamespace(busy=False, drafts=[], written=True)),
        workspace=SimpleNamespace(_instruction_test_active=False))
    assert not Main_window.prepare_for_update(window)[0]
    window.command_thread.isRunning = lambda: False
    window.auto_update = SimpleNamespace(shutdown=lambda: True)
    window.save_data = Mock(return_value=False)
    # A QWidget is required only for the real dialog; mock the dialog here.
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Cancel):
        assert not Main_window.prepare_for_update(window)[0]
        window.save_data.assert_not_called()
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        assert not Main_window.prepare_for_update(window)[0]
        window.save_data.assert_called_once()






def test_gate_allows_only_audited_readonly_files():
    spec = importlib.util.spec_from_file_location('release_gate_test', Path(__file__).parents[1] / 'packaging/发布门槛.py')
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    for path in ('defaults/命令集.db', 'lib/app/defaults/命令集.db', 'current/cv2/data/__init__.py'):
        gate._check_member(path)
    for path in ('data/命令集.db', 'current/data/命令集.db', '../defaults/命令集.db',
                 'lib/app/defaults/live.db', 'current/data/defaults/命令集.db'):
        with pytest.raises(RuntimeError):
            gate._check_member(path)


def test_prepare_blocks_recording_and_instruction_test(app):
    from Start_Win import Main_window
    recording = SimpleNamespace(busy=True, drafts=[], written=True)
    window = SimpleNamespace(command_thread=SimpleNamespace(isRunning=lambda: False),
        view_workspace=SimpleNamespace(recording_page=recording),
        workspace=SimpleNamespace(_instruction_test_active=False))
    assert not Main_window.prepare_for_update(window)[0]
    recording.busy = False
    window.workspace._instruction_test_active = True
    assert not Main_window.prepare_for_update(window)[0]


def test_actual_managed_storage_with_environment(tmp_path, monkeypatch):
    from startup_environment import prepare_environment
    current = tmp_path / 'current'
    current.mkdir()
    (current / 'sq.version').touch()
    (tmp_path / 'Update.exe').touch()
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setattr(sys, 'executable', str(current / 'AnClicker.exe'))
    monkeypatch.setenv('ANCLICKER_DATA_DIR', '')
    assert prepare_environment() == tmp_path / 'data'
    assert not (current / 'data').exists()


def test_update_confirmation_cannot_start_task(app):
    from Start_Win import Main_window
    window = SimpleNamespace(_update_preparing=True, statusBar=SimpleNamespace(showMessage=Mock()))
    assert not Main_window.start(window)
    assert window.statusBar.showMessage.called


def test_cancel_releases_update_preparation_guard(app):
    manager = AutoUpdateManager(None, apply_update=Mock())
    manager.main_window = SimpleNamespace(prepare_for_update=lambda: (False, '取消'))
    manager._ready_update_info = 'ready'
    with patch.object(QMessageBox, 'warning'):
        assert not manager.apply_ready_update()
    assert not manager.main_window._update_preparing
