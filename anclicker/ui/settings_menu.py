"""Settings label opens the dialog; its arrow and hover expand sections."""
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt, QTimer
from anclicker.platform.qt_compat.QtWidgets import QMenu

class SettingsMenuClick(QObject):
    def __init__(self, menu, action, window):
        super().__init__(menu)
        self.action, self.window = action, window
        self.pressed = False
        menu.installEventFilter(self)

    def eventFilter(self, menu, event):
        kind = event.type()
        if kind not in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            return False
        if event.button() != Qt.LeftButton:
            return False
        rect = menu.actionGeometry(self.action)
        arrow_width = max(24, menu.fontMetrics().height() + 8)
        on_label = menu.actionAt(event.pos()) is self.action and event.pos().x() < rect.right() - arrow_width
        if kind == QEvent.MouseButtonPress:
            self.pressed = on_label
            return on_label
        if self.pressed:
            self.pressed = False
            if on_label:
                self.action.menu().hide()
                menu.hide()
                QTimer.singleShot(0, lambda: self.window.show_windows('设置'))
            return True
        return False


def install_settings_click(window):
    window.actions_2.triggered.connect(lambda: window.show_windows('设置'))
    window._settings_click_filters = [SettingsMenuClick(menu, window.actions_2, window)
        for menu in window.findChildren(QMenu) if window.actions_2 in menu.actions()]
