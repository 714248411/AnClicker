"""Integration regressions discovered while merging the remote updater."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox


def test_busy_updater_blocks_close_before_any_data_changes():
    from Start_Win import Main_window
    window = SimpleNamespace(auto_update=SimpleNamespace(shutdown=lambda: False))
    event = Mock()
    with patch.object(QMessageBox, 'information') as notice:
        Main_window.closeEvent(window, event)
    event.ignore.assert_called_once()
    notice.assert_called_once()


def test_project_switch_does_not_reference_a_close_event():
    from Start_Win import Main_window
    window = SimpleNamespace(
        command_thread=SimpleNamespace(isRunning=lambda: False),
        view_workspace=SimpleNamespace(recording_page=SimpleNamespace(busy=False, drafts=[], written=True)),
        db=SimpleNamespace(get_setting_value=lambda _: None),
        workspace=SimpleNamespace(repository=SimpleNamespace(list_commands=lambda: [])),
        auto_update=SimpleNamespace(shutdown=Mock(return_value=False)),
        data_import=Mock(), add_recent_to_fileMenu=Mock())
    Main_window.open_project_path(window, 'example.xlsx')
    window.data_import.assert_called_once_with('example.xlsx')
    window.auto_update.shutdown.assert_not_called()


def test_delayed_startup_check_ignores_closed_window():
    pytest.importorskip('velopack')
    from update.自动更新接入 import AutoUpdateManager
    owner = SimpleNamespace(main_window=SimpleNamespace(_closing=True), check_for_updates=Mock())
    AutoUpdateManager.check_on_startup(owner)
    owner.check_for_updates.assert_not_called()


def test_bad_source_configuration_is_reported_without_escaping_slot():
    pytest.importorskip('velopack')
    from update.自动更新接入 import AutoUpdateManager
    app = QApplication.instance() or QApplication([])
    manager = AutoUpdateManager(None, check_thread_factory=Mock(side_effect=ValueError('invalid source')))
    with patch.object(manager, 'handle_check_failure') as error:
        manager.check_for_updates()
    error.assert_called_once()
    assert manager.check_thread is None
    manager.deleteLater()


def test_release_script_can_resolve_version_from_another_working_directory(tmp_path):
    script = Path(__file__).resolve().parents[1] / 'packaging' / 'build_release.py'
    result = subprocess.run([sys.executable, str(script), '--help'], cwd=tmp_path, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
