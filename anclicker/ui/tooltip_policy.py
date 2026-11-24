"""User controls for hover tips and tips too large for the application."""
import re
from collections import OrderedDict
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt
from anclicker.platform.qt_compat.QtGui import QFontMetrics, QTextDocument
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget, QMenu, QAbstractItemView, QToolTip

SHOW_ALL = '显示悬浮提示'
SHOW_LONG = '显示过长悬浮提示'


class TooltipPolicy(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._measurements = OrderedDict()
        self.show_all = window.db.get_setting_value(SHOW_ALL) != 'False'
        self.show_long = window.db.get_setting_value(SHOW_LONG) == 'True'
        menu = window.menu_2
        menu.addSeparator()
        self.all_action = menu.addAction('显示悬浮提示')
        self.all_action.setCheckable(True)
        self.all_action.setChecked(self.show_all)
        self.long_action = menu.addAction('显示过长悬浮提示')
        self.long_action.setCheckable(True)
        self.long_action.setChecked(self.show_long)
        self.all_action.toggled.connect(self._set_all)
        self.long_action.toggled.connect(self._set_long)
        QApplication.instance().installEventFilter(self)

    def _set_all(self, enabled):
        self.show_all = bool(enabled)
        self.window.db.set_setting_value(SHOW_ALL, str(self.show_all))
        QToolTip.hideText()

    def _set_long(self, enabled):
        self.show_long = bool(enabled)
        self.window.db.set_setting_value(SHOW_LONG, str(self.show_long))
        QToolTip.hideText()

    def owns(self, widget):
        obj = widget
        while obj is not None:
            if obj is self.window or getattr(obj, '_workspace_owner', None) is self.window:
                return True
            obj = obj.parent()
        return False

    def allow(self, text, widget):
        if not self.show_all:
            return False
        if self.show_long or not text:
            return True
        font = QToolTip.font()
        text = str(text)
        key = (text, font.toString(), font.resolve())
        size = self._measurements.get(key)
        if size is None:
            if re.search(r'<[A-Za-z][^>]*>', text):
                document = QTextDocument()
                document.setDefaultFont(font)
                document.setHtml(text)
                document.adjustSize()
                size = (document.idealWidth() + 16, document.size().height() + 12)
            else:
                metrics = QFontMetrics(font)
                lines = text.splitlines() or ['']
                size = (max(metrics.horizontalAdvance(line) for line in lines) + 16,
                        len(lines) * metrics.lineSpacing() + 12)
            # Bound retained user text and measurements for long-running sessions.
            if len(text) <= 8192:
                self._measurements[key] = size
                if len(self._measurements) > 128:
                    self._measurements.popitem(last=False)
        else:
            self._measurements.move_to_end(key)
        width, height = size
        surface = widget.window() if isinstance(widget, QWidget) else self.window
        if isinstance(surface, QMenu) or surface.width() < 100:
            surface = self.window
        screen = surface.screen() or self.window.screen()
        available = screen.availableGeometry() if screen else None
        max_width = surface.width()
        max_height = surface.height()
        if available is not None:
            max_width = min(max_width, available.width())
            max_height = min(max_height, available.height())
        return width <= max_width and height <= max_height

    def eventFilter(self, obj, event):
        if event.type() != QEvent.ToolTip or not isinstance(obj, QWidget) or not self.owns(obj):
            return False
        text = obj.toolTip()
        if isinstance(obj, QMenu):
            action = obj.actionAt(event.pos())
            if action is not None:
                text = action.toolTip()
        view = obj if isinstance(obj, QAbstractItemView) else obj.parentWidget()
        if isinstance(view, QAbstractItemView) and not obj.isWindow():
            # Popup children are separate windows, not table viewport content.
            # QWidget.mapFrom(widget, ...) requires an ancestor in Qt 5; a
            # sibling/table popup can cause a native access violation.
            point = view.viewport().mapFromGlobal(obj.mapToGlobal(event.pos()))
            index = view.indexAt(point)
            if index.isValid():
                text = index.data(Qt.ToolTipRole) or text
        if not self.allow(text, obj):
            QToolTip.hideText()
            event.accept()
            return True
        return False
