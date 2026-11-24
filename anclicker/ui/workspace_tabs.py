"""Rounded, attached workspace tabs with a continuous page edge."""
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QRectF, QSize
from anclicker.platform.qt_compat.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from anclicker.platform.qt_compat.QtWidgets import QTabBar, QStyle, QStyleOptionTab, QStylePainter


class WorkspaceTabBar(QTabBar):
    EMBEDDED = {'主界面', '表格图', '流程图', '多功能', '录制', '网页录制', '对话Ai编程'}
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
        rect.adjust(.5, .5, -.5, 0)
        if index == 0:
            rect.setLeft(self._button_rect(index).left() + .5)
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
        outline = self._surface_path(edge, straight_left=index == 0)
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

    @staticmethod
    def _surface_path(rect, straight_left=False):
        # Tangent cubic arcs join upright sides to the page without a kink.
        radius = min(7, rect.width() / 2, rect.height() / 2)
        shoulder = 4
        k = .55228475
        l,t,r,b = rect.left(),rect.top(),rect.right(),rect.bottom()
        path = QPainterPath()
        if straight_left:
            path.moveTo(l,b)
        else:
            path.moveTo(l-shoulder,b)
            path.cubicTo(l-shoulder+k*shoulder,b,l,b-shoulder+k*shoulder,l,b-shoulder)
        path.lineTo(l,t+radius)
        path.cubicTo(l,t+radius-k*radius,l+radius-k*radius,t,l+radius,t)
        path.lineTo(r-radius,t)
        path.cubicTo(r-radius+k*radius,t,r,t+radius-k*radius,r,t+radius)
        path.lineTo(r,b-shoulder)
        path.cubicTo(r,b-shoulder+k*shoulder,r+shoulder-k*shoulder,b,r+shoulder,b)
        return path

    def _paint_groups(self, painter):
        painter.setPen(Qt.NoPen)
        for labels in self.GROUPS:
            group = QRectF()
            for index in range(self.count()):
                if self.isTabVisible(index) and self.tabText(index) in labels:
                    group = group.united(self._embedded_rect(index))
            if not group.isEmpty():
                painter.fillPath(self._surface_path(group, straight_left=group.left() < 1), QColor(self.colors['surface2']))

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
