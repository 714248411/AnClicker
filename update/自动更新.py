from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import velopack
from qt_compat.QtCore import QCoreApplication, QThread, QTimer, Signal

from update.config import update_url

LOGGER = logging.getLogger(__name__)
UpdateManagerFactory = Callable[[str], Any]


def is_velopack_managed(
    executable_path: str | Path | None = None,
    *,
    frozen: bool | None = None,
) -> bool:
    """判断进程是否位于 Velopack 管理的 current 目录。"""
    frozen_ = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if not frozen_:
        return False
    executable_ = Path(executable_path or sys.executable).resolve()
    content_dir_ = executable_.parent
    root_dir_ = content_dir_.parent
    return (
        content_dir_.name.casefold() == "current"
        and (content_dir_ / "sq.version").is_file()
        and (root_dir_ / "Update.exe").is_file()
    )


def update_target_details(update_info_: Any) -> tuple[str, str]:
    """提取目标版本和 Markdown 更新说明。"""
    target_ = getattr(update_info_, "TargetFullRelease", None) or update_info_
    version_ = str(getattr(target_, "Version", "") or "").strip()
    notes_ = str(getattr(target_, "NotesMarkdown", "") or "").strip()
    return version_, notes_


def is_delta_update(update_info_: Any) -> bool:
    """Velopack 计划使用增量包时，回调的前 70% 对应下载阶段。"""
    return bool(getattr(update_info_, "DeltasToTarget", None))


class CheckUpdateThread(QThread):
    pending_update_found = Signal(object)
    update_found = Signal(object)
    no_update = Signal()
    check_skipped = Signal(str)
    check_failed = Signal(str)

    def __init__(
        self,
        parent=None,
        *,
        source_url: str | None = None,
        manager_factory: UpdateManagerFactory = velopack.UpdateManager,
        managed_checker: Callable[[], bool] = is_velopack_managed,
    ):
        super().__init__(parent)
        self.source_url = source_url if source_url is not None else update_url()
        self.manager_factory = manager_factory
        self.managed_checker = managed_checker

    def run(self) -> None:
        if not self.managed_checker():
            self.check_skipped.emit("当前进程不是 Velopack 管理版本，跳过更新检查。")
            return
        if not self.source_url:
            self.check_skipped.emit("此构建未配置自更新地址。")
            return
        try:
            manager_ = self.manager_factory(self.source_url)
            pending_update_ = manager_.get_update_pending_restart()
            if pending_update_ is not None:
                self.pending_update_found.emit(pending_update_)
                return
            update_info_ = manager_.check_for_updates()
        except Exception as exc:
            self.check_failed.emit(f"{type(exc).__name__}: {exc}")
            return
        if update_info_ is None:
            self.no_update.emit()
        else:
            self.update_found.emit(update_info_)


class DownloadUpdateThread(QThread):
    download_progress = Signal(int)
    delta_patch_started = Signal()
    full_download_fallback_started = Signal()
    download_finished = Signal(object)
    download_failed = Signal(str)

    def __init__(
        self,
        update_info_: Any,
        parent=None,
        *,
        source_url: str | None = None,
        manager_factory: UpdateManagerFactory = velopack.UpdateManager,
    ):
        super().__init__(parent)
        self.update_info = update_info_
        self.source_url = source_url if source_url is not None else update_url()
        self.manager_factory = manager_factory
        self.uses_delta = is_delta_update(update_info_)
        self._last_raw_progress: int | None = None
        self._delta_patch_reported = False
        self._full_fallback_reported = False

    def _handle_velopack_progress(self, progress_: int) -> None:
        progress_ = max(0, min(100, int(progress_)))
        if self.uses_delta and not self._full_fallback_reported:
            if self._last_raw_progress is not None and progress_ < self._last_raw_progress:
                self._full_fallback_reported = True
                self.full_download_fallback_started.emit()
            elif progress_ >= 70 and not self._delta_patch_reported:
                self._delta_patch_reported = True
                self.delta_patch_started.emit()
        self._last_raw_progress = progress_
        self.download_progress.emit(progress_)

    def run(self) -> None:
        try:
            manager_ = self.manager_factory(self.source_url)
            manager_.download_updates(
                self.update_info,
                progress_callback=self._handle_velopack_progress,
            )
        except Exception as exc:
            self.download_failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.download_finished.emit(self.update_info)


def apply_update_and_restart(
    update_info_: Any,
    *,
    source_url: str | None = None,
    restart_args: list[str] | None = None,
    manager_factory: UpdateManagerFactory = velopack.UpdateManager,
) -> None:
    """应用已下载更新并重启当前程序。"""
    manager_ = manager_factory(source_url if source_url is not None else update_url())
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError('应用事件循环尚未初始化')
    # Start the updater first. Only exit after the SDK has accepted the request.
    manager_.wait_exit_then_apply_updates(update_info_, silent=True, restart=True, restart_args=restart_args)
    QTimer.singleShot(0, app.quit)
