from __future__ import annotations

from anclicker.platform.qt_compat.QtCore import QEvent, QObject, QPoint, QSize, QTimer, Qt
from anclicker.platform.qt_compat.QtGui import QGuiApplication, QScreen
from anclicker.platform.qt_compat.QtWidgets import QDialog, QWidget


class WindowStateController(QObject):
    """保存和恢复顶层窗口尺寸、最大化状态及可选的位置。"""

    def __init__(
        self,
        window: QWidget,
        db,
        window_name: str,
        *,
        center: bool = True,
        enable_maximize_button: bool = True,
        remember_position: bool = False,
    ):
        super().__init__(window)
        self.window = window
        self.db = db
        self.window_name = str(window_name or "").strip()
        self.center = bool(center)
        self.remember_position = bool(remember_position)
        self.default_size = QSize(window.width(), window.height())
        self.restore_maximized_on_show = False
        self._maximized_requested = False
        self._saved = False
        self._position_save_timer = QTimer(self)
        self._position_save_timer.setSingleShot(True)
        self._position_save_timer.setInterval(400)
        self._position_save_timer.timeout.connect(self._save_position_after_move)

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
            elif event.type() in (QEvent.Type.Move, QEvent.Type.Resize, QEvent.Type.WindowStateChange):
                if self.remember_position and self.window.isVisible():
                    self._saved = False
                    self._position_save_timer.start()
            elif event.type() == QEvent.Type.Close:
                self._position_save_timer.stop()
                self.save_window_state()
                QTimer.singleShot(0, self._reset_after_ignored_close)
        return super().eventFilter(watched, event)

    def _save_position_after_move(self) -> None:
        if not self.window.isVisible() or self.window.isMinimized():
            return
        self._saved = False
        self.save_window_state()
        # Closing must still capture the final geometry and mode.
        self._saved = False

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
        compact=getattr(getattr(self.window,'view_workspace',None),'compact',None)
        if compact is not None and compact.active:
            # Close filters may run before compact mode has restored the main
            # window. Persist the captured main geometry, never the console.
            is_maximized=compact.was_maximized
            geometry = compact.normal_rect
        else:
            geometry = self.window.geometry()
            if is_maximized or self.window.isMinimized():
                geometry = self.window.normalGeometry()
                if is_maximized:
                    geometry = getattr(self.window, '_restore_client_geometry', geometry)
        size = geometry.size() if geometry.isValid() else self._normal_window_size()
        options = {}
        if self.remember_position and geometry.isValid():
            options['position'] = (geometry.x(), geometry.y())
        self.db.save_window_size(
            size.width(),
            size.height(),
            self.window_name,
            maximized=is_maximized,
            **options,
        )

    def _restore_window_state(self) -> None:
        if not self.window_name:
            return
        state = self.db.get_window_state(self.window_name)
        position = state.get("position") if state and self.remember_position else None
        screen = (QGuiApplication.screenAt(QPoint(*position)) if position else None) or self._window_screen()
        if state is None:
            size = self._bounded_window_size(
                self.default_size.width(), self.default_size.height()
            )
        else:
            self.restore_maximized_on_show = bool(state.get("maximized", False))
            size = self._bounded_window_size(*state["size"], screen=screen)
        self.window.resize(size)
        if position is not None:
            # A removed monitor or changed work area must not hide the title bar.
            available = screen.availableGeometry()
            self.window.move(
                max(available.left(), min(position[0], available.right() - self.window.width() + 1)),
                max(available.top(), min(position[1], available.bottom() - self.window.height() + 1)),
            )
        elif self.center:
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

    def _bounded_window_size(self, width: int, height: int, screen=None) -> QSize:
        available = (screen or self._window_screen()).availableGeometry()
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
    remember_position: bool = False,
) -> WindowStateController:
    controller = WindowStateController(
        window,
        db,
        window_name,
        center=center,
        enable_maximize_button=enable_maximize_button,
        remember_position=remember_position,
    )
    window._window_state_controller = controller
    return controller
