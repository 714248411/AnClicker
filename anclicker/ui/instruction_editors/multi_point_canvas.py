"""屏幕多点画布：连续取点、拖动标记，确认后一次提交。"""
import sys
from anclicker.platform.qt_compat.QtCore import QPoint, QRectF, Qt
from anclicker.platform.qt_compat.QtGui import QColor, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'ctypes': ('import', 'ctypes', (), False),
    'wintypes': ('from', 'ctypes', ('wintypes',), 0),
    'pyautogui_module': ('from', 'anclicker.execution.actions', ('pyautogui_module',), 0),
})



class MultiPointCanvas(QDialog):
    def __init__(self, points=(), parent=None):
        super().__init__(parent)
        self.points = [tuple(point) for point in points]
        self._drag_index = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        screen = QApplication.primaryScreen()
        if screen: self.setGeometry(screen.virtualGeometry())
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addStretch()
        toolbar = QWidget(self)
        toolbar.setObjectName('pointCanvasToolbar')
        toolbar.setStyleSheet('QWidget#pointCanvasToolbar {background:rgba(38,52,73,235);border-radius:7px;} QPushButton {font-size:12px;padding:3px 8px;border-radius:4px;background:#f1f3f8;color:#263449;} QPushButton:hover {background:#cbd8ff;}')
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(8, 4, 8, 4)
        bar.setSpacing(5)
        label = QLabel('单击取点 · 拖动调整 · Enter 完成 · Esc 取消')
        label.setStyleSheet('color:white;background:transparent;font-size:12px;padding:2px;')
        bar.addWidget(label)
        for text, callback in [('撤回', self.undo), ('完成', self.accept), ('取消', self.reject)]:
            button = QPushButton(text)
            button.setAutoDefault(False)
            button.setFixedSize(48, 26)
            button.clicked.connect(callback)
            bar.addWidget(button)
        toolbar.setFixedSize(toolbar.sizeHint())
        top.addWidget(toolbar)
        top.addStretch()
        layout.addLayout(top); layout.addStretch()

    def local_point(self, point):
        if sys.platform == 'win32':
            ctypes = _module_imports.load('ctypes')
            wintypes = _module_imports.load('wintypes')
            native = wintypes.POINT(*map(int, point))
            if ctypes.windll.user32.ScreenToClient(wintypes.HWND(int(self.winId())), ctypes.byref(native)):
                ratio = self.devicePixelRatioF()
                return QPoint(round(native.x / ratio), round(native.y / ratio))
        return self.mapFromGlobal(QPoint(*map(int, point)))

    def capture_point(self):
        pyautogui_module = _module_imports.load('pyautogui_module')
        point = pyautogui_module().position()
        return (int(point.x), int(point.y))

    def marker_radius(self, index):
        return max(16, self.fontMetrics().horizontalAdvance(str(index + 1)) / 2 + 7)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(20, 25, 35, 35))
        for index, point in enumerate(self.points):
            center = self.local_point(point)
            radius = self.marker_radius(index)
            rect = QRectF(center.x()-radius, center.y()-radius, radius*2, radius*2)
            painter.setBrush(QColor(255, 35, 35, 128))
            painter.setPen(QPen(QColor(255, 230, 230, 200), 1))
            painter.drawEllipse(rect)
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, str(index+1))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        pos = event.pos()
        self._drag_index = next((i for i in range(len(self.points)-1, -1, -1)
            if (self.local_point(self.points[i])-pos).manhattanLength() <= self.marker_radius(i)), None)
        if self._drag_index is None:
            self.points.append(self.capture_point())
            self._drag_index = len(self.points)-1
        self.update()

    def mouseMoveEvent(self, event):
        if self._drag_index is not None and event.buttons() & Qt.LeftButton:
            self.points[self._drag_index] = self.capture_point()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_index is not None:
            self.points[self._drag_index] = self.capture_point()
            self._drag_index = None
            self.update()

    def undo(self):
        if self.points: self.points.pop()
        self._drag_index = None
        self.update()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter): self.accept()
        elif event.key() == Qt.Key_Backspace: self.undo()
        else: super().keyPressEvent(event)
