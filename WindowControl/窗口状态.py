from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QSize, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtWidgets import QDialog, QWidget


class WindowStateController(QObject):
    """统一保存和恢复顶层窗口尺寸及最大化状态。"""

    def __init__(
        self,
        window: QWidget,
        db,
        window_name: str,
        *,
        center: bool = True,
        enable_maximize_button: bool = True,
    ):
        super().__init__(window)
        self.window = window
        self.db = db
        self.window_name = str(window_name or "").strip()
        self.center = bool(center)
        self.default_size = QSize(window.width(), window.height())
        self.restore_maximized_on_show = False
        self._maximized_requested = False
        self._saved = False

        if enable_maximize_button:
            self.window.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
            self.window.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)

        self._restore_window_state()
        self.window.installEventFilter(self)
        if isinstance(self.window, QDialog):
            self.window.finished.connect(lambda *_: self.save_window_state())

    def eventFilter(self, watched, event):
        if watched is self.window:
            if event.type() == QEvent.Type.Show:
                self._saved = False
                self._restore_maximized_after_show()
            elif event.type() == QEvent.Type.Close:
                self.save_window_state()
                QTimer.singleShot(0, self._reset_after_ignored_close)
        return super().eventFilter(watched, event)

    def _reset_after_ignored_close(self) -> None:
        if self.window.isVisible():
            self._saved = False

    def save_window_state(self) -> None:
        if self._saved or not self.window_name:
            return
        self._saved = True
        is_maximized = bool(
            self.window.windowState() & Qt.WindowState.WindowMaximized
        )
        size = self._normal_window_size() if is_maximized else self.window.size()
        self.db.save_window_size(
            size.width(),
            size.height(),
            self.window_name,
            maximized=is_maximized,
        )

    def _restore_window_state(self) -> None:
        if not self.window_name:
            return
        state = self.db.get_window_state(self.window_name)
        if state is None:
            size = self._bounded_window_size(
                self.default_size.width(), self.default_size.height()
            )
        else:
            self.restore_maximized_on_show = bool(state.get("maximized", False))
            size = self._bounded_window_size(*state["size"])
        self.window.resize(size)
        if self.center:
            self._center_window_on_screen()

    def _restore_maximized_after_show(self) -> None:
        if not self.restore_maximized_on_show or self._maximized_requested:
            return
        self._maximized_requested = True
        QTimer.singleShot(0, self.window.showMaximized)

    def _normal_window_size(self) -> QSize:
        normal_geometry = self.window.normalGeometry()
        if normal_geometry.isValid():
            normal_size = normal_geometry.size()
            if normal_size.width() > 0 and normal_size.height() > 0:
                return self._bounded_window_size(
                    normal_size.width(), normal_size.height()
                )
        return self._bounded_window_size(
            self.default_size.width(), self.default_size.height()
        )

    def _bounded_window_size(self, width: int, height: int) -> QSize:
        available = self._window_screen().availableGeometry()
        minimum = self.window.minimumSize()
        return QSize(
            max(max(1, minimum.width()), min(int(width), available.width())),
            max(max(1, minimum.height()), min(int(height), available.height())),
        )

    def _center_window_on_screen(self) -> None:
        screen = self._window_screen()
        frame_geometry = self.window.frameGeometry()
        frame_geometry.moveCenter(screen.availableGeometry().center())
        self.window.move(frame_geometry.topLeft())

    def _window_screen(self) -> QScreen:
        return self.window.screen() or QGuiApplication.primaryScreen()


def install_window_state(
    window: QWidget,
    db,
    window_name: str,
    *,
    center: bool = True,
    enable_maximize_button: bool = True,
) -> WindowStateController:
    controller = WindowStateController(
        window,
        db,
        window_name,
        center=center,
        enable_maximize_button=enable_maximize_button,
    )
    window._window_state_controller = controller
    return controller
