"""Frozen-screen rectangle snapping with an always-available manual drag fallback."""
from datetime import datetime
from pathlib import Path

from qt_compat.QtCore import QPoint, QRect, QRectF, Qt
from qt_compat.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from qt_compat.QtWidgets import QApplication, QDialog


def edge_rectangles(image):
    """Canny + closed contours, bounded resolution/candidate count (no network)."""
    import cv2
    import numpy as np
    rgb = np.asarray(image.convert('RGB'))
    height, width = rgb.shape[:2]
    ratio = min(1.0, 1920 / max(width, height))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if ratio < 1:
        gray = cv2.resize(gray, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 30, 100)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = set()
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 20 * ratio or h < 16 * ratio or w*h > width*height*ratio*ratio*.98:
            continue
        if abs(cv2.contourArea(contour)) / (w*h) < .65:
            continue
        rectangles.add((round(x/ratio), round(y/ratio), round(w/ratio), round(h/ratio)))
    return sorted(rectangles, key=lambda r: r[2]*r[3])[:2500]


def snap_rectangle(rectangles, x, y):
    return next((r for r in rectangles if r[0] <= x < r[0]+r[2] and r[1] <= y < r[1]+r[3]), None)


def capture_screen_pixels(screen):
    """Use the same Qt screen for geometry and native-pixel capture.

    Do not multiply a logical screen size by a cached/global DPI value: Windows
    can change scaling while the application is running.
    """
    from PIL import Image
    if screen is None:
        raise RuntimeError('无法获取当前屏幕')
    captured = screen.grabWindow(0).toImage().convertToFormat(QImage.Format.Format_RGB888)
    if captured.isNull():
        raise RuntimeError('无法截取屏幕，请检查屏幕录制权限')
    return Image.frombytes('RGB', (captured.width(), captured.height()),
                           bytes(captured.constBits()), 'raw', 'RGB', captured.bytesPerLine())


class SmartCaptureDialog(QDialog):
    """Primary-screen capture; physical pixels and Qt logical pixels stay separate."""
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        screen = QApplication.primaryScreen()
        self.image = (image if image is not None else capture_screen_pixels(screen)).convert('RGB')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(screen.geometry() if screen else QRect(0, 0, self.image.width, self.image.height))
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        raw = self.image.tobytes()
        self.background = QImage(raw, self.image.width, self.image.height,
                                 self.image.width*3, QImage.Format.Format_RGB888).copy()
        self.candidates = edge_rectangles(self.image)
        self.selection = QRect()
        self.origin = None
        self.dragged = False

    def _pixel(self, position):
        return QPoint(max(0, min(self.image.width-1, round(position.x()*self.image.width/self.width()))),
                      max(0, min(self.image.height-1, round(position.y()*self.image.height/self.height()))))

    def mouseMoveEvent(self, event):
        point = self._pixel(event.position())
        if self.origin is not None and (point-self.origin).manhattanLength() > 3:
            self.dragged = True
        if self.dragged:
            self.selection = QRect(self.origin, point).normalized()
        else:
            candidate = snap_rectangle(self.candidates, point.x(), point.y())
            self.selection = QRect(*candidate) if candidate else QRect()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.reject()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.mouseMoveEvent(event)
            self.origin = self._pixel(event.position())
            self.dragged = False

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self.mouseMoveEvent(event)
        self.origin = None
        self.dragged = False
        if self.selection.width() >= 2 and self.selection.height() >= 2:
            self.accept()

    def selected_region(self):
        if self.result() != QDialog.DialogCode.Accepted:
            return None
        rect = self.selection.intersected(QRect(0, 0, self.image.width, self.image.height))
        return rect.x(), rect.y(), rect.width(), rect.height()

    def save_selection(self, path):
        region = self.selected_region()
        if region is None:
            raise ValueError('尚未选择截图区域')
        x, y, w, h = region
        self.image.crop((x, y, x+w, y+h)).save(str(path))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.background)
        sx, sy = self.width()/self.image.width, self.height()/self.image.height
        rect = QRectF(self.selection.x()*sx, self.selection.y()*sy,
                      self.selection.width()*sx, self.selection.height()*sy)
        shade = QPainterPath()
        shade.addRect(QRectF(self.rect()))
        if not rect.isEmpty():
            shade.addRect(rect)
        shade.setFillRule(Qt.FillRule.OddEvenFill)
        painter.fillPath(shade, QColor(0, 0, 0, 95))
        painter.setPen(QPen(QColor('#3b9cff'), 2))
        painter.drawRect(rect)
        painter.fillRect(10, 10, min(self.width()-20, 720), 38, QColor(20, 24, 30, 220))
        painter.setPen(QColor('white'))
        painter.drawText(QRect(20, 10, self.width()-40, 38), Qt.AlignmentFlag.AlignVCenter,
                         '悬停吸附边缘 · 单击确认 · 拖拽手动框选 · Esc/右键取消（主屏）')


def capture_path(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f'截图_{datetime.now():%Y%m%d_%H%M%S_%f}.png'
