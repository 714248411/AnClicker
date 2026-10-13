"""检查更新窗口的真实进度、可重入交互与失败保护。"""
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from qt_compat.QtCore import QObject, QThread, Qt, Signal
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication, QMainWindow

import update.自动更新接入 as module
from update.自动更新 import DownloadUpdateThread


class ControlledCheck(QObject):
    pending_update_found = Signal(object)
    update_found = Signal(object)
    no_update = Signal()
    check_skipped = Signal(str)
    check_failed = Signal(str)
    finished = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.running = False

    def start(self):
        self.running = True

    def isRunning(self):
        return self.running

    def requestInterruption(self):
        self.running = False

    def wait(self, timeout):
        return not self.running

    def finish(self):
        self.running = False
        self.finished.emit()


class ControlledDownload(ControlledCheck):
    download_progress = Signal(int)
    delta_patch_started = Signal()
    full_download_fallback_started = Signal()
    download_finished = Signal(object)
    download_failed = Signal(str)

    def __init__(self, info, parent):
        super().__init__(parent)
        self.info = info


@pytest.fixture
def update_ui(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.resize(800, 520)
    window.view_workspace = SimpleNamespace(theme_mode='light')
    window.prepare_for_update = Mock(return_value=(True, ''))
    window.show()
    manager = module.AutoUpdateManager(
        window, check_thread_factory=ControlledCheck,
        download_thread_factory=ControlledDownload, apply_update=Mock(),
    )
    notices, warnings = [], []
    monkeypatch.setattr(module.QMessageBox, 'information', lambda *args: notices.append(args[1:]))
    monkeypatch.setattr(module.QMessageBox, 'warning', lambda *args: warnings.append(args[1:]))
    info = SimpleNamespace(
        TargetFullRelease=SimpleNamespace(Version='9.9.9', NotesMarkdown='测试更新'),
        DeltasToTarget=[],
    )
    yield SimpleNamespace(app=app, window=window, manager=manager, info=info,
                          notices=notices, warnings=warnings)
    manager.cancel_for_exit()
    window.close()
    window.deleteLater()
    QTest.qWait(10)


def test_manual_check_reuses_window_and_reports_latest(update_ui):
    m = update_ui.manager
    m.check_for_updates(True)
    thread, dialog = m.check_thread, m._progress_dialog
    assert dialog.isVisible() and dialog.progress_bar.maximum() == 0
    m.check_for_updates(True)
    assert m.check_thread is thread and m._progress_dialog is dialog
    assert not update_ui.notices
    thread.no_update.emit()
    thread.finish()
    assert not dialog.isVisible() and m.check_thread is None
    assert len(update_ui.notices) == 1
    assert '已更新完毕' in update_ui.notices[0][1]
    assert module.CURRENT_VERSION in update_ui.notices[0][1]


def test_startup_latest_check_stays_quiet(update_ui):
    m = update_ui.manager
    m.check_on_startup()
    m.check_thread.no_update.emit()
    m.check_thread.finish()
    assert m._progress_dialog is None and not update_ui.notices


@pytest.mark.parametrize('signal', ['check_failed', 'check_skipped'])
def test_check_failure_or_unsupported_build_never_claims_success(update_ui, signal):
    m = update_ui.manager
    m.check_for_updates(True)
    getattr(m.check_thread, signal).emit('测试：无法完成检查')
    m.check_thread.finish()
    assert not m._progress_dialog.isVisible()
    messages = update_ui.notices + update_ui.warnings
    assert len(messages) == 1 and '无法完成检查' in messages[0][1]
    assert '已更新完毕' not in messages[0][1]


def test_full_download_progress_is_immediate_and_does_not_invent_progress(update_ui):
    m = update_ui.manager
    m.start_download(update_ui.info, is_manual=True)
    dialog = m._progress_dialog
    assert dialog.isVisible() and not dialog.isModal()
    assert dialog.percent_label.text() == '0%'
    m.download_thread.download_progress.emit(73)
    assert dialog.progress_bar.value() == 73
    assert dialog.percent_label.text() == '73%'
    QTest.qWait(450)
    assert dialog.progress_bar.value() == 73
    m.download_thread.download_progress.emit(100)
    assert dialog.progress_bar.maximum() == 0
    assert '校验' in dialog.status_label.text() and not dialog.percent_label.text()
    assert m.ready_update_info is None


@pytest.mark.parametrize('entry', ['menu', 'title'])
def test_hidden_download_reopens_at_live_progress_without_restarting(update_ui, entry):
    m = update_ui.manager
    m.start_download(update_ui.info, is_manual=True)
    dialog, thread = m._progress_dialog, m.download_thread
    QTest.keyClick(dialog, Qt.Key_Escape)
    assert not dialog.isVisible() and thread.isRunning()
    thread.download_progress.emit(68)
    if entry == 'menu':
        m.check_for_updates(True)
    else:
        m.activate_update_entry()
    assert m._progress_dialog is dialog and dialog.isVisible()
    assert dialog.progress_bar.value() == 68
    assert m.download_thread is thread and not update_ui.notices
    m.start_download(update_ui.info, is_manual=True)
    assert m.download_thread is thread


def test_delta_download_patch_and_fallback_show_current_phase(update_ui):
    m = update_ui.manager
    update_ui.info.DeltasToTarget = [object()]
    m.start_download(update_ui.info, is_manual=True)
    dialog = m._progress_dialog
    # Exercise the SDK adapter's phase detection with its documented 70% split.
    adapter = DownloadUpdateThread(update_ui.info, source_url='unused')
    adapter.download_progress.connect(m.handle_download_progress)
    adapter.delta_patch_started.connect(m.handle_delta_patch_started)
    adapter.full_download_fallback_started.connect(m.handle_full_download_fallback)
    adapter._handle_velopack_progress(35)
    assert dialog.percent_label.text() == '50%' and '下载增量' in dialog.status_label.text()
    adapter._handle_velopack_progress(70)
    assert dialog.percent_label.text() == '0%' and '增量补丁' in dialog.status_label.text()
    adapter._handle_velopack_progress(85)
    assert dialog.percent_label.text() == '50%'
    adapter._handle_velopack_progress(8)
    assert dialog.percent_label.text() == '8%'
    assert '下载完整' in dialog.status_label.text()
    adapter._handle_velopack_progress(100)
    assert '校验' in dialog.status_label.text()
    assert m.ready_update_info is None


def test_download_failure_stops_spinner_and_retry_starts_fresh(update_ui):
    m = update_ui.manager
    m.start_download(update_ui.info, is_manual=True)
    m._install_after_download = True
    thread = m.download_thread
    thread.download_progress.emit(100)
    thread.download_failed.emit('测试校验失败')
    thread.finish()
    dialog = m._progress_dialog
    assert '校验失败' in dialog.status_label.text()
    assert dialog.progress_bar.isHidden() and not dialog.percent_label.text()
    assert not m._install_after_download and m.ready_update_info is None
    assert not m.apply_update.called and update_ui.warnings
    m.start_download(update_ui.info, is_manual=True)
    assert m.download_thread is not thread and m._progress_dialog is dialog
    assert dialog.progress_bar.isVisible() and dialog.percent_label.text() == '0%'


def test_confirm_download_shows_progress_and_installs_only_after_worker_exits(update_ui):
    m = update_ui.manager
    m.check_for_updates(True)
    check = m.check_thread
    check.update_found.emit(update_ui.info)
    check.finish()
    assert m._update_prompt.isVisible() and not m._progress_dialog.isVisible()
    assert m.download_thread is None
    m._update_prompt.update_button.click()
    dialog, download = m._progress_dialog, m.download_thread
    assert dialog.isVisible() and m._install_after_download
    download.download_finished.emit(update_ui.info)
    assert dialog.progress_bar.value() == 100
    assert dialog.status_label.text() == '更新包准备完成'
    assert not m.apply_update.called
    download.finish()
    QTest.qWait(20)
    m.apply_update.assert_called_once_with(update_ui.info)
    assert '重启' in dialog.status_label.text()
    assert dialog.progress_bar.maximum() == 0


@pytest.mark.parametrize('failure', ['prepare', 'install'])
def test_install_failure_keeps_error_visible_without_claiming_updated(update_ui, failure):
    m = update_ui.manager
    m.start_download(update_ui.info, is_manual=True)
    m.download_thread.download_finished.emit(update_ui.info)
    m.download_thread.finish()
    if failure == 'prepare':
        update_ui.window.prepare_for_update.return_value = (False, '请先关闭编辑窗口')
    else:
        m.apply_update.side_effect = RuntimeError('测试安装失败')
    assert not m.apply_ready_update()
    assert m._progress_dialog.progress_bar.isHidden()
    assert update_ui.warnings and not update_ui.notices
    assert not update_ui.window._update_preparing


def test_close_app_hides_progress_and_ignores_late_completion(update_ui):
    m = update_ui.manager
    m.start_download(update_ui.info, is_manual=True)
    assert m.cancel_for_exit()
    m.handle_download_progress(60)
    m.handle_download_finished(update_ui.info)
    m.handle_no_update()
    assert not m._progress_dialog.isVisible()
    assert m.ready_update_info is None and not update_ui.notices


@pytest.mark.parametrize('theme,width', [('light', 800), ('dark', 800), ('dark', 360)])
def test_progress_dialog_theme_layout_and_transparent_corners(update_ui, theme, width):
    m = update_ui.manager
    update_ui.window.view_workspace.theme_mode = theme
    update_ui.window.resize(width, 520)
    m.start_download(update_ui.info, is_manual=True)
    m.download_thread.download_progress.emit(62)
    dialog = m._progress_dialog
    QTest.qWait(30)
    for widget in (dialog.version_label, dialog.status_label, dialog.percent_label,
                   dialog.progress_bar, dialog.close_button, dialog.dismiss_button):
        assert widget.isVisible() and dialog.rect().contains(widget.geometry())
    assert dialog.status_label.geometry().right() < dialog.percent_label.geometry().left()
    assert dialog.testAttribute(Qt.WA_TranslucentBackground)
    root = Path('validation/update-progress-ui')
    root.mkdir(parents=True, exist_ok=True)
    dialog.grab().save(str(root / f'{theme}-{width}.png'))


def test_worker_progress_reaches_gui_while_verification_is_still_running(update_ui):
    m = update_ui.manager
    release = Event()
    class DownloadService:
        def download_updates(self, info, progress_callback):
            progress_callback(18)
            progress_callback(79)
            progress_callback(100)
            if not release.wait(5):
                raise RuntimeError('测试超时')
    m.download_thread_factory = lambda info, parent: DownloadUpdateThread(
        info, parent, source_url='unused', manager_factory=lambda _: DownloadService())
    observed = []
    m.update_progress.connect(lambda text, value: observed.append((QThread.currentThread(), text, value)))
    m.start_download(update_ui.info, is_manual=True)
    try:
        for _ in range(100):
            QTest.qWait(10)
            if any('校验' in text for _, text, _ in observed):
                break
        assert {18, 79, -1} <= {value for _, _, value in observed}
        assert all(thread == update_ui.app.thread() for thread, _, _ in observed)
        assert m.download_thread.isRunning() and m.ready_update_info is None
        assert m._progress_dialog.progress_bar.maximum() == 0
    finally:
        release.set()
        if m.download_thread is not None:
            assert m.download_thread.wait(5000)
        QTest.qWait(30)
    assert m.ready_update_info is update_ui.info
    assert m._progress_dialog.progress_bar.value() == 100
