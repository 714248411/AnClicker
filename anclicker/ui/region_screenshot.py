"""In-memory desktop snapshot in the native image recognition coordinate system."""
import io
import sys
from PIL import ImageGrab
from anclicker.platform.qt_compat.QtGui import QPixmap


def capture_desktop():
    image = ImageGrab.grab(all_screens=True)
    left = top = 0
    if sys.platform == 'win32':
        import win32api
        left, top = win32api.GetSystemMetrics(76), win32api.GetSystemMetrics(77)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    pixmap = QPixmap()
    if not pixmap.loadFromData(buffer.getvalue()):
        raise ValueError('无法读取屏幕截图')
    return pixmap, (left, top, image.width, image.height)
