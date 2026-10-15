"""Long-press ordering for toolbar commands, with persistent stable action IDs."""
import json
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QTimer, Qt, QPoint, QPointF, QRectF, QVariantAnimation, QEasingCurve
from anclicker.platform.qt_compat.QtGui import QPainter, QColor, QPen
from anclicker.platform.qt_compat.QtWidgets import QToolButton, QWidget, QApplication, QStyle, QStyleOptionToolBar

SETTING = '工具栏按钮顺序'


class ToolbarDragPreview(QWidget):
    """Animate snapshots without disturbing Qt's layout or mouse capture."""
    DURATION_MS = 160

    def __init__(self, toolbar, action, last_action, pointer):
        super().__init__(toolbar)
        self.toolbar, self.action = toolbar, action
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self.setGeometry(toolbar.rect())
        self.vertical = toolbar.orientation() == Qt.Vertical
        self.reverse = not self.vertical and toolbar.layoutDirection() == Qt.RightToLeft
        self.items, self.pixmaps, self.original = [], {}, {}
        self.stationary = []
        action_widgets = set()
        for candidate in toolbar.actions():
            widget = toolbar.widgetForAction(candidate)
            if widget is None or not widget.isVisible():
                continue
            action_widgets.add(widget)
            rect = QRectF(widget.geometry())
            pixmap = widget.grab()
            if candidate == last_action:
                self.stationary.append((rect, pixmap))
            else:
                self.items.append(candidate)
                self.original[candidate] = rect
                self.pixmaps[candidate] = pixmap
        # Keep the overflow button and any other fixed toolbar widgets visible.
        for widget in toolbar.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            if widget is not self and widget not in action_widgets and widget.isVisible():
                self.stationary.append((QRectF(widget.geometry()), widget.grab()))
        self.origin = QPointF(pointer)
        self.ghost = QRectF(self.original[action])
        self.positions = {a: r.topLeft() for a, r in self.original.items()}
        self.targets = dict(self.positions)
        self.starts = dict(self.positions)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(self.DURATION_MS)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.animate)
        self.spacing = toolbar.style().pixelMetric(QStyle.PM_ToolBarItemSpacing, None, toolbar)
        self.show()
        self.raise_()

    def axis(self, point):
        return point.y() if self.vertical else (-point.x() if self.reverse else point.x())

    def slots(self):
        first = self.original[next(iter(self.original))]
        cursor = first.top() if self.vertical else (first.right() if self.reverse else first.left())
        result = {}
        for action in self.items:
            rect = QRectF(self.original[action])
            if self.vertical:
                rect.moveTop(cursor)
                cursor += rect.height() + self.spacing
            elif self.reverse:
                rect.moveRight(cursor)
                cursor -= rect.width() + self.spacing
            else:
                rect.moveLeft(cursor)
                cursor += rect.width() + self.spacing
            result[action] = rect
        return result

    def move_pointer(self, pointer):
        delta = QPointF(pointer) - self.origin
        self.ghost = self.original[self.action].translated(delta)
        if not self.rect().contains(pointer):
            self.update()
            return
        center = self.axis(self.ghost.center())
        previous = list(self.items)
        index = self.items.index(self.action)
        slots = self.slots()
        # Adjacent midpoints provide hysteresis: shifted buttons do not bounce
        # back into the gap while the pointer is stationary.
        while index > 0 and center <= self.axis(slots[self.items[index - 1]].center()):
            self.items[index - 1], self.items[index] = self.items[index], self.items[index - 1]
            index -= 1
            slots = self.slots()
        while index + 1 < len(self.items) and center >= self.axis(slots[self.items[index + 1]].center()):
            self.items[index + 1], self.items[index] = self.items[index], self.items[index + 1]
            index += 1
            slots = self.slots()
        if previous != self.items:
            self.animation.stop()
            self.starts = dict(self.positions)
            self.targets = {a: rect.topLeft() for a, rect in slots.items()}
            self.animation.start()
        self.update()

    def animate(self, value):
        self.positions = {a: self.starts[a] + (self.targets[a] - self.starts[a]) * value for a in self.items}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.toolbar.palette().window())
        option = QStyleOptionToolBar()
        option.initFrom(self.toolbar)
        option.rect = self.rect()
        self.toolbar.style().drawControl(QStyle.CE_ToolBar, option, painter, self.toolbar)
        for rect, pixmap in self.stationary:
            painter.drawPixmap(rect.topLeft(), pixmap)
        accent = self.toolbar.palette().highlight().color()
        tint = QColor(accent)
        tint.setAlpha(35)
        gap = self.slots()[self.action].adjusted(1, 1, -1, -1)
        painter.setPen(QPen(accent, 1, Qt.DashLine))
        painter.setBrush(tint)
        painter.drawRoundedRect(gap, 4, 4)
        for action in self.items:
            if action != self.action:
                painter.drawPixmap(self.positions[action], self.pixmaps[action])
        painter.setOpacity(0.94)
        painter.drawPixmap(self.ghost.topLeft(), self.pixmaps[self.action])
        painter.setOpacity(1)
        painter.setPen(QPen(accent, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.ghost.adjusted(1, 1, -1, -1), 4, 4)


class ToolbarReorder(QObject):
    HOLD_MS = 450

    def __init__(self, window, last_action):
        super().__init__(window)
        self.window, self.toolbar, self.last_action = window, window.toolBar, last_action
        self.pressed = None
        self.dragging = False
        self.preview = None
        self.pointer = QPoint()
        self.toolbar.installEventFilter(self)
        QApplication.instance().installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.arm)
        try:
            saved = json.loads(window.db.get_setting_value(SETTING) or '[]')
        except (ValueError, TypeError):
            saved = []
        self.order = list(dict.fromkeys(x for x in saved if isinstance(x, str))) if isinstance(saved, list) else []
        for index, action in enumerate(self.toolbar.actions()):
            action.setProperty('toolbarOrderId', 'base:' + (action.objectName() or str(index)))

    def key(self, action):
        return action.property('toolbarOrderId')

    def refresh(self):
        if self.dragging:
            return
        actions = [a for a in self.toolbar.actions() if a != self.last_action]
        ranks = {key: i for i, key in enumerate(self.order)}
        desired = sorted(actions, key=lambda a: ranks.get(self.key(a), len(ranks)))
        if desired != actions:
            # Only move out-of-place actions; repeated insertion can hide Qt buttons.
            for index, action in enumerate(desired):
                current = self.toolbar.actions()
                if current[index] != action:
                    self.toolbar.insertAction(current[index], action)
                    button = self.toolbar.widgetForAction(action)
                    if button and action.isVisible():
                        button.show()
        for action in desired:
            button = self.toolbar.widgetForAction(action)
            if isinstance(button, QToolButton) and not action.isSeparator():
                button.installEventFilter(self)

    def arm(self):
        if self.pressed is not None:
            self.dragging = True
            self.pressed.setDown(False)
            self.pressed.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.preview = ToolbarDragPreview(self.toolbar, self.pressed.defaultAction(),
                                              self.last_action, self.pointer)

    def cancel(self):
        self.timer.stop()
        if self.preview is not None:
            self.preview.animation.stop()
            self.preview.hide()
            self.preview.deleteLater()
            self.preview = None
        if self.pressed is not None:
            self.pressed.setDown(False)
            self.pressed.unsetCursor()
        self.pressed = None
        self.dragging = False

    def move_to(self, action, position):
        if not self.toolbar.rect().contains(position):
            return
        vertical = self.toolbar.orientation() == Qt.Orientation.Vertical
        coordinate = position.y() if vertical else position.x()
        before = self.last_action
        for candidate in self.toolbar.actions():
            if candidate == action or candidate == self.last_action or not candidate.isVisible():
                continue
            rect = self.toolbar.actionGeometry(candidate)
            button = self.toolbar.widgetForAction(candidate)
            if rect.isEmpty() or (button and not button.isVisible()):
                continue
            midpoint = rect.center().y() if vertical else rect.center().x()
            if coordinate < midpoint:
                before = candidate
                break
        self.toolbar.insertAction(before, action)
        button = self.toolbar.widgetForAction(action)
        if button and action.isVisible():
            button.show()
        self.order = [self.key(a) for a in self.toolbar.actions() if a != self.last_action and self.key(a)]
        self.window.db.set_setting_value(SETTING, json.dumps(self.order, ensure_ascii=False))
        self.refresh()

    def commit_preview(self, items):
        # Hidden overflow actions keep their relative positions.
        visible = set(items)
        ordered = iter(items)
        desired = [next(ordered) if a in visible else a for a in self.toolbar.actions()]
        for index, action in enumerate(desired):
            current = self.toolbar.actions()
            if current[index] != action:
                self.toolbar.insertAction(current[index], action)
                widget = self.toolbar.widgetForAction(action)
                if widget and action.isVisible():
                    widget.show()
        self.order = [self.key(a) for a in desired if a != self.last_action and self.key(a)]
        self.window.db.set_setting_value(SETTING, json.dumps(self.order, ensure_ascii=False))
        self.refresh()

    def eventFilter(self, obj, event):
        kind = event.type()
        if self.pressed is not None:
            if kind == QEvent.Type.KeyPress and event.key() == Qt.Key_Escape:
                self.cancel()
                return True
            if (kind == QEvent.Type.WindowDeactivate and obj is self.window) or (obj is self.toolbar and kind in (QEvent.Type.Resize, QEvent.Type.Hide, QEvent.Type.ActionAdded, QEvent.Type.ActionRemoved)):
                self.cancel()
        if (not isinstance(obj, QToolButton) or obj.parent() != self.toolbar
                or obj.defaultAction() not in self.toolbar.actions() or obj.defaultAction() == self.last_action):
            return False
        if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if not obj.isEnabled():
                return False
            self.cancel()
            self.pressed = obj
            self.pointer = self.toolbar.mapFromGlobal(event.globalPos())
            obj.setDown(True)
            self.timer.start(self.HOLD_MS)
            return True
        if obj is self.pressed:
            if kind == QEvent.Type.MouseMove:
                self.pointer = self.toolbar.mapFromGlobal(event.globalPos())
                if self.preview is not None:
                    self.preview.move_pointer(self.pointer)
                return True
            if kind == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                dragging = self.dragging
                inside = obj.rect().contains(event.pos())
                position = self.toolbar.mapFromGlobal(event.globalPos())
                items = None
                if dragging and self.preview is not None and self.toolbar.rect().contains(position):
                    self.preview.move_pointer(position)
                    items = list(self.preview.items)
                self.cancel()
                if items is not None:
                    self.commit_preview(items)
                elif not dragging and inside:
                    obj.click()
                return True
            if kind == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                self.cancel()
                return True
            if kind in (QEvent.Type.Hide, QEvent.Type.WindowDeactivate):
                self.cancel()
        return False
