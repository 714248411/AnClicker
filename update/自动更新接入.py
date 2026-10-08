from __future__ import annotations

import logging
import random
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from info import CURRENT_VERSION
from update.自动更新 import (
    CheckUpdateThread,
    DownloadUpdateThread,
    apply_update_and_restart,
    is_delta_update,
    update_target_details,
)

LOGGER = logging.getLogger(__name__)


class UpdateProgressAnimator(QObject):
    """平滑显示下载回调，并把校验和补丁阶段限制在 99%。"""

    display_changed = Signal(int, str)

    def __init__(
        self,
        parent=None,
        *,
        interval_ms: int = 400,
        random_int: Callable[[int, int], int] = random.randint,
    ):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.tick)
        self.random_int = random_int
        self.current_progress = 0
        self.target_progress = 0
        self.status_text = ""

    def reset(self, status_text: str) -> None:
        self.timer.stop()
        self.current_progress = 0
        self.target_progress = 0
        self.status_text = status_text
        self.timer.start()
        self.display_changed.emit(0, self.status_text)

    def set_target(self, progress: int) -> None:
        self.target_progress = max(
            self.target_progress, min(99, max(0, int(progress)))
        )

    def enter_processing(self, status_text: str) -> None:
        self.status_text = status_text
        self.target_progress = 99
        self.display_changed.emit(self.current_progress, self.status_text)

    @Slot()
    def tick(self) -> None:
        if self.current_progress < self.target_progress:
            step = max(1, min(2, int(self.random_int(1, 2))))
            self.current_progress = min(self.target_progress, self.current_progress + step)
        self.display_changed.emit(self.current_progress, self.status_text)

    def complete(self) -> None:
        self.timer.stop()
        self.current_progress = 100
        self.target_progress = 100
        self.display_changed.emit(100, "更新包准备完成")

    def stop(self) -> None:
        self.timer.stop()


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
        self.check_thread = None
        self.download_thread = None
        self.show_check_message = False
        self.download_was_manual = False
        self._ready_update_info = None
        self.current_update_uses_delta = False
        self.download_result_handled = False
        self.download_status_text = ""
        self.progress_animator = UpdateProgressAnimator(self)
        self.progress_animator.display_changed.connect(self.handle_animated_progress)

    @property
    def ready_update_info(self) -> Any | None:
        return self._ready_update_info

    def check_on_startup(self) -> None:
        if getattr(self.main_window, '_closing', False):
            return
        self.check_for_updates(show_message=False)

    def check_for_updates(self, show_message: bool = False) -> None:
        if self.download_thread is not None and self.download_thread.isRunning():
            if show_message:
                self.download_was_manual = True
                QMessageBox.information(self.main_window, "检查更新", "正在下载更新，请稍候。")
            return
        if self.check_thread is not None and self.check_thread.isRunning():
            if show_message:
                self.show_check_message = True
                QMessageBox.information(
                    self.main_window, "检查更新", "正在检查更新，请稍候。"
                )
            return
        self.show_check_message = bool(show_message)
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
        if self.show_check_message:
            QMessageBox.information(
                self.main_window,
                "检查更新",
                f"当前已是最新版本：{CURRENT_VERSION}",
            )

    @Slot(str)
    def handle_check_skipped(self, message_: str) -> None:
        LOGGER.info(message_)
        if self.show_check_message:
            QMessageBox.information(self.main_window, "检查更新", message_)

    @Slot(str)
    def handle_check_failure(self, message_: str) -> None:
        LOGGER.warning("Velopack 更新检查失败: %s", message_)
        if self.show_check_message:
            QMessageBox.warning(self.main_window, "检查更新失败", message_)

    @Slot(object)
    def handle_pending_update(self, update_info_: Any) -> None:
        self.mark_update_ready(update_info_)
        if self.show_check_message:
            self.show_manual_update_message(update_info_, ready=True)

    @Slot(object)
    def handle_update_info(self, update_info_: Any) -> None:
        if self.show_check_message:
            self.show_manual_update_message(update_info_, ready=False)
        self.start_download(update_info_, is_manual=self.show_check_message)

    def start_download(self, update_info_: Any, *, is_manual: bool = False) -> None:
        if self.download_thread is not None and self.download_thread.isRunning():
            self.download_was_manual = self.download_was_manual or bool(is_manual)
            return
        self.download_was_manual = bool(is_manual)
        self.current_update_uses_delta = is_delta_update(update_info_)
        self.download_result_handled = False
        self.download_status_text = (
            "正在下载增量更新包…"
            if self.current_update_uses_delta
            else "正在下载完整更新包…"
        )
        self.progress_animator.reset(self.download_status_text)
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

    @Slot(int)
    def handle_download_progress(self, percent_: int) -> None:
        percent_ = max(0, min(100, percent_))
        if self.current_update_uses_delta:
            mapped_progress_ = min(percent_, 70) * 90 // 70
        else:
            mapped_progress_ = percent_ * 90 // 100
        self.progress_animator.set_target(mapped_progress_)
        if not self.current_update_uses_delta and percent_ >= 100:
            self.progress_animator.enter_processing("正在校验更新包…")

    @Slot(int, str)
    def handle_animated_progress(self, percent_: int, status_text_: str) -> None:
        self.update_progress.emit(status_text_, percent_)

    @Slot()
    def handle_delta_patch_started(self) -> None:
        if not self.current_update_uses_delta:
            return
        self.progress_animator.set_target(90)
        self.progress_animator.enter_processing("正在应用增量补丁…")

    @Slot()
    def handle_full_download_fallback(self) -> None:
        self.current_update_uses_delta = False
        self.download_status_text = "增量补丁不可用，正在下载完整更新包…"
        self.progress_animator.reset(self.download_status_text)

    @Slot()
    def on_download_thread_finished(self) -> None:
        self.progress_animator.stop()
        if not self.download_result_handled:
            self.update_progress.emit("", -2)
        thread_, self.download_thread = self.download_thread, None
        if thread_ is not None:
            thread_.deleteLater()

    @Slot(str)
    def handle_download_failure(self, message_: str) -> None:
        self.download_result_handled = True
        self.progress_animator.stop()
        LOGGER.warning("Velopack 更新下载或校验失败: %s", message_)
        self.update_progress.emit("", -2)
        if self.download_was_manual:
            QMessageBox.warning(
                self.main_window, "更新失败", f"更新包下载或校验失败：\n{message_}"
            )

    @Slot(object)
    def handle_download_finished(self, update_info_: Any) -> None:
        self.download_result_handled = True
        self.progress_animator.complete()
        self.mark_update_ready(update_info_)

    def mark_update_ready(self, update_info_: Any) -> None:
        self._ready_update_info = update_info_
        version_, notes_ = update_target_details(update_info_)
        self.progress_animator.stop()
        self.update_progress.emit("", -2)
        self.update_ready.emit(version_, notes_)

    def show_manual_update_message(self, update_info_: Any, *, ready: bool) -> None:
        version_, notes_ = update_target_details(update_info_)
        if ready:
            message_ = f"新版本 {version_ or '未知版本'} 的更新包已准备完成。"
            message_ += "\n\n请点击帮助菜单中的“重启更新”安装并重启。"
        else:
            message_ = f"发现新版本 {version_ or '未知版本'}。"
            message_ += "\n\n更新包将在后台下载，状态栏会显示进度；准备完成后帮助菜单中的“重启更新”将可用。"
        if notes_:
            message_ += f"\n\n更新内容：\n{notes_}"
        QMessageBox.information(self.main_window, "检查更新", message_)

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
        self.update_progress.emit("正在准备安装更新…", -1)
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
            self.update_progress.emit("", -2)
            QMessageBox.warning(
                self.main_window,
                "更新失败",
                reason_ or "更新前保存数据或停止后台任务失败。",
            )
            return False
        try:
            self.update_progress.emit("正在启动安装并重启…", -1)
            self.apply_update(update_info_)
        except Exception as exc:
            self.main_window._update_preparing = False
            LOGGER.exception("Velopack 更新应用失败")
            self.update_progress.emit("", -2)
            QMessageBox.warning(
                self.main_window,
                "更新失败",
                f"无法应用更新并重启：\n{type(exc).__name__}: {exc}",
            )
            return False
        return True

    def shutdown(self) -> bool:
        # SDK downloads cannot be forcibly terminated without risking corrupt packages.
        if any(t is not None and t.isRunning() for t in (self.check_thread, self.download_thread)):
            return False
        self.progress_animator.stop()
        return True
