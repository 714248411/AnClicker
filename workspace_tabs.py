"""Rounded, attached workspace tabs with a continuous page edge."""
from qt_compat.QtCore import Qt, QPointF, QRectF, QSize
from qt_compat.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from qt_compat.QtWidgets import QTabBar, QStyle, QStyleOptionTab, QStylePainter


class WorkspaceTabBar(QTabBar):
    EMBEDDED = {'主界面', '表格图', '流程图', '多功能', '录制', '网页录制', '对话 Agent'}
    GROUPS = (('主界面',), ('表格图', '流程图', '多功能'), ('录制', '网页录制'))
    SURFACE_PAGES = {'表格图', '流程图', '多功能'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setMouseTracking(True)
        self.colors = {}
        self.hovered = -1

    def set_theme(self, colors):
        self.colors = colors
        self.update()

    def is_embedded(self, index):
        return self.tabText(index) in self.EMBEDDED

    def mouseMoveEvent(self, event):
        self.hovered = self.tabAt(event.pos())
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered = -1
        self.update()
        super().leaveEvent(event)

    def _gap(self, index):
        if self.tabText(index) == '录制':
            return max(12, self.fontMetrics().horizontalAdvance('  '))
        return 8 if self.tabText(index) == '表格图' else 0

    def _separator_rect(self, index):
        if self.tabText(index) != '录制':
            return QRectF()
        rect, gap = self.tabRect(index), self._gap(index)
        x = rect.right() - gap / 2 if self.layoutDirection() == Qt.RightToLeft else rect.left() + gap / 2
        return QRectF(x - 1, 7, 2, max(12, self.height() - 10))

    def _tab_font(self, selected=False):
        font = self.font()
        if font.pixelSize() > 0:
            font.setPixelSize(round(font.pixelSize() * 14 / 13))
        else:
            font.setPointSizeF(font.pointSizeF() * 14 / 13)
        font.setBold(True)
        return font

    def tabSizeHint(self, index):
        # Reserve the selected weight for every tab so switching never shifts it.
        metrics = QFontMetrics(self._tab_font(True))
        return QSize(metrics.horizontalAdvance(self.tabText(index)) + 30 + self._gap(index),
                     max(26, metrics.height() + 6))

    def minimumTabSizeHint(self, index):
        return self.tabSizeHint(index)

    def _button_rect(self, index):
        rect = self.tabRect(index)
        if self.layoutDirection() == Qt.RightToLeft:
            rect.adjust(0, 0, -self._gap(index), 0)
        else:
            rect.adjust(self._gap(index), 0, 0, 0)
        return rect

    def _label_rect(self, index):
        return QRectF(self._button_rect(index)).adjusted(2, 1, -2, -4)

    def _embedded_rect(self, index):
        rect = self._label_rect(index)
        rect.setBottom(self.height())
        return rect

    def tabAt(self, point):
        index = super().tabAt(point)
        return index if index < 0 or self._button_rect(index).contains(point) else -1

    def mousePressEvent(self, event):
        if self.tabAt(event.pos()) < 0:
            event.ignore()
            return
        super().mousePressEvent(event)

    def _paint_tab(self, painter, index):
        c = self.colors
        selected = index == self.currentIndex()
        hovered = index == self.hovered and self.isTabEnabled(index)
        rect = self._label_rect(index)
        edge = self._embedded_rect(index)
        radius, shoulder = 7, 4
        outline = QPainterPath()
        outline.moveTo(edge.left() - shoulder, edge.bottom())
        outline.quadTo(edge.left() + .5, edge.bottom(), edge.left() + .5, edge.bottom() - shoulder)
        outline.lineTo(edge.left() + .5, edge.top() + radius)
        outline.quadTo(edge.left() + .5, edge.top() + .5, edge.left() + radius, edge.top() + .5)
        outline.lineTo(edge.right() - radius, edge.top() + .5)
        outline.quadTo(edge.right() - .5, edge.top() + .5, edge.right() - .5, edge.top() + radius)
        outline.lineTo(edge.right() - .5, edge.bottom() - shoulder)
        outline.quadTo(edge.right() - .5, edge.bottom(), edge.right() + shoulder, edge.bottom())
        painter.save()
        background = c['surface'] if self.tabText(index) in self.SURFACE_PAGES else c['bg']
        if selected or hovered:
            painter.fillPath(outline, QColor(background if selected else c['surface3']))
        if selected:
            painter.setPen(QPen(QColor(c['line']), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(outline)
        painter.setFont(self._tab_font(selected))
        color = c['accent'] if selected or hovered else c['dim']
        painter.setPen(QColor(color))
        if not self.isTabEnabled(index):
            painter.setOpacity(.45)
        text = self.tabText(index)
        metrics = painter.fontMetrics()
        # Keep the glyphs close to the content edge, raised three pixels.
        baseline = self.height() - 6 - metrics.tightBoundingRect(text).bottom()
        x = rect.center().x() - metrics.horizontalAdvance(text) / 2
        painter.drawText(QPointF(x, baseline), text)
        if self.hasFocus() and selected:
            painter.setPen(QPen(QColor(c['accent']), 1, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(edge.adjusted(3, 3, -3, -1), 4, 4)
        painter.restore()

    def _paint_groups(self, painter):
        # One continuous silhouette per group; the individual items have no
        # idle box, border or horizontal inset between them.
        painter.setPen(Qt.NoPen)
        for labels in self.GROUPS:
            group = QRectF()
            for index in range(self.count()):
                if self.isTabVisible(index) and self.tabText(index) in labels:
                    group = group.united(QRectF(self._button_rect(index)))
            if group.isEmpty():
                continue
            group.adjust(2.5, 1.5, -2.5, 0)
            group.setBottom(self.height())
            radius, shoulder = 7, 4
            path = QPainterPath()
            path.moveTo(group.left() - shoulder, group.bottom())
            path.quadTo(group.left(), group.bottom(), group.left(), group.bottom() - shoulder)
            path.lineTo(group.left(), group.top() + radius)
            path.quadTo(group.left(), group.top(), group.left() + radius, group.top())
            path.lineTo(group.right() - radius, group.top())
            path.quadTo(group.right(), group.top(), group.right(), group.top() + radius)
            path.lineTo(group.right(), group.bottom() - shoulder)
            path.quadTo(group.right(), group.bottom(), group.right() + shoulder, group.bottom())
            path.closeSubpath()
            painter.fillPath(path, QColor(self.colors['surface2']))

    def paintEvent(self, event):
        painter = QStylePainter(self)
        if self.colors:
            painter.fillRect(self.rect(), QColor(self.colors['bg']))
            painter.setRenderHint(QPainter.Antialiasing)
            self._paint_groups(painter)
        order = [i for i in range(self.count()) if i != self.currentIndex()]
        if self.currentIndex() >= 0:
            order.append(self.currentIndex())
        for index in order:
            if not self.isTabVisible(index):
                continue
            if self.colors:
                self._paint_tab(painter, index)
            else:
                option = QStyleOptionTab()
                self.initStyleOption(option, index)
                option.rect = self._button_rect(index)
                painter.drawControl(QStyle.CE_TabBarTab, option)
        # Keep the group divider in the non-clickable gap, outside both tabs.
        color = QColor(self.colors["dim"]) if self.colors else self.palette().windowText().color()
        color.setAlpha(190)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        for index in range(self.count()):
            if self.isTabVisible(index):
                divider = self._separator_rect(index)
                if not divider.isEmpty():
                    painter.drawRoundedRect(divider, 1, 1)
