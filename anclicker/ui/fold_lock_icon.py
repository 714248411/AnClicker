"""Compact, theme-aware vector locks; independent of emoji/font rendering."""
from anclicker.platform.qt_compat.QtCore import Qt, QRectF
from anclicker.platform.qt_compat.QtGui import QColor, QFontInfo, QPalette, QPainter, QPainterPath, QPen


def paint_fold_lock(painter, rect, locked, palette, font=None):
    color = QColor('#ffffff' if palette.color(QPalette.Base).lightness() < 128 else '#000000')
    # The table theme defaults to 13px text; use the current cell font so
    # stylesheet/font changes take effect immediately, including after restart.
    pixels = font.pixelSize() if font is not None else 13
    if pixels <= 0 and font is not None:
        pixels = QFontInfo(font).pixelSize()
        if pixels <= 0:
            pixels = font.pointSizeF() * painter.device().logicalDpiY() / 72.0
    if pixels <= 0:
        pixels = 13
    size = min(16.0, 14.0 * max(1, pixels) / 13.0, rect.width(), rect.height())
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(rect.center())
    painter.scale(size / 22.0, size / 22.0)
    pen = QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    shackle = QPainterPath()
    if locked:
        shackle.moveTo(5, 10)
        shackle.lineTo(5, 6)
        shackle.cubicTo(5, 0.7, 13, 0.7, 13, 6)
        shackle.lineTo(13, 10)
    else:
        # Open shackle swings out to the right, leaving a large visible gap.
        shackle.moveTo(13, 10)
        shackle.lineTo(13, 6)
        shackle.cubicTo(13, 0.7, 21, 0.7, 21, 6)
    body = QPainterPath()
    body.addRoundedRect(QRectF(2, 10, 14, 11), 2, 2)
    # The glyph is asymmetric within its 22-unit drawing canvas. Center its
    # actual outline, sharing the exact cell center used by the progress ring.
    center = shackle.boundingRect().united(body.boundingRect()).center()
    painter.translate(-center.x(), -center.y())
    painter.drawPath(shackle)
    if locked:
        keyhole = QPainterPath()
        keyhole.addRoundedRect(QRectF(8, 13, 2, 5), 1, 1)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPath(body.subtracted(keyhole))
    else:
        painter.drawPath(body)
    painter.restore()
