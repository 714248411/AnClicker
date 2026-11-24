"""Movable workspace panels; the command table remains in the central tabs."""
import base64
import json

from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt, QMimeData, QTimer, QByteArray, QSize, QPoint, QRect, QRectF
from anclicker.platform.qt_compat.QtGui import QDrag, QCursor, QPainter, QColor, QPen
from anclicker.platform.qt_compat.QtWidgets import (QApplication, QDockWidget, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QScrollArea, QFrame, QDialog, QToolTip, QSizePolicy)

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'style_context_menu': ('from', 'anclicker.ui.context_menu_style', ('style_context_menu',), 0),
    'AdaptivePanelSizer': ('from', 'anclicker.ui.adaptive_panels', ('AdaptivePanelSizer',), 0),
    'QSignalBlocker': ('from', 'anclicker.platform.qt_compat.QtCore', ('QSignalBlocker',), 0),
    'style_settings_combos': ('from', 'anclicker.ui.settings_combo', ('style_settings_combos',), 0),
    'parameter_popup_size': ('from', 'anclicker.ui.instruction_editors.compact_settings', ('parameter_popup_size',), 0),
    'QMessageBox': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QMessageBox',), 0),
    'fit_initial_popup': ('from', 'anclicker.ui.instruction_editors.compact_settings', ('fit_initial_popup',), 0),
})


FIXED_PANELS = {'table', 'flow'}
PANEL_MIME = 'application/x-anclicker-panel'
PIN_RESULT = 731
AREAS = {'left': Qt.LeftDockWidgetArea, 'right': Qt.RightDockWidgetArea,
         'top': Qt.TopDockWidgetArea, 'bottom': Qt.BottomDockWidgetArea}
LABELS = {'top':'上栏', 'center':'中栏', 'bottom':'下栏', 'left':'左栏', 'right':'右栏'}


def set_panel_hint(manager,widget,text):
    widget.setProperty('dockEditableHint',text)
    widget.setToolTip(text if manager.editable else '')


class DropZone(QLabel):
    def __init__(self, manager, key):
        super().__init__(LABELS[key], manager.host)
        self.manager, self.key = manager, key
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet('background: rgba(70,100,210,210); color: white; border: 2px solid #b6c8ff; border-radius: 10px; font-size: 16px;')
        self.hide()

    def dragEnterEvent(self, event):
        if self.manager.editable and event.mimeData().hasFormat(PANEL_MIME): event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.manager.editable:
            event.ignore(); self.manager.hide_targets(); return
        key = bytes(event.mimeData().data(PANEL_MIME)).decode('utf-8')
        if self.manager.drop_on_target(key, self.key): event.acceptProposedAction()
        self.manager.hide_targets()


class DockPlaceholder(QWidget):
    """A text-height notice that cannot absorb splitter space."""
    def __init__(self, title, callback, compact=False):
        super().__init__()
        self._compact = compact
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)
        self.notice = QLabel(title + '已停靠', self)
        self.notice.setToolTip(title + '已停靠到其他栏目')
        self.back = QLabel('<a href="return">返回中栏</a>', self)
        self.back.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        self.back.setOpenExternalLinks(False)
        self.back.linkActivated.connect(lambda *_: callback())
        layout.addWidget(self.notice, 0, Qt.AlignVCenter)
        layout.addWidget(self.back, 0, Qt.AlignVCenter)
        layout.addStretch()
        self._fit_height()

    def _fit_height(self):
        if self._compact:
            height = max(self.notice.sizeHint().height(), self.back.sizeHint().height()) + 2
            if self.minimumHeight() != height or self.maximumHeight() != height:
                self.setFixedHeight(height)

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange, QEvent.LayoutRequest) and hasattr(self, 'back'):
            self._fit_height()
        return result


