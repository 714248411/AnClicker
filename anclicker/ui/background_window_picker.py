"""Click-to-select a native window without delivering the selection click to it."""
from anclicker.platform.qt_compat.QtCore import QRect, Qt
from anclicker.platform.qt_compat.QtGui import QColor, QCursor, QPainter
from anclicker.platform.qt_compat.QtWidgets import QApplication, QDialog
from anclicker.platform.background_runtime import Windows


class BackgroundWindowPicker(QDialog):
    def __init__(self, windows=None):
        super().__init__()
        self.windows = windows or Windows()
        self.selection = None
        self.message = '点击目标窗口 · Ctrl + 点击选择子窗口 · Esc / 右键取消'
        self.setWindowTitle('点选后台窗口')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())
        available = screen.availableGeometry()
        width = min(620, available.width() - 24)
        self.hint = QRect(available.center().x() - self.x() - width // 2,
                          available.top() - self.y() + 16, width, 48)

    def paintEvent(self, event):
        painter = QPainter(self)
        # A nonzero alpha also makes the empty overlay consume the selection click.
        painter.fillRect(self.rect(), QColor(0, 0, 0, 8))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#20242c'))
        painter.drawRoundedRect(self.hint, 10, 10)
        painter.setPen(QColor('#ffffff'))
        painter.drawText(self.hint.adjusted(12, 0, -12, 0), Qt.AlignCenter, self.message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            event.accept()

    def mousePressEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.reject()
        elif event.button() == Qt.LeftButton:
            # Hide only after release: neither press nor release reaches the target.
            point = self.windows.cursor_position()
            child = bool(event.modifiers() & Qt.ControlModifier)
            # Hiding a QDialog ends exec(), even if an invalid target shows it
            # again. Transparency removes it from native hit testing without
            # ending the modal picker.
            opacity = self.windowOpacity()
            self.setWindowOpacity(0.0)
            try:
                self.selection = self.windows.at_point(point, child=child)
            except Exception as error:
                self.message = str(error) + '；Esc / 右键取消'
                self.setWindowOpacity(opacity)
                self.raise_();self.activateWindow();self.update()
                return
            self.accept()


def pick_background_window(owner):
    """Restore exactly the application's windows that were visible before picking."""
    picker = BackgroundWindowPicker()
    visible = [(widget, widget.windowOpacity()) for widget in QApplication.topLevelWidgets()
               if widget is not picker and widget.isVisible()]
    try:
        for widget, _ in visible:
            widget.setWindowOpacity(0.0)
        return picker.selection if picker.exec() == QDialog.Accepted else None
    finally:
        picker.close();picker.deleteLater()
        for widget, opacity in visible:
            try:
                widget.setWindowOpacity(opacity)
            except RuntimeError:
                pass
        if owner.isVisible():
            owner.window().raise_();owner.window().activateWindow()
