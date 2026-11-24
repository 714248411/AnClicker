"""Two independently fading columns sharing one dismissible popup."""
from anclicker.platform.qt_compat.QtCore import QEvent, QEventLoop, QObject, QPoint, QRectF, QTimer, Qt
from anclicker.platform.qt_compat.QtGui import QCursor, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import QApplication, QFrame, QHBoxLayout, QMenu, QStyle, QStyleOptionMenuItem


class _ClosingClickGuard(QObject):
    """Consume the closing click's release/context event after the popup exits."""
    def __init__(self, button):
        app = QApplication.instance()
        super().__init__(app)
        self.button = button
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish)
        app.installEventFilter(self)
        self.timer.start(1000)

    def finish(self):
        QApplication.instance().removeEventFilter(self)
        self.timer.stop()
        self.deleteLater()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.ContextMenu:
            return True
        if event.type() == QEvent.MouseButtonRelease and event.button() == self.button:
            self.timer.start(120)
            return True
        if event.type() == QEvent.MouseButtonPress:
            self.finish()
        return False


class MenuColumn(QMenu):
    def __init__(self, owner):
        super().__init__(owner)
        self.column_opacity = 1.0

    def set_column_opacity(self, opacity):
        self.column_opacity = opacity
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRegion(event.region())
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setOpacity(self.column_opacity)
        painter.setRenderHint(QPainter.Antialiasing)
        background = self._rounded_menu_background
        painter.setBrush(background.background)
        painter.setPen(QPen(background.border, 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 9, 9)
        for action in self.actions():
            if not action.isVisible():
                continue
            option = QStyleOptionMenuItem()
            self.initStyleOption(option, action)
            option.rect = self.actionGeometry(action)
            self.style().drawControl(QStyle.CE_MenuItem, option, painter, self)
        painter.end()


class TwoColumnMenu(QFrame):
    def __init__(self, left, right, owner):
        super().__init__(owner, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.columns = (left, right)
        self.chosen = None
        self.loop = QEventLoop(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for menu in self.columns:
            menu.setParent(self, Qt.Widget)
            menu.setAttribute(Qt.WA_TranslucentBackground)
            menu.setMouseTracking(True)
            menu.setFixedSize(menu.sizeHint())
            menu.removeEventFilter(menu._rounded_menu_background)
            layout.addWidget(menu, 0, Qt.AlignTop)
            menu.triggered.connect(self._choose)
        self._active_column(0)

    def _active_column(self, index):
        for column, menu in enumerate(self.columns):
            menu.set_column_opacity(1.0 if column == index else 0.2)


    def _choose(self, action):
        if action.isEnabled() and not any(sub.menuAction() == action for sub in self.findChildren(QMenu)):
            self.chosen = action
            self.close()

    def _column_of(self, widget):
        while widget is not None:
            if widget in self.columns:
                return self.columns.index(widget)
            widget = widget.parentWidget() if hasattr(widget, 'parentWidget') else None
        return None

    def _position_submenu(self, menu):
        parent = menu.parentWidget()
        if parent not in self.columns:
            return
        index = self.columns.index(parent)
        area = (QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()).availableGeometry()
        width, height = menu.width(), menu.height()
        left = self.x() - width - 4
        right = self.x() + self.width() + 4
        preferred = (left, right) if index == 0 else (right, left)
        x = next((value for value in preferred if area.left() <= value and value + width <= area.right()+1), preferred[0])
        y = parent.mapToGlobal(parent.actionGeometry(menu.menuAction()).topLeft()).y()
        menu.move(max(area.left(), min(x, area.right()-width+1)),
                  max(area.top(), min(y, area.bottom()-height+1)))

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Show and isinstance(watched, QMenu):
            self._position_submenu(watched)
        if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            if kind == QEvent.MouseButtonPress:
                menus = (*self.columns, *self.findChildren(QMenu))
                inside = any(menu.isVisible() and menu.rect().contains(menu.mapFromGlobal(event.globalPos()))
                             for menu in menus)
                if event.button() == Qt.RightButton or not inside:
                    # Native submenus otherwise consume the first outside click,
                    # leaving the two-column parent popup behind.
                    self._closing_click_guard = _ClosingClickGuard(event.button())
                    self.close()
                    return True
            if event.button() == Qt.LeftButton and isinstance(watched, QMenu) and self._column_of(watched) is not None:
                action = watched.actionAt(event.pos())
                has_submenu = action is not None and any(sub.menuAction() == action for sub in watched.findChildren(QMenu))
                if action is not None and action.isEnabled() and not action.isSeparator() and not has_submenu:
                    watched.setActiveAction(action)
                    if kind == QEvent.MouseButtonRelease:
                        self.chosen = action
                        self.close()
                        action.trigger()
                    return True
        if kind == QEvent.ContextMenu:
            return True
        if kind == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.close()
            return True
        if kind in (QEvent.Enter, QEvent.MouseMove, QEvent.FocusIn):
            index = self._column_of(watched)
            if index is not None:
                self._active_column(index)
        return super().eventFilter(watched, event)

    def hideEvent(self, event):
        # Actions may open modal dialogs before exec() returns. Stop filtering
        # application input as soon as this popup is dismissed.
        QApplication.instance().removeEventFilter(self)
        for menu in self.findChildren(QMenu):
            if menu not in self.columns:
                menu.hide()
        self.loop.quit()
        super().hideEvent(event)

    def exec(self, position):
        self.adjustSize()
        screen = QApplication.screenAt(position) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        self.move(QPoint(max(area.left(), min(position.x(), area.right()-self.width()+1)),
                         max(area.top(), min(position.y(), area.bottom()-self.height()+1))))
        app = QApplication.instance()
        app.installEventFilter(self)
        try:
            self.show()
            for index, menu in enumerate(self.columns):
                if menu.rect().contains(menu.mapFromGlobal(QCursor.pos())):
                    self._active_column(index)
            self.columns[0].setFocus()
            self.loop.exec_()
            return self.chosen
        finally:
            app.removeEventFilter(self)
            self.close()


def exec_two_column_menu(left, right, position, owner):
    popup = TwoColumnMenu(left, right, owner)
    try:
        return popup.exec(position)
    finally:
        popup.deleteLater()
