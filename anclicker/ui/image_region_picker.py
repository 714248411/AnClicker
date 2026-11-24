"""Fixed image region: drag a rectangle or click a native window."""
from anclicker.platform.qt_compat.QtCore import Qt, QRect, QPoint
from anclicker.platform.qt_compat.QtWidgets import QRubberBand, QApplication, QDialog
from anclicker.ui.background_window_picker import BackgroundWindowPicker
from anclicker.platform.image_region import window_region


class ImageRegionPicker(BackgroundWindowPicker):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('框选固定区域')
        self.message = '拖动框选固定区域 · 单击选取窗口范围 · Ctrl + 单击选子窗口 · Esc / 右键取消'
        self.region = None
        self.origin = None
        self.band = QRubberBand(QRubberBand.Rectangle, self)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.origin = self.windows.cursor_position()
            self.local_origin = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.origin is not None and event.buttons() & Qt.LeftButton:
            self.band.setGeometry(QRect(self.local_origin, event.position().toPoint()).normalized())
            self.band.show()

    def mouseReleaseEvent(self, event):
        self.band.hide()
        if event.button() == Qt.RightButton:
            self.reject(); return
        if event.button() != Qt.LeftButton or self.origin is None:
            return
        end = self.windows.cursor_position()
        start = self.origin
        self.origin = None
        if (event.position().toPoint()-self.local_origin).manhattanLength() < QApplication.startDragDistance():
            opacity = self.windowOpacity()
            self.setWindowOpacity(0)
            try:
                target = self.windows.at_point(end, child=bool(event.modifiers() & Qt.ControlModifier))
                self.region = window_region(target, self.windows)
            except Exception as error:
                self.message = str(error) + '；Esc / 右键取消'
                self.setWindowOpacity(opacity); self.update(); return
        else:
            self.region = (min(start[0],end[0]), min(start[1],end[1]), abs(end[0]-start[0]), abs(end[1]-start[1]))
            if not self.region[2] or not self.region[3]:
                return
        self.accept()


def pick_fixed_region(owner):
    picker = ImageRegionPicker()
    visible = [(w, w.windowOpacity()) for w in QApplication.topLevelWidgets() if w is not picker and w.isVisible()]
    try:
        for w, _ in visible: w.setWindowOpacity(0)
        return picker.region if picker.exec() == QDialog.Accepted else None
    finally:
        picker.deleteLater()
        for w, opacity in visible:
            try: w.setWindowOpacity(opacity)
            except RuntimeError: pass
        if owner.isVisible(): owner.raise_(); owner.activateWindow()
