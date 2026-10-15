from __future__ import annotations

import logging
from typing import Any

from anclicker.platform.qt_compat.QtCore import QObject, QTimer, Signal, Slot
from anclicker.platform.qt_compat.QtWidgets import QMessageBox

from info import CURRENT_VERSION
from anclicker.app.updates.自动更新 import (
    CheckUpdateThread,
    DownloadUpdateThread,
    apply_update_and_restart,
    is_delta_update,
    update_target_details,
)

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'UpdateCheckDialog': ('from', 'anclicker.ui.dialogs.update_notice', ('UpdateCheckDialog',), 0),
    'UpdatePrompt_animate_to_entry': ('from', 'anclicker.ui.dialogs.update_notice', ('UpdatePrompt', 'animate_to_entry'), 0),
})


LOGGER = logging.getLogger(__name__)


class AutoUpdateManager(QObject):
    """协调手动及启动检查、下载和应用更新。"""

    update_ready = Signal(str, str)
    update_progress = Signal(str, int)

    def __init__(
        self,
        main_window_,
        *,
        check_thread_factory=CheckUpdateThread,
        download_thread_factory=DownloadUpdateThread,
        apply_update=apply_update_and_restart,
    ):
        super().__init__(main_window_)
        self.main_window = main_window_
        self.check_thread_factory = check_thread_factory
        self.download_thread_factory = download_thread_factory
        self.apply_update = apply_update
        self._stopping = False
        self.check_thread = None
        self.download_thread = None
        self.show_check_message = False
        self.download_was_manual = False
        self._ready_update_info = None
        self._available_update_info = None
        self._update_prompt = None
        self._progress_dialog = None
        self._last_progress = ("正在检查更新…", -1)
        self._install_after_download = False
        self.current_update_uses_delta = False
        self._delta_patch_active = False
        self.download_result_handled = False
        self.download_status_text = ""

    def _report_progress(self, text: str, value: int) -> None:
        self._last_progress = (text, value)
        if self._progress_dialog is not None:
            self._progress_dialog.set_progress(text, value)
        self.update_progress.emit(text, value)

    def _show_progress_dialog(self) -> None:
        if self._stopping or getattr(self.main_window, '_closing', False):
            return
        UpdateCheckDialog = _module_imports.load('UpdateCheckDialog')
        if self._progress_dialog is None:
            self._progress_dialog = UpdateCheckDialog(self.main_window, CURRENT_VERSION)
        dialog = self._progress_dialog
        dialog.apply_theme(self.main_window)
        version, _ = update_target_details(self._available_update_info)
        dialog.version_label.setText(
            f'当前版本 {CURRENT_VERSION}' + (f'  →  新版本 {version}' if version else '')
        )
        downloading = self.download_thread is not None and self.download_thread.isRunning()
        if getattr(self.main_window, '_update_preparing', False):
            dialog.hint_label.setText('正在保存当前状态并准备重启。')
            dialog.dismiss_button.setText('关闭')
        elif downloading:
            dialog.hint_label.setText(
                '下载完成后将安装并重启。关闭此窗口后仍会继续，可从“检查更新”再次查看。'
                if self._install_after_download else
                '关闭此窗口后仍会继续下载，可从“检查更新”再次查看。'
            )
            dialog.dismiss_button.setText('后台下载')
        else:
            dialog.hint_label.setText('检查结果会在完成后提示。')
            dialog.dismiss_button.setText('关闭')
        dialog.set_progress(*self._last_progress)
        if not dialog.isVisible():
            rect = dialog.frameGeometry()
            rect.moveCenter(self.main_window.frameGeometry().center())
            dialog.move(rect.topLeft())
            dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _hide_progress_dialog(self) -> None:
        if self._progress_dialog is not None:
            self._progress_dialog.hide()

    def _progress_failed(self, message: str) -> None:
        self.update_progress.emit('', -2)
        if self._progress_dialog is not None:
            self._progress_dialog.set_error(message)

    @property
    def ready_update_info(self) -> Any | None:
        return self._ready_update_info

    def check_on_startup(self) -> None:
        if getattr(self.main_window, '_closing', False):
            return
        self.check_for_updates(show_message=False)

    def check_for_updates(self, show_message: bool = False) -> None:
        if self._stopping:
            return
        if getattr(self.main_window, '_update_preparing', False):
            if show_message:
                self._show_progress_dialog()
            return
        if self._ready_update_info is not None:
            if show_message:
                self.show_manual_update_message(self._ready_update_info, ready=True)
            return
        if self.download_thread is not None and self.download_thread.isRunning():
            if show_message:
                self.download_was_manual = True
                self._show_progress_dialog()
            return
        if self.check_thread is not None and self.check_thread.isRunning():
            if show_message:
                self.show_check_message = True
                self._show_progress_dialog()
            return
        self.show_check_message = bool(show_message)
        self._last_progress = ('正在检查更新…', -1)
        if show_message:
            self._show_progress_dialog()
        try:
            check_thread_ = self.check_thread_factory(self.main_window)
        except Exception as error:
            self.handle_check_failure(f'更新配置读取失败：{error}')
            return
        check_thread_.pending_update_found.connect(self.handle_pending_update)
        check_thread_.update_found.connect(self.handle_update_info)
        check_thread_.no_update.connect(self.handle_no_update)
        check_thread_.check_skipped.connect(self.handle_check_skipped)
        check_thread_.check_failed.connect(self.handle_check_failure)
        check_thread_.finished.connect(self.on_check_finished)
        self.check_thread = check_thread_
        check_thread_.start()

    @Slot()
    def on_check_finished(self) -> None:
        thread_, self.check_thread = self.check_thread, None
        if thread_ is not None:
            thread_.deleteLater()

    @Slot()
    def handle_no_update(self) -> None:
        if self._stopping:
            return
        self._available_update_info = None
        self._hide_progress_dialog()
        if self.show_check_message:
            QMessageBox.information(
                self.main_window,
                "检查更新",
                f"已更新完毕，当前已是最新版本：{CURRENT_VERSION}",
            )

    @Slot(str)
    def handle_check_skipped(self, message_: str) -> None:
        LOGGER.info(message_)
        self._hide_progress_dialog()
        if self.show_check_message:
            QMessageBox.information(self.main_window, "检查更新", message_)

    @Slot(str)
    def handle_check_failure(self, message_: str) -> None:
        LOGGER.warning("Velopack 更新检查失败: %s", message_)
        self._hide_progress_dialog()
        if self.show_check_message:
            QMessageBox.warning(self.main_window, "检查更新失败", message_)

    @Slot(object)
    def handle_pending_update(self, update_info_: Any) -> None:
        if self._stopping:
            return
        self.mark_update_ready(update_info_)
        self.show_manual_update_message(update_info_, ready=True)

    @Slot(object)
    def handle_update_info(self, update_info_: Any) -> None:
        if self._stopping:
            return
        self._available_update_info = update_info_
        bar = getattr(getattr(self.main_window, 'view_workspace', None), 'title_bar', None)
        if bar is not None:
            version, notes = update_target_details(update_info_)
            bar.show_update(version, notes, ready=False)
        self.show_manual_update_message(update_info_, ready=False)

    def start_download(self, update_info_: Any, *, is_manual: bool = False) -> None:
        if self._stopping:
            return
        if self.download_thread is not None and self.download_thread.isRunning():
            self.download_was_manual = self.download_was_manual or bool(is_manual)
            if is_manual:
                self._show_progress_dialog()
            return
        self.download_was_manual = bool(is_manual)
        self._available_update_info = update_info_
        self.current_update_uses_delta = is_delta_update(update_info_)
        self._delta_patch_active = False
        self.download_result_handled = False
        self.download_status_text = (
            "正在下载增量更新包…"
            if self.current_update_uses_delta
            else "正在下载完整更新包…"
        )
        self._report_progress(self.download_status_text, 0)
        try:
            download_thread_ = self.download_thread_factory(update_info_, self.main_window)
        except Exception as error:
            self.handle_download_failure(f'无法开始下载：{error}')
            return
        download_thread_.download_progress.connect(self.handle_download_progress)
        download_thread_.delta_patch_started.connect(self.handle_delta_patch_started)
        download_thread_.full_download_fallback_started.connect(
            self.handle_full_download_fallback
        )
        download_thread_.download_finished.connect(self.handle_download_finished)
        download_thread_.download_failed.connect(self.handle_download_failure)
        download_thread_.finished.connect(self.on_download_thread_finished)
        self.download_thread = download_thread_
        download_thread_.start()
        if is_manual:
            self._show_progress_dialog()

    @Slot(int)
    def handle_download_progress(self, percent_: int) -> None:
        if self._stopping or self.download_result_handled:
            return
        percent_ = max(0, min(100, percent_))
        if percent_ >= 100:
            self._report_progress('下载完成，正在校验更新包…', -1)
        elif self.current_update_uses_delta and self._delta_patch_active:
            self._report_progress('正在应用增量补丁…', max(0, percent_ - 70) * 100 // 30)
        elif self.current_update_uses_delta:
            self._report_progress(self.download_status_text, min(percent_, 70) * 100 // 70)
        else:
            self._report_progress(self.download_status_text, percent_)

    @Slot()
    def handle_delta_patch_started(self) -> None:
        if self._stopping or self.download_result_handled or not self.current_update_uses_delta:
            return
        self._delta_patch_active = True
        self._report_progress('正在应用增量补丁…', 0)

    @Slot()
    def handle_full_download_fallback(self) -> None:
        if self._stopping or self.download_result_handled:
            return
        self.current_update_uses_delta = False
        self._delta_patch_active = False
        self.download_status_text = "增量补丁不可用，正在下载完整更新包…"
        self._report_progress(self.download_status_text, 0)

    @Slot()
    def on_download_thread_finished(self) -> None:
        if not self.download_result_handled and not self._stopping:
            self._progress_failed('更新下载已中断，请重新检查更新。')
        thread_, self.download_thread = self.download_thread, None
        if thread_ is not None:
            thread_.deleteLater()
        if self._install_after_download and self._ready_update_info is not None and not self._stopping:
            self._install_after_download = False
            QTimer.singleShot(0, self.apply_ready_update)

    @Slot(str)
    def handle_download_failure(self, message_: str) -> None:
        self._install_after_download = False
        self.download_result_handled = True
        LOGGER.warning("Velopack 更新下载或校验失败: %s", message_)
        self._progress_failed(f'更新包下载或校验失败：{message_}')
        if self.download_was_manual:
            QMessageBox.warning(
                self.main_window, "更新失败", f"更新包下载或校验失败：\n{message_}"
            )

    @Slot(object)
    def handle_download_finished(self, update_info_: Any) -> None:
        if self._stopping:
            return
        self.download_result_handled = True
        self._report_progress('更新包准备完成', 100)
        if self._progress_dialog is not None:
            self._progress_dialog.hint_label.setText(
                '即将安装并重启。' if self._install_after_download else
                '更新包已准备好，可从“检查更新”选择安装并重启。'
            )
            self._progress_dialog.dismiss_button.setText('关闭')
        self.mark_update_ready(update_info_)

    def mark_update_ready(self, update_info_: Any) -> None:
        self._ready_update_info = update_info_
        version_, notes_ = update_target_details(update_info_)
        self.update_progress.emit("", -2)
        self.update_ready.emit(version_, notes_)

    def show_manual_update_message(self, update_info_: Any, *, ready: bool) -> None:
        if self._stopping or getattr(self.main_window, '_closing', False): return
        self._hide_progress_dialog()
        if self._update_prompt is not None and self._update_prompt.isVisible():
            self._update_prompt.raise_(); return
        UpdatePrompt, animate_to_entry = _module_imports.load('UpdatePrompt_animate_to_entry')
        version, notes = update_target_details(update_info_)
        prompt = UpdatePrompt(self.main_window, version, notes, ready)
        self._update_prompt = prompt
        def defer(pixmap, rect):
            bar = getattr(getattr(self.main_window, 'view_workspace', None), 'title_bar', None)
            if bar is not None:
                bar.show_update(version, notes, ready=ready)
                self._defer_animation = animate_to_entry(self.main_window, bar.updateButton, pixmap, rect)
        def choose():
            if ready:
                self.apply_ready_update()
            else:
                self._install_after_download = True
                self.start_download(update_info_, is_manual=True)
        prompt.deferred.connect(defer)
        prompt.update_requested.connect(choose)
        def cleanup(*_):
            if self._update_prompt is prompt: self._update_prompt = None
            prompt.deleteLater()
        prompt.finished.connect(cleanup)
        prompt.show()
        rect = prompt.frameGeometry();rect.moveCenter(self.main_window.frameGeometry().center())
        prompt.move(rect.topLeft());prompt.raise_()

    def activate_update_entry(self):
        if self.download_thread is not None and self.download_thread.isRunning():
            self.download_was_manual = True
            self._show_progress_dialog()
            return False
        if self._ready_update_info is not None:
            return self.apply_ready_update()
        if self._available_update_info is not None:
            self.show_manual_update_message(self._available_update_info, ready=False)
        else:
            self.check_for_updates(show_message=True)
        return False

    def apply_ready_update(self) -> bool:
        update_info_ = self._ready_update_info
        if update_info_ is None:
            QMessageBox.warning(self.main_window, "更新失败", "没有已准备完成的更新包。")
            return False
        prepare_ = getattr(self.main_window, "prepare_for_update", None)
        if not callable(prepare_):
            QMessageBox.warning(
                self.main_window,
                "更新失败",
                "主窗口未实现更新前准备协议。",
            )
            return False
        if getattr(self.main_window, '_update_preparing', False):
            return False
        self.main_window._update_preparing = True
        self._report_progress("正在准备安装更新…", -1)
        try:
            preparation_ = prepare_()
        except Exception as exc:
            preparation_ = (False, f"自动更新前准备失败: {exc}")
        if isinstance(preparation_, tuple):
            prepared_ = bool(preparation_[0])
            reason_ = str(preparation_[1] or "") if len(preparation_) > 1 else ""
        else:
            prepared_ = bool(preparation_)
            reason_ = ""
        if not prepared_:
            self.main_window._update_preparing = False
            self._progress_failed(reason_ or "更新前保存数据或停止后台任务失败。")
            QMessageBox.warning(
                self.main_window,
                "更新失败",
                reason_ or "更新前保存数据或停止后台任务失败。",
            )
            return False
        try:
            self._report_progress("正在启动安装并重启…", -1)
            self.apply_update(update_info_)
            self.main_window._update_exit_requested = True
        except Exception as exc:
            self.main_window._update_preparing = False
            self.main_window._update_exit_requested = False
            LOGGER.exception("Velopack 更新应用失败")
            self._progress_failed(f"无法应用更新并重启：{type(exc).__name__}: {exc}")
            QMessageBox.warning(
                self.main_window,
                "更新失败",
                f"无法应用更新并重启：\n{type(exc).__name__}: {exc}",
            )
            return False
        return True

    def cancel_for_exit(self) -> bool:
        self._stopping = True
        self._install_after_download = False
        if self._update_prompt is not None: self._update_prompt.accept()
        self._hide_progress_dialog()
        self.show_check_message = self.download_was_manual = False
        threads = [t for t in (self.check_thread, self.download_thread) if t is not None]
        for thread in threads:
            if thread.isRunning():
                thread.requestInterruption()
        for thread in threads:
            if thread.isRunning() and not thread.wait(5000):
                return False
        return True

    def shutdown(self) -> bool:
        # Ordinary shutdown waits; explicit exit cancels the isolated SDK process.
        if any(t is not None and t.isRunning() for t in (self.check_thread, self.download_thread)):
            return False
        return True
