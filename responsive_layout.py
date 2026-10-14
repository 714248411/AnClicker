"""Wrap compact option/button rows when the workspace becomes narrow."""
from qt_compat.QtCore import QRect, QSize, Qt
from qt_compat.QtWidgets import QLayout, QWidgetItem


class FlowLayout(QLayout):
    def __init__(self, parent=None, *, center_rows=False):
        super().__init__(parent)
        self._items = []
        self.center_rows = center_rows
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)

    def addItem(self, item):
        self._items.append(item)

    def addWidget(self, widget, *args):
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))

    def addStretch(self, *args):
        pass

    def addSpacing(self, *args):
        pass

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), False)

    def minimumSize(self):
        return QSize(0, 0)

    def sizeHint(self):
        width = sum(item.sizeHint().width() + self.spacing() for item in self._items)
        return QSize(width, self.heightForWidth(max(1, width)))

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, True)

    def _arrange(self, rect, apply):
        left, top, right, bottom = self.getContentsMargins()
        available = max(1, rect.width() - left - right)
        x, y, line_height = 0, top, 0
        gap = max(0, self.spacing())
        row = []

        def place_row():
            if apply:
                for item, offset, width, height in row:
                    dy = (line_height - height) // 2 if self.center_rows else 0
                    item.setGeometry(QRect(rect.x() + left + offset,
                                           rect.y() + y + dy, width, height))

        for item in self._items:
            if item.isEmpty():
                continue
            hint = item.sizeHint()
            width = min(available, hint.width())
            if x and x + width > available:
                place_row()
                row = []
                x, y, line_height = 0, y + line_height + gap, 0
            row.append((item, x, width, hint.height()))
            x += width + gap
            line_height = max(line_height, hint.height())
        place_row()
        return y + line_height + bottom