class FloatingPanelButton(QPushButton):
    """Small vector icons remain clear at every display scale."""
    def __init__(self, kind, hint, parent):
        super().__init__('', parent)
        self.kind = kind
        self._drag_origin = None
        self._drag_moved = False
        self.setFixedSize(28, 24)
        self.setToolTip(hint)
        self.setAccessibleName(hint)
        self.setCheckable(kind in ('pin', 'follow'))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet('QPushButton {border:none; border-radius:5px; padding:0; background:transparent;}'
                           'QPushButton:hover {background:rgba(100,130,200,35);}'
                           'QPushButton:checked {background:rgba(70,130,220,65);}')

    def mousePressEvent(self, event):
        if self.kind == 'more' and event.button() == Qt.LeftButton:
            dock = self.parentWidget().dock
            self._drag_origin = (event.globalPos(), dock.pos()) if not dock.pinned else None
            self._drag_moved = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None and event.buttons() & Qt.LeftButton:
            dock = self.parentWidget().dock
            delta = event.globalPos() - self._drag_origin[0]
            if not dock.pinned and (self._drag_moved or delta.manhattanLength() >= QApplication.startDragDistance()):
                self._drag_moved = True
                self.setDown(False)
                dock.move(self._drag_origin[1] + delta)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin = None
        if self._drag_moved:
            self._drag_moved = False
            self.setDown(False)
            self.parentWidget().dock.manager.schedule_save()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width()/2, self.height()/2)
        painter.setPen(QPen(self.palette().buttonText().color(), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.kind == 'more':
            painter.setBrush(self.palette().buttonText())
            for x in (-5, 0, 5): painter.drawEllipse(QRectF(x-1, -1, 2, 2))
        elif self.kind == 'pin':
            painter.drawLine(-4,-6,4,-6); painter.drawLine(-3,-6,-3,0); painter.drawLine(3,-6,3,0)
            painter.drawLine(-3,0,-5,3); painter.drawLine(3,0,5,3); painter.drawLine(-5,3,5,3)
            painter.drawLine(0,3,0,7)
        elif self.kind == 'follow':
            painter.drawRoundedRect(QRectF(-8,-6,9,8),1,1)
            painter.drawRoundedRect(QRectF(-1,-1,9,7),1,1)
            painter.drawLine(-6,5,-3,5); painter.drawLine(-4,3,-2,5); painter.drawLine(-2,5,-4,7)
        else:
            painter.drawRoundedRect(QRectF(-7,-6,14,12),1,1)
            painter.drawLine(6,0,-3,0); painter.drawLine(-3,0,0,-3); painter.drawLine(-3,0,0,3)
        painter.end()


class FloatingPanelControls(QFrame):
    def __init__(self, title):
        super().__init__(title)
        self.dock = title.dock
        self.expanded = False
        self.setObjectName('floatingPanelControls')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 0, 3, 0); layout.setSpacing(2)
        self.more = FloatingPanelButton('more', '展开面板操作', self)
        self.pin = FloatingPanelButton('pin', '固定位置并置顶（再次点击取消固定）', self)
        self.follow = FloatingPanelButton('follow', '跟随主窗口相对移动', self)
        self.restore = FloatingPanelButton('restore', '恢复进主窗口', self)
        for button in (self.more, self.pin, self.follow, self.restore): layout.addWidget(button)
        self.more.clicked.connect(self.toggle)
        self.pin.clicked.connect(self.dock.set_pinned)
        self.follow.clicked.connect(self.dock.set_follow_main)
        self.restore.clicked.connect(self.dock.restore_to_main)
        self.sync()

    def toggle(self):
        self.expanded = not self.expanded
        self.sync()

    def sync(self):
        colors = self.dock.manager.view.THEMES[self.dock.manager.view.theme_mode]
        self.setStyleSheet('QFrame#floatingPanelControls {background:'+colors['surface2']+'; border:1px solid '+colors['line']+'; border-top:0; border-bottom-left-radius:8px; border-bottom-right-radius:8px;}')
        for button in (self.pin, self.follow, self.restore): button.setVisible(self.expanded)
        self.pin.setChecked(self.dock.pinned)
        self.follow.setChecked(self.dock.follow_main)
        self.more.setToolTip(('收起面板操作' if self.expanded else '展开面板操作') + ('；已固定，不能拖动' if self.dock.pinned else '；按住拖动窗口'))
        self.setFixedSize(124 if self.expanded else 34, 26)
        self.move(max(0, (self.parentWidget().width()-self.width())//2), 2 if self.parentWidget() is self.dock else 0)


class PanelTitle(QLabel):
    def sizeHint(self):
        size = super().sizeHint()
        if self.dock.isFloating():
            size.setHeight(self.height())
            return size
        dock = self.dock
        if dock.key in ('palette', 'controls') and not dock.isFloating():
            manager = dock.manager
            if manager.suspended:
                size.setHeight(0);return size
            if manager.host.dockWidgetArea(dock) in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
                tabs = manager.view.tabs
                content_top = tabs.mapTo(manager.host, QPoint()).y() + tabs.tabBar().height()
                # Inactive tabbed docks are parked at large negative coordinates by Qt.
                # Their position must never become a minimum-height constraint.
                if manager.host.tabifiedDockWidgets(dock):
                    size.setHeight(0)
                else:
                    size.setHeight(min(tabs.tabBar().height(), max(0, content_top - max(0, dock.y()))))
        return size

    def __init__(self, dock):
        super().__init__('', dock)
        self.setAccessibleName(dock.windowTitle() + '拖拽条')
        self.setFixedHeight(0 if dock.key in ('palette','controls','log') or dock.key.startswith('parameters_') else 12)
        self.dock = dock
        if dock.key.startswith('parameters_') or dock.key == 'agent':
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 0, 6, 0)
            self.setIndent(10)
            self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setStyleSheet("QLabel#dockPanelTitle {background:transparent; border:none; font-weight:600; font-size:13px;}")
            layout.addStretch()
            self.close_button = QPushButton('×', self)
            self.close_button.setFixedSize(26, 26)
            self.close_button.setStyleSheet("QPushButton {padding:0; margin:0; border:none; border-radius:6px; background:transparent; font-size:18px;} QPushButton:hover {background:rgba(128,128,128,35);}")
            self.close_button.setToolTip('关闭并取消未保存修改')
            self.close_button.clicked.connect(dock.close)
            layout.addWidget(self.close_button)
            self.close_button.hide()
            if dock.key == 'agent':
                self.setFixedHeight(36);self.setText('对话Ai编程 · 设置与流程草稿')
                self.close_button.setText('↩');self.close_button.setToolTip('返回主界面，保留当前对话与草稿');self.close_button.show()
        self.setObjectName('dockPanelTitle')
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(30)
        set_panel_hint(dock.manager,self,dock.windowTitle() + '：拖动拉出；双击窗口化/嵌入；右击打开面板菜单')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        controls = getattr(self, 'floating_controls', None)
        if controls is not None and controls.parentWidget() is self:
            controls.move(max(0, (self.width()-controls.width())//2), 0)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dock.manager.editable:
                self.dock.manager.float_panel(self.dock.key, not self.dock.isFloating())
            event.accept()
        else: event.ignore()

    def contextMenuEvent(self, event):
        self.dock.manager.panel_menu(self.dock.key, event.globalPos())
        event.accept()


class PanelDock(QDockWidget):
    def __init__(self, manager, key, title):
        super().__init__(title, manager.host)
        self.manager, self.key = manager, key
        self.pinned = False
        self.follow_main = False
        self._changing_chrome = False
        self.setObjectName('panelDock_' + key)
        self.setProperty('instructionParameter', key.startswith('parameters_'))
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self._embedded_title = PanelTitle(self)
        self.setTitleBarWidget(self._embedded_title)
        self._title_drag_filter = PanelDragFilter(manager, self._embedded_title, key)
        if key.startswith('parameters_'):
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAutoFillBackground(False)
            self.topLevelChanged.connect(self._parameter_window_chrome)
        self.setMinimumSize(0, 0)
        set_panel_hint(manager,self,'拖动标题停靠到上、下、左、右栏；右击标题可选择并排、堆叠或返回中栏')
        self.dockLocationChanged.connect(lambda *_: manager.schedule_save())
        self.topLevelChanged.connect(lambda *_: manager.schedule_save())
        self.topLevelChanged.connect(lambda *_: manager.configure_dock(self))
        self.topLevelChanged.connect(self._floating_chrome)
        self._embedded_title.floating_controls = FloatingPanelControls(self._embedded_title)
        self._embedded_title.floating_controls.hide()

    def _floating_chrome(self, floating):
        if self._changing_chrome:
            return
        title = self._embedded_title
        controls = title.floating_controls
        if floating:
            self.setContentsMargins(1, 0, 1, 1)
            title.setFixedHeight(28 if self.key.startswith('parameters_') else 0)
            controls.setParent(self)
            title.setText('')
            title.setStyleSheet('QLabel#dockPanelTitle {background:transparent; border:none;}')
            controls.sync(); controls.show(); controls.raise_()
        else:
            self.setContentsMargins(0, 0, 0, 0)
            controls.expanded = False; controls.hide(); controls.setParent(title)
            title.setFixedHeight(0 if self.key in ('palette','controls','log') or self.key.startswith('parameters_') else 36 if self.key == 'agent' else 12)
            if self.key == 'agent': title.setText('对话Ai编程 · 设置与流程草稿')
        if not floating and self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)

    def set_pinned(self, enabled):
        self.pinned = bool(enabled)
        if self.isFloating():
            geometry, visible = self.geometry(), self.isVisible()
            self._changing_chrome = True
            try:
                self.setWindowFlag(Qt.WindowStaysOnTopHint, self.pinned)
                self.setGeometry(geometry)
                if visible: self.show()
            finally:
                self._changing_chrome = False
        self._embedded_title.floating_controls.sync()
        self.manager.configure_dock(self)
        self.manager.schedule_save()

    def set_follow_main(self, enabled):
        self.follow_main = bool(enabled)
        self._embedded_title.floating_controls.sync()
        self.manager.schedule_save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        title = getattr(self, '_embedded_title', None)
        controls = getattr(title, 'floating_controls', None)
        if controls is not None and controls.parentWidget() is self:
            controls.move(max(0, (self.width()-controls.width())//2), 2)
            controls.raise_()

    def restore_to_main(self):
        if self.key in self.manager.placeholders:
            self.manager.return_center(self.key)
        else:
            self.manager.float_panel(self.key, False)

    def _parameter_window_chrome(self, floating):
        features = QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        if floating: features |= QDockWidget.DockWidgetClosable
        title = self._embedded_title
        self.setContentsMargins(8, 6, 8, 8) if floating else self.setContentsMargins(0, 0, 0, 0)
        title.setFixedHeight(32 if floating else 0)
        title.setText(self.windowTitle() if floating else '')
        title.close_button.setVisible(floating)
        editor = self.manager.parameters.get(self.key)
        if editor is not None:
            heading = editor.findChild(QLabel, 'titleLabel')
            if heading is not None:
                # Floating editors already identify the instruction in the corner caption.
                # Embedded editors retain their title as the panel's drag handle.
                heading.setVisible(not floating)
        self.setFeatures(features)
        self.manager.configure_dock(self)

    def paintEvent(self, event):
        if not self.key.startswith('parameters_') or not self.isFloating():
            return super().paintEvent(event)
        colors = self.manager.view.THEMES[self.manager.view.theme_mode]
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(colors['surface']))
        painter.setPen(QPen(QColor(colors['line']), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 14, 14)
        painter.end()

    def contextMenuEvent(self, event):
        self.manager.panel_menu(self.key, event.globalPos())

    def closeEvent(self, event):
        if self.key.startswith('parameters_'):
            editor = self.manager.parameters.get(self.key)
            if editor is not None: editor.reject()
        elif self.key == 'palette':
            self.manager.view.palette_collapsed = True
            self.manager.view._update_view_actions()
        elif self.key == 'controls':
            self.manager.view.controls_action.setChecked(False)
        else:
            QTimer.singleShot(0, lambda: self.manager.return_center(self.key))
        event.accept()
        self.manager.schedule_save()


class DragCancelGuard(QObject):
    def __init__(self):
        super().__init__()
        self.cancelled = False
    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.cancelled = True
        return False


class PanelDragFilter(QObject):
    def __init__(self, manager, widget, key=None, *, header_only=False, context_menu=True):
        super().__init__(widget)
        self.manager, self.key, self.origin = manager, key, None
        self.header_only, self.context_menu = header_only, context_menu
        widget.installEventFilter(self)
        widget.setContextMenuPolicy(Qt.DefaultContextMenu)
        set_panel_hint(manager,widget,'拖到上、下、左、右栏；右击选择停靠位置。表格与流程图固定在中栏。')

    def eventFilter(self, watched, event):
        kind = event.type()
        dock = self.manager.docks.get(self.key)
        if kind in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonDblClick) and dock is not None and dock.isFloating() and dock.pinned:
            self.origin = None
            return False
        if kind == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton and self.key:
            on_title = not self.header_only or (event.pos().y() <= 28 and event.pos().x() <= watched.fontMetrics().horizontalAdvance(watched.title()) + 30)
            if on_title:
                dock = self.manager.ensure_dock(self.key) if self.manager.editable else None
                if dock is not None:
                    self.manager.float_panel(self.key, not dock.isFloating())
                self.origin = None
                return True
        if kind == QEvent.ContextMenu and self.context_menu:
            key = self.key or self.manager.tab_key(watched.tabAt(event.pos()))
            if key and key not in FIXED_PANELS:
                self.manager.panel_menu(key, event.globalPos())
                return True
        if not self.manager.editable:
            self.origin = None
            return False
        if kind == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if self.header_only and (event.pos().y() > 28 or event.pos().x() > watched.fontMetrics().horizontalAdvance(watched.title()) + 30):
                self.origin = None
                return False
            key = self.key or self.manager.tab_key(watched.tabAt(event.pos()))
            self.origin = (event.pos(), key) if key and key != 'table' else None
        elif kind == QEvent.MouseButtonRelease:
            self.origin = None
        elif kind == QEvent.MouseMove and self.origin and event.buttons() & Qt.LeftButton:
            point, key = self.origin
            if (event.pos()-point).manhattanLength() >= QApplication.startDragDistance():
                self.origin = None
                drag = QDrag(watched)
                mime = QMimeData(); mime.setData(PANEL_MIME, key.encode('utf-8')); drag.setMimeData(mime)
                self.manager.show_targets(key)
                guard = DragCancelGuard()
                QApplication.instance().installEventFilter(guard)
                try:
                    result = drag.exec(Qt.MoveAction)
                finally:
                    QApplication.instance().removeEventFilter(guard)
                    self.manager.hide_targets()
                if result == Qt.IgnoreAction and not guard.cancelled:
                    point = QCursor.pos()
                    if not self.manager.host.rect().contains(self.manager.host.mapFromGlobal(point)):
                        self.manager.float_panel(key, True)
                        dock = self.manager.docks.get(key)
                        if dock is not None and not key.startswith('parameters_'): dock.move(point.x()-30,point.y()-6)
                return True
        return False


class ParameterPinFilter(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
        self.manager = None
        self.key = None
        dialog.installEventFilter(self)
        # Keep text fields' native context menus; empty dialog space offers pinning.
        dialog.setToolTip('右击设置窗口空白处，可固定到主界面')

    def eventFilter(self, watched, event):
        if event.type() == QEvent.ContextMenu:
            menu = QMenu(self.dialog)
            style_context_menu = _module_imports.load('style_context_menu')
            style_context_menu(menu, self.dialog)
            if self.manager is None:
                menu.addAction('融入主窗体（固定）', lambda: self.dialog.done(PIN_RESULT))
            else:
                dock = self.manager.docks[self.key]
                menu.addAction('融入主窗体' if dock.isFloating() else '弹出为独立窗口',
                               lambda: self.manager.float_parameters(self.key, not dock.isFloating()))
            menu.exec(event.globalPos()); menu.deleteLater()
            return True
        return False


class DockWorkspace(QObject):
    def __init__(self, view):
        super().__init__(view.window)
        self.view, self.window = view, view.window
        self.docks, self.placeholders, self.parameters = {}, {}, {}
        self.restoring, self.suspended = True, False
        self.controls_horizontal = False
        self.editable = self.window.db.get_setting_value('可编辑视图') == 'True'
        self.host = QMainWindow()
        self.host.setObjectName('dockWorkspace')
        self.host.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AnimatedDocks)
        self.host.setDockNestingEnabled(True)
        self.host.setMinimumSize(0, 0)
        self.pages = dict(view._remembered_pages())
        self.pages['log'] = view.table_splitter.widget(1)
        self.titles = dict(zip(self.pages, ['主界面','表格图','流程图','多功能','录制','网页录制','对话Ai编程','运行日志']))
        grid = self.window.gridLayout_4
        grid.removeWidget(view.workspace_splitter)
        self.host.setCentralWidget(view.tabs)
        self.create_dock('palette', '快捷指令', self.window.instructionPaletteHost, 'left')
        self.create_dock('controls', '控制与操作', view.controls_scroll, 'right')
        self.docks['controls'].dockLocationChanged.connect(lambda *_: self.update_controls_layout())
        self.docks['controls'].topLevelChanged.connect(lambda *_: self.update_controls_layout())
        view.workspace_splitter.hide()
        grid.addWidget(self.host, 0, 0, 1, 3)
        self.host.resizeDocks([self.docks['palette'],self.docks['controls']], [190,245], Qt.Horizontal)
        self.filters = [PanelDragFilter(self, view.tabs.tabBar()),
                        PanelDragFilter(self, self.pages['log'].findChild(QLabel), 'log'),
                        PanelDragFilter(self, self.window.groupBox_3, 'controls', header_only=True),
                        PanelDragFilter(self, self.window.workspace.palette.search_edit, 'palette', context_menu=False)]
        self.targets = [DropZone(self, key) for key in LABELS]
        self.target_panel = None
        self.dragged_panel = None
        self.target_timer = QTimer(self)
        self.target_timer.setInterval(40)
        self.target_timer.timeout.connect(lambda: self.update_targets(QCursor.pos()))
        self.save_timer = QTimer(self); self.save_timer.setSingleShot(True); self.save_timer.setInterval(250)
        self.save_timer.timeout.connect(self.save)
        self._main_position = self.window.pos()
        self.window.installEventFilter(self)
        self.host.installEventFilter(self)
        view.tabs.tabBar().installEventFilter(self)
        AdaptivePanelSizer = _module_imports.load('AdaptivePanelSizer')
        self.scalers = [AdaptivePanelSizer(self.window.instructionPaletteHost,
                           self.window.instructionPaletteHost, 150, palette=True),
                        AdaptivePanelSizer(view.controls_scroll.viewport(),
                           self.window.groupBox_3, 280)]
        view.controls_scroll.setMinimumWidth(100)
        self.window.instructionPaletteHost.setMinimumWidth(90)
        self.window.groupBox_3.setMinimumWidth(0)
        self.restore()
        self.restoring = False
        self.update_controls_layout()

    def configure_dock(self, dock):
        if getattr(dock, '_programmatic_move', False): return
        dock.setAllowedAreas(Qt.AllDockWidgetAreas if self.editable else Qt.NoDockWidgetArea)
        features = QDockWidget.NoDockWidgetFeatures
        if self.editable and not (dock.isFloating() and dock.pinned):
            features |= QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable
        if (dock.key.startswith('parameters_') or dock.key == 'agent') and dock.isFloating(): features |= QDockWidget.DockWidgetClosable
        dock.setFeatures(features)

    def _set_floating(self, dock, floating):
        # Explicit menu actions remain available while native drag docking is locked.
        dock._programmatic_move = True
        try:
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            dock.setFeatures(dock.features() | QDockWidget.DockWidgetFloatable)
            if not floating and self.host.dockWidgetArea(dock) == Qt.NoDockWidgetArea:
                self.host.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.setFloating(floating)
        finally:
            dock._programmatic_move = False
            self.configure_dock(dock)

    def set_editable(self, enabled):
        self.editable = bool(enabled)
        self.window.db.set_setting_value('可编辑视图', str(self.editable))
        if not self.editable:
            self.hide_targets();QToolTip.hideText()
        for widget in self.host.findChildren(QWidget):
            text=widget.property('dockEditableHint')
            if text:widget.setToolTip(text if self.editable else '')
        for dock in self.docks.values(): self.configure_dock(dock)

    def tab_key(self, index):
        page = self.view.tabs.widget(index) if index >= 0 else None
        if page is None:return None
        return next((key for key, widget in self.pages.items()
                     if page is widget or page is self.placeholders.get(key)), None)

    def create_dock(self, key, title, widget, area, *, floating=False):
        dock = PanelDock(self, key, title)
        dock.setWidget(widget)
        self.docks[key] = dock
        if floating:
            dock.setFloating(True)
        else:
            self.host.addDockWidget(AREAS[area], dock)
        widget.show(); dock.show()
        self.configure_dock(dock)
        if key == 'log':
            dock.visibilityChanged.connect(lambda *_: self.view.sync_runtime_log_visibility())
            self.view.sync_runtime_log_visibility()
        return dock

    def ensure_dock(self, key):
        if key in self.docks: return self.docks[key]
        if key not in self.pages or key in FIXED_PANELS: return None
        page = self.pages[key]
        placeholder = DockPlaceholder(self.titles[key], lambda: self.return_center(key), compact=key == 'log')
        self.placeholders[key] = placeholder
        if key == 'log':
            self.view.table_splitter.insertWidget(1, placeholder)
        else:
            tabs = self.view.tabs
            index, current = tabs.indexOf(page), tabs.currentIndex()
            QSignalBlocker = _module_imports.load('QSignalBlocker')
            with QSignalBlocker(tabs):
                tabs.removeTab(index); tabs.insertTab(index, placeholder, self.titles[key]); tabs.setCurrentIndex(current)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMinimumSize(90, 60); scroll.setWidget(page)
        return self.create_dock(key, self.titles[key], scroll, 'right')

    def move_palette_side(self, area):
        """Keep the palette beside existing side panels instead of stacking it."""
        palette = self.docks['palette']
        candidates = [(key, dock) for key, dock in self.docks.items()
                      if key != 'palette' and not dock.isFloating()
                      and self.host.dockWidgetArea(dock) == AREAS[area]]
        target = max(candidates, key=lambda item: item[1].height())[0] if candidates else None
        width = palette.width()
        if self.move_panel('palette', area, target=target, arrangement='horizontal'):
            self.host.resizeDocks([palette], [width], Qt.Horizontal)

    def move_panel(self, key, area, target=None, arrangement='vertical'):
        if key == 'table' or self.suspended: return False
        if area == 'center':
            return self.return_center(key)
        if area not in AREAS: return False
        dock = self.ensure_dock(key)
        if dock is None: return False
        self._set_floating(dock, False)
        self.host.addDockWidget(AREAS[area], dock)
        other = self.docks.get(target)
        if other is not None and other is not dock:
            if arrangement == 'tabs': self.host.tabifyDockWidget(other, dock)
            else: self.host.splitDockWidget(other, dock, Qt.Horizontal if arrangement == 'horizontal' else Qt.Vertical)
        dock.show(); dock.widget().show(); dock.raise_()
        self.schedule_save()
        return True

    def return_center(self, key):
        if key not in self.placeholders: return False
        dock = self.docks.pop(key)
        page, placeholder = self.pages[key], self.placeholders.pop(key)
        dock.widget().takeWidget()
        if key == 'log':
            page.setParent(self.view.table_splitter)
            self.view.table_splitter.insertWidget(1, page)
        else:
            tabs = self.view.tabs
            index = tabs.indexOf(placeholder)
            QSignalBlocker = _module_imports.load('QSignalBlocker')
            with QSignalBlocker(tabs):
                tabs.removeTab(index); tabs.insertTab(index, page, self.titles[key]); tabs.setCurrentIndex(index)
        placeholder.setParent(None); placeholder.deleteLater()
        self.host.removeDockWidget(dock); dock.setObjectName('retired_' + key); dock.hide(); dock.deleteLater()
        page.show()
        if key == 'log':
            self.view.sync_runtime_log_visibility()
        self.schedule_save()
        return True

    def panel_menu(self, key, point):
        menu = QMenu(self.window)
        menu._arrangement_submenus = []
        style_context_menu = _module_imports.load('style_context_menu')
        style_context_menu(menu, self.window)
        if key in self.pages and key not in FIXED_PANELS and key not in self.docks:
            menu.addAction('弹出对话Ai编程（含设置与流程草稿）' if key == 'agent' else '弹出为独立窗口',
                           lambda: self.float_panel(key, True))
            menu.addSeparator()
        for area in ('top','bottom','left','right'):
            menu.addAction('移到'+LABELS[area], lambda checked=False,a=area: self.move_panel(key,a))
        if key in self.docks:
            dock = self.docks[key]
            menu.addAction('融入主窗体' if dock.isFloating() else '窗口化',
                           lambda checked=False, target=dock: self.float_panel(key, not target.isFloating()))
            menu.addAction('取消并收起' if key.startswith('parameters_') else '收起面板', dock.close)
        if key in self.placeholders: menu.addAction('返回中栏', lambda: self.return_center(key))
        available = [(k,d) for k,d in self.docks.items() if k != key and not d.isHidden() and not d.isFloating()]
        if available:
            menu.addSeparator()
            for text, arrangement in [('横向并排','horizontal'),('纵向堆叠','vertical'),('合为标签','tabs')]:
                sub = QMenu(text, menu)
                style_context_menu(sub, self.window)
                menu._arrangement_submenus.append(sub)
                menu.addMenu(sub)
                for other, dock in available:
                    area = next((k for k,v in AREAS.items() if v == self.host.dockWidgetArea(dock)), 'right')
                    sub.addAction(dock.windowTitle(), lambda checked=False,a=area,k=other,r=arrangement:self.move_panel(key,a,k,r))
        menu.exec(point); menu.deleteLater()

    def reset_parameter_sizes(self):
        self.view.interface_scale.change(None)
        for key, editor in self.parameters.items():
            dock = self.docks.get(key)
            if dock is None: continue
            size = editor._original_popup_size
            dock.resize(size.width(), size.height()+40)
            scaler = editor._panel_scaler
            if hasattr(scaler, 'expanded_pixels'): del scaler.expanded_pixels
            def finish(scaler=scaler):
                scaler.reference_width = max(1, scaler.viewport.width())
                scaler.reference_height = max(1, scaler.viewport.height())
                scaler.last_size = None
                scaler.apply()
            QTimer.singleShot(0, finish)

    def reset_layout(self):
        if self.view.compact.active: self.view.compact.set_active(False)
        self.save_timer.stop()
        self.restoring = True
        current = list(self.view._remembered_pages()).index('table')
        try:
            for key in list(self.placeholders): self.return_center(key)
            # Preserve unfinished edits without letting them affect the default columns.
            for key in list(self.parameters): self.float_panel(key, True)
            for key,area in (('palette','left'),('controls','right')):
                dock=self.docks[key]
                self.host.removeDockWidget(dock)
                self._set_floating(dock, False)
                self.host.addDockWidget(AREAS[area],dock)
            self.view.palette_side='left'
            self.view.palette_collapsed = self.tab_key(current) not in ('table', 'flow')
            self.view.controls_action.setChecked(True)
            self.view.set_controls_visible(True)
            self.host.resizeDocks([self.docks['palette'],self.docks['controls']],[190,245],Qt.Horizontal)
            self.view.table_splitter.setSizes([680,320])
            self.window.toolBar.hide()
            self.window.actiong.setChecked(False)
            self.window.db.set_setting_value('显示工具栏', 'False')
            self.view.tabs.setCurrentIndex(current)
            self.sync_visibility()
            self.view._update_view_actions()
        finally:
            self.restoring=False
        self.reset_parameter_sizes()
        self.save()
        self.window.statusBar.showMessage('已恢复默认视图；快捷指令顺序保持不变。',4000)

    def show_targets(self, dragged=None):
        if not self.editable: return
        self.dragged_panel = dragged
        self.update_targets(QCursor.pos() if dragged else self.view.tabs.mapToGlobal(self.view.tabs.rect().center()))
        if dragged: self.target_timer.start()

    def update_targets(self, global_point):
        if not self.editable: return
        point = self.host.mapFromGlobal(global_point)
        selected = None
        rect = None
        for key, dock in self.docks.items():
            if key == self.dragged_panel or not dock.isVisible() or dock.isFloating(): continue
            candidate = QRect(dock.mapTo(self.host, QPoint(0, 0)), dock.size())
            if candidate.contains(point):
                selected, rect = key, candidate
                break
        if rect is None:
            central = self.view.tabs
            candidate = QRect(central.mapTo(self.host, QPoint(0, 0)), central.size())
            if candidate.contains(point): rect = candidate
        self.target_panel = selected
        if rect is None:
            for target in self.targets: target.hide()
            return
        self.target_rect = rect
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        third_h, third_w = h // 3, w // 3
        rects = {'top': (x, y, w, third_h),
                 'bottom': (x, y + h - third_h, w, third_h),
                 'left': (x, y + third_h, third_w, h - 2 * third_h),
                 'right': (x + w - third_w, y + third_h, third_w, h - 2 * third_h),
                 'center': (x + third_w, y + third_h, w - 2 * third_w, h - 2 * third_h)}
        for target in self.targets:
            target.setGeometry(*rects[target.key])
            target.setText(('合为标签' if selected else '返回中栏') if target.key == 'center' else LABELS[target.key])
            target.show(); target.raise_()

    def drop_on_target(self, key, direction):
        if not self.editable or key in FIXED_PANELS or key == self.target_panel: return False
        other = self.docks.get(self.target_panel)
        if other is None:
            return self.move_panel(key, direction)
        area = next((name for name, value in AREAS.items() if value == self.host.dockWidgetArea(other)), None)
        if area is None: return False
        orientation = Qt.Horizontal if direction in ('left', 'right') else Qt.Vertical
        arrangement = 'tabs' if direction == 'center' else ('horizontal' if orientation == Qt.Horizontal else 'vertical')
        if not self.move_panel(key, area, self.target_panel, arrangement): return False
        dock = self.docks[key]
        if direction in ('left', 'top'):
            self.host.splitDockWidget(dock, other, orientation)
        if direction != 'center':
            extent = self.target_rect.width() if orientation == Qt.Horizontal else self.target_rect.height()
            self.host.resizeDocks([dock, other], [max(1, extent // 2)] * 2, orientation)
        return True

    def hide_targets(self):
        self.target_timer.stop()
        self.dragged_panel = None
        self.target_panel = None
        for target in self.targets: target.hide()

    def sync_visibility(self):
        if self.suspended: return
        view = self.view
        palette_visible = not view.palette_collapsed and self.tab_key(view.tabs.currentIndex()) != 'code'
        palette = self.docks['palette']
        was_visible = not palette.isHidden()
        if was_visible and not palette_visible and palette.isVisible():
            self._palette_before_hide = (QSize(palette.size()), self.host.dockWidgetArea(palette), palette.isFloating())
            if not palette.isFloating() and self.host.dockWidgetArea(palette) in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
                view._panel_sizes['palette'] = palette.width()
                self.window.db.set_setting_value('工作区面板宽度', json.dumps(view._panel_sizes))
        palette.setVisible(palette_visible)
        self.window.instructionPaletteHost.setVisible(palette_visible)
        saved = getattr(self, '_palette_before_hide', None)
        if palette_visible and not was_visible and not self.restoring and saved:
            size, area, floating = saved
            if floating and palette.isFloating():
                palette.resize(size)
            elif not palette.isFloating() and self.host.dockWidgetArea(palette) == area:
                self.host.resizeDocks([palette], [size.width()], Qt.Horizontal)
                self.host.resizeDocks([palette], [size.height()], Qt.Vertical)
        elif palette_visible and not was_visible and not self.restoring and not palette.isFloating():
            if self.host.dockWidgetArea(palette) in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
                self.host.resizeDocks([palette], [view._panel_sizes['palette']], Qt.Horizontal)
        self.docks['controls'].setVisible(not view.controls_collapsed)
        view.controls_scroll.setVisible(not view.controls_collapsed)
        key = self.tab_key(view.tabs.currentIndex())
        if key in self.placeholders:
            self.docks[key].show(); self.docks[key].raise_()

    def schedule_save(self):
        if not self.restoring and not self.suspended: self.save_timer.start()

    def save(self):
        if self.restoring or self.suspended: return
        state = base64.b64encode(bytes(self.host.saveState(1))).decode('ascii')
        options = {key: {'pinned': dock.pinned, 'follow': dock.follow_main} for key, dock in self.docks.items() if not key.startswith('parameters_')}
        self.window.db.set_setting_value('五栏停靠布局', json.dumps({'version':1,'pages':list(self.placeholders),'state':state,'floating_options':options}))

    def restore(self):
        try:
            record = json.loads(self.window.db.get_setting_value('五栏停靠布局') or '{}')
            if not isinstance(record, dict) or record.get('version') != 1: return
            if not isinstance(record.get('pages', []), list): return
            for key in record.get('pages', []):
                if key in self.pages and key != 'table': self.ensure_dock(key)
            self.host.restoreState(QByteArray(base64.b64decode(record['state'],validate=True)),1)
            for key, options in record.get('floating_options', {}).items():
                if key in self.docks and isinstance(options, dict):
                    self.docks[key].set_follow_main(bool(options.get('follow', False)))
                    self.docks[key].set_pinned(bool(options.get('pinned', False)))
        except (ValueError, TypeError, KeyError): pass

    def pin_editor(self, editor, callback, key, *, floating=False):
        if key in self.parameters:
            self.docks[key].show(); self.docks[key].raise_(); return
        reused = next(((old_key, self.docks[old_key]) for old_key in self.parameters
                       if old_key in self.docks and not self.docks[old_key].isFloating()), None)
        if reused is not None:
            floating = False
        style_settings_combos = _module_imports.load('style_settings_combos')
        editor.setProperty('uniformSettingsFont', True)
        if str(getattr(editor, 'TYPE_ID', '')).startswith('窗口'):
            from anclicker.ui.settings_theme import fit_window_settings
            fit_window_settings(editor)
        from anclicker.ui.settings_theme import apply_settings_theme
        apply_settings_theme(editor, self.window)
        style_settings_combos(editor, self.window)
        editor.ensurePolished()
        parameter_popup_size = _module_imports.load('parameter_popup_size')
        editor._original_popup_size = parameter_popup_size(editor)
        self.parameters[key] = editor
        editor._workspace_owner = self.window
        if not hasattr(editor, '_pin_filter'): editor._pin_filter = ParameterPinFilter(editor)
        editor._pin_filter.manager, editor._pin_filter.key = self, key
        editor.setParent(None)
        editor.setWindowFlags(Qt.Widget)
        editor.setModal(False)
        editor.setMinimumSize(0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(editor)
        # Both scroll viewports must follow the theme, including exposed margins.
        for area in [scroll] + editor.findChildren(QScrollArea):
            area.setObjectName('parameterScroll')
            area.viewport().setObjectName('parameterViewport')
        AdaptivePanelSizer = _module_imports.load('AdaptivePanelSizer')
        if hasattr(editor, '_panel_scaler'): editor._panel_scaler.rebind(scroll.viewport())
        else: editor._panel_scaler = AdaptivePanelSizer(scroll.viewport(), editor, 600, reference_height=420, base_pixels=13)
        editor._panel_scaler.base_pixels = 14
        editor._panel_scaler.base_style = editor.styleSheet()
        editor._panel_scaler.reference_width = max(260, editor._original_popup_size.width())
        editor._panel_scaler.reference_height = min(420, max(160, editor._original_popup_size.height()-56))
        if reused is not None:
            old_key, dock = reused
            old_editor = self.parameters.pop(old_key)
            self.docks.pop(old_key)
            old_scroll = dock.widget()
            old_scroll.takeWidget()
            old_editor.reject()
            old_editor.deleteLater()
            dock.key = key
            dock.setObjectName('panelDock_' + key)
            dock.setWindowTitle('指令参数 · ' + editor.windowTitle())
            dock._title_drag_filter.key = key
            dock.setWidget(scroll)
            self.docks[key] = dock
            old_scroll.deleteLater()
        else:
            dock = self.create_dock(key, '指令参数 · '+editor.windowTitle(), scroll, 'right', floating=floating)
        title = editor.findChild(QLabel, 'titleLabel') or editor.findChild(QLabel)
        if title is not None:
            editor._drag_filter = PanelDragFilter(self, title, key)
        if not floating and reused is None:
            controls = self.docks['controls']
            self.host.splitDockWidget(dock, controls, Qt.Horizontal)
            self.host.resizeDocks([dock,controls], [360,300], Qt.Horizontal)
        def finished(result):
            if self.parameters.get(key) is not editor: return
            if result == QDialog.Accepted:
                try: callback(editor.get_draft())
                except Exception as error:
                    QMessageBox = _module_imports.load('QMessageBox')
                    QMessageBox.warning(self.window,'保存指令失败',str(error));editor.show();return
            self.parameters.pop(key, None);self.docks.pop(key,None)
            self.host.removeDockWidget(dock);dock.hide();dock.deleteLater()
            self.schedule_save()
        editor.finished.connect(finished)
        editor.show();dock.show()
        if floating:
            self.float_panel(key, True)
            fit_initial_popup = _module_imports.load('fit_initial_popup')
            QTimer.singleShot(0, lambda: fit_initial_popup(editor, dock) if key in self.parameters else None)

    def update_controls_layout(self):
        dock = self.docks['controls']
        horizontal = not self.suspended and not dock.isFloating() and self.host.dockWidgetArea(dock) in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea)
        if horizontal == self.controls_horizontal:
            self.refresh_control_actions_style()
            return
        self.controls_horizontal = horizontal
        w = self.window
        grid = w.gridLayout_2
        if horizontal:
            self._control_stretches = [grid.rowStretch(i) for i in range(8)]
            self._control_columns = [grid.columnStretch(i) for i in range(3)]
            self._control_spacer = grid.takeAt(grid.indexOf(w.verticalSpacer_4))
            self.control_actions = QWidget()
            layout = QVBoxLayout(self.control_actions)
            layout.setContentsMargins(12, 4, 4, 4); layout.setSpacing(6)
            for button in (w.pushButton_5,w.pushButton_7,w.pushButton_6):
                layout.addWidget(button)
            grid.addWidget(self.control_actions,0,2,4,1)
            grid.setColumnStretch(0,0)
            grid.setColumnStretch(1,2)
            grid.setColumnStretch(2,1)
            for i in range(8): grid.setRowStretch(i,0)
            self.control_actions.show()
        else:
            for row,button in enumerate((w.pushButton_5,w.pushButton_7,w.pushButton_6),5):
                grid.addWidget(button,row,0,1,2); button.show()
            grid.removeWidget(self.control_actions)
            self.control_actions.hide();self.control_actions.deleteLater()
            if self._control_spacer is not None: grid.addItem(self._control_spacer,4,0,1,2)
            for i,stretch in enumerate(self._control_columns): grid.setColumnStretch(i,stretch)
            for i,stretch in enumerate(self._control_stretches): grid.setRowStretch(i,stretch)
        w.groupBox_3.setProperty('horizontalControls', horizontal)
        self.refresh_control_actions_style()
        if hasattr(self,'scalers'):
            self.scalers[1].last_size = None
            self.scalers[1].timer.start()

    def refresh_control_actions_style(self):
        if not self.controls_horizontal or not hasattr(self, 'control_actions'):
            return
        actions = self.control_actions
        presets = getattr(self.view, 'layout_presets', None)
        compact = getattr(presets, 'selected', None) == 'dynamic1'
        layout = actions.layout()
        if compact:
            buttons = (self.window.pushButton_5, self.window.pushButton_7, self.window.pushButton_6)
            preferred = max(190, max(button.sizeHint().width() for button in buttons) + 32)
            actions.setMaximumWidth(preferred)
            actions.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            layout.setContentsMargins(8, 4, 4, 4)
            layout.setSpacing(8)
            layout.setAlignment(Qt.AlignTop)
            self.window.gridLayout_2.setAlignment(actions, Qt.AlignTop | Qt.AlignRight)
        else:
            actions.setMaximumWidth(16777215)
            actions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            layout.setContentsMargins(12, 4, 4, 4)
            layout.setSpacing(6)
            layout.setAlignment(Qt.Alignment())
            self.window.gridLayout_2.setAlignment(actions, Qt.Alignment())

    def float_parameters(self, key, floating):
        self.float_panel(key, floating)

    def float_panel(self, key, floating):
        dock = self.ensure_dock(key)
        if dock is None: return
        self._set_floating(dock, floating)
        if floating and key == 'agent':
            available=self.window.screen().availableGeometry()
            dock.resize(QSize(1100,760).boundedTo(available.size()-QSize(40,60)))
            frame=dock.frameGeometry();frame.moveCenter(available.center());dock.move(frame.topLeft())
        if floating and key.startswith('parameters_'):
            editor = self.parameters[key]
            size = editor._original_popup_size
            screen = self.window.screen()
            available = screen.availableGeometry()
            dock.resize(size.boundedTo(available.size() - QSize(40, 60)))
            center = self.window.frameGeometry().center()
            frame = dock.frameGeometry()
            frame.moveCenter(center)
            frame.moveLeft(max(available.left(), min(frame.left(), available.right()-frame.width()+1)))
            frame.moveTop(max(available.top(), min(frame.top(), available.bottom()-frame.height()+1)))
            dock.move(frame.topLeft())
        if floating and dock.pinned:
            dock.set_pinned(True)
        dock.show(); dock.raise_()
        self.schedule_save()

    def suspend(self):
        self.save()
        self.suspended = True
        self.update_controls_layout()
        self._compact_state = self.host.saveState(1)
        self._compact_hidden = {key:dock.isHidden() for key,dock in self.docks.items()}
        self._log_detached = 'log' in self.placeholders
        if self._log_detached:
            self.docks['log'].widget().takeWidget()
            self.pages['log'].setParent(self.view.table_splitter)
            self.view.table_splitter.insertWidget(1,self.pages['log'])
        for key,dock in self.docks.items():
            dock.setVisible(key == 'controls')
        controls=self.docks['controls'];self._set_floating(controls, False)
        self.host.addDockWidget(Qt.RightDockWidgetArea,controls)

    def resume(self):
        if self._log_detached: self.docks['log'].widget().setWidget(self.pages['log'])
        self.host.restoreState(self._compact_state,1)
        for key,hidden in self._compact_hidden.items():
            if key in self.docks:self.docks[key].setVisible(not hidden)
        self.suspended=False
        self.update_controls_layout()
        self.sync_visibility()

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QEvent.Move:
            position = self.window.pos()
            delta = position - self._main_position
            self._main_position = position
            if not self.restoring and not self.suspended and not delta.isNull():
                for dock in list(self.docks.values()):
                    if dock.isFloating() and dock.follow_main and dock.isVisible():
                        dock.move(dock.pos() + delta)
                self.schedule_save()
        if event.type() in (QEvent.Resize,QEvent.LayoutRequest):
            self.schedule_save()
            for key in ('palette', 'controls'):
                dock = self.docks.get(key)
                if dock is not None:
                    title = dock.titleBarWidget()
                    height = title.sizeHint().height()
                    if getattr(title, '_alignment_height', None) != height:
                        title._alignment_height = height
                        title.updateGeometry()
        return False
