"""Movable workspace panels; the command table remains in the central tabs."""
import base64
import json

from qt_compat.QtCore import QObject, QEvent, Qt, QMimeData, QTimer, QByteArray, QSize, QPoint, QRect
from qt_compat.QtGui import QDrag, QCursor
from qt_compat.QtWidgets import (QApplication, QDockWidget, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QScrollArea, QFrame, QDialog)

FIXED_PANELS = {'table', 'flow'}
PANEL_MIME = 'application/x-anclicker-panel'
PIN_RESULT = 731
AREAS = {'left': Qt.LeftDockWidgetArea, 'right': Qt.RightDockWidgetArea,
         'top': Qt.TopDockWidgetArea, 'bottom': Qt.BottomDockWidgetArea}
LABELS = {'top':'上栏', 'center':'中栏', 'bottom':'下栏', 'left':'左栏', 'right':'右栏'}


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


class PanelTitle(QLabel):
    def __init__(self, dock):
        super().__init__('', dock)
        self.setAccessibleName(dock.windowTitle() + '拖拽条')
        self.setFixedHeight(0 if dock.key in ('palette','controls','log') or dock.key.startswith('parameters_') else 12)
        self.dock = dock
        if dock.key.startswith('parameters_'):
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 0, 3, 0)
            layout.addStretch()
            self.close_button = QPushButton('×', self)
            self.close_button.setFixedSize(24, 24)
            self.close_button.setToolTip('关闭并取消未保存修改')
            self.close_button.clicked.connect(dock.close)
            layout.addWidget(self.close_button)
            self.close_button.hide()
        self.setObjectName('dockPanelTitle')
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(30)
        self.setToolTip(dock.windowTitle() + '：拖动拉出；双击窗口化/嵌入；右击打开面板菜单')

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dock.manager.editable or not self.dock.isFloating():
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
        self.setObjectName('panelDock_' + key)
        self.setProperty('instructionParameter', key.startswith('parameters_'))
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self._embedded_title = PanelTitle(self)
        self.setTitleBarWidget(self._embedded_title)
        self._title_drag_filter = PanelDragFilter(manager, self._embedded_title, key)
        if key.startswith('parameters_'):
            self.topLevelChanged.connect(self._parameter_window_chrome)
        self.setMinimumSize(0, 0)
        self.setToolTip('拖动标题停靠到上、下、左、右栏；右击标题可选择并排、堆叠或返回中栏')
        self.dockLocationChanged.connect(lambda *_: manager.schedule_save())
        self.topLevelChanged.connect(lambda *_: manager.schedule_save())
        self.topLevelChanged.connect(lambda *_: manager.configure_dock(self))

    def _parameter_window_chrome(self, floating):
        features = QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        if floating: features |= QDockWidget.DockWidgetClosable
        title = self._embedded_title
        title.setFixedHeight(28 if floating else 0)
        title.setText(self.windowTitle() if floating else '')
        title.close_button.setVisible(floating)
        self.setFeatures(features)
        self.manager.configure_dock(self)

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
        widget.setToolTip('拖到上、下、左、右栏；右击选择停靠位置。表格与流程图固定在中栏。')

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton and self.key:
            on_title = not self.header_only or (event.pos().y() <= 28 and event.pos().x() <= watched.fontMetrics().horizontalAdvance(watched.title()) + 30)
            if on_title:
                dock = self.manager.ensure_dock(self.key)
                if dock is not None and (self.manager.editable or not dock.isFloating()):
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
            from context_menu_style import style_context_menu
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
        self.editable = self.window.db.get_setting_value('可编辑视图') != 'False'
        self.host = QMainWindow()
        self.host.setObjectName('dockWorkspace')
        self.host.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AnimatedDocks)
        self.host.setDockNestingEnabled(True)
        self.host.setMinimumSize(0, 0)
        self.pages = dict(view._remembered_pages())
        self.pages['log'] = view.table_splitter.widget(1)
        self.titles = dict(zip(self.pages, ['主界面','表格','流程图','多功能','录制','网页录制','运行日志']))
        grid = self.window.gridLayout_4
        grid.removeWidget(view.workspace_splitter)
        self.host.setCentralWidget(view.tabs)
        self.create_dock('palette', '快捷指令', self.window.instructionPaletteHost, 'left')
        self.create_dock('controls', '控制与操作', view.controls_scroll, 'right')
        self.docks['controls'].dockLocationChanged.connect(lambda *_: self.update_controls_layout())
        self.docks['controls'].topLevelChanged.connect(lambda *_: self.update_controls_layout())
        view.workspace_splitter.hide()
        grid.addWidget(self.host, 0, 0, 1, 3)
        self.host.resizeDocks([self.docks['palette'],self.docks['controls']], [230,300], Qt.Horizontal)
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
        self.host.installEventFilter(self)
        from adaptive_panels import AdaptivePanelSizer
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
        features = QDockWidget.DockWidgetFloatable
        if self.editable or dock.isFloating(): features |= QDockWidget.DockWidgetMovable
        if dock.key.startswith('parameters_') and dock.isFloating(): features |= QDockWidget.DockWidgetClosable
        dock.setFeatures(features)

    def _set_floating(self, dock, floating):
        # Explicit menu actions remain available while native drag docking is locked.
        dock._programmatic_move = True
        try:
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            if not floating and self.host.dockWidgetArea(dock) == Qt.NoDockWidgetArea:
                self.host.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.setFloating(floating)
        finally:
            dock._programmatic_move = False
            self.configure_dock(dock)

    def set_editable(self, enabled):
        self.editable = bool(enabled)
        self.window.db.set_setting_value('可编辑视图', str(self.editable))
        if not self.editable: self.hide_targets()
        for dock in self.docks.values(): self.configure_dock(dock)

    def tab_key(self, index):
        keys = ['main','table','flow','code','recording','web_recording']
        return keys[index] if 0 <= index < len(keys) else None

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
        return dock

    def ensure_dock(self, key):
        if key in self.docks: return self.docks[key]
        if key not in self.pages or key in FIXED_PANELS: return None
        page = self.pages[key]
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.addWidget(QLabel(self.titles[key] + '已停靠到其他栏目'))
        back = QPushButton('返回中栏'); back.clicked.connect(lambda: self.return_center(key))
        layout.addWidget(back); layout.addStretch()
        self.placeholders[key] = placeholder
        if key == 'log':
            self.view.table_splitter.insertWidget(1, placeholder)
        else:
            tabs = self.view.tabs
            index, current = tabs.indexOf(page), tabs.currentIndex()
            from qt_compat.QtCore import QSignalBlocker
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
            from qt_compat.QtCore import QSignalBlocker
            with QSignalBlocker(tabs):
                tabs.removeTab(index); tabs.insertTab(index, page, self.titles[key]); tabs.setCurrentIndex(index)
        placeholder.setParent(None); placeholder.deleteLater()
        self.host.removeDockWidget(dock); dock.setObjectName('retired_' + key); dock.hide(); dock.deleteLater()
        page.show()
        self.schedule_save()
        return True

    def panel_menu(self, key, point):
        menu = QMenu(self.window)
        from context_menu_style import style_context_menu
        style_context_menu(menu, self.window)
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
                sub = menu.addMenu(text)
                for other, dock in available:
                    area = next((k for k,v in AREAS.items() if v == self.host.dockWidgetArea(dock)), 'right')
                    sub.addAction(dock.windowTitle(), lambda checked=False,a=area,k=other,r=arrangement:self.move_panel(key,a,k,r))
        menu.exec(point); menu.deleteLater()

    def reset_layout(self):
        if self.view.compact.active: self.view.compact.set_active(False)
        self.save_timer.stop()
        self.restoring = True
        current = self.view.tabs.currentIndex()
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
            self.view.palette_collapsed=False
            self.view.controls_action.setChecked(True)
            self.view.set_controls_visible(True)
            self.host.resizeDocks([self.docks['palette'],self.docks['controls']],[230,300],Qt.Horizontal)
            self.view.table_splitter.setSizes([520,260])
            self.view.tabs.setCurrentIndex(current)
            self.sync_visibility()
            self.view._update_view_actions()
        finally:
            self.restoring=False
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
        self.docks['palette'].setVisible(palette_visible)
        self.window.instructionPaletteHost.setVisible(palette_visible)
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
        self.window.db.set_setting_value('五栏停靠布局', json.dumps({'version':1,'pages':list(self.placeholders),'state':state}))

    def restore(self):
        try:
            record = json.loads(self.window.db.get_setting_value('五栏停靠布局') or '{}')
            if not isinstance(record, dict) or record.get('version') != 1: return
            if not isinstance(record.get('pages', []), list): return
            for key in record.get('pages', []):
                if key in self.pages and key != 'table': self.ensure_dock(key)
            self.host.restoreState(QByteArray(base64.b64decode(record['state'],validate=True)),1)
        except (ValueError, TypeError, KeyError): pass

    def pin_editor(self, editor, callback, key, *, floating=False):
        if key in self.parameters:
            self.docks[key].show(); self.docks[key].raise_(); return
        editor.ensurePolished()
        editor._original_popup_size = QSize(editor.size().expandedTo(editor.sizeHint()))
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
        from adaptive_panels import AdaptivePanelSizer
        if hasattr(editor, '_panel_scaler'): editor._panel_scaler.rebind(scroll.viewport())
        else: editor._panel_scaler = AdaptivePanelSizer(scroll.viewport(), editor, 600, reference_height=420, base_pixels=12)
        dock = self.create_dock(key, '指令参数 · '+editor.windowTitle(), scroll, 'right', floating=floating)
        title = editor.findChild(QLabel, 'titleLabel') or editor.findChild(QLabel)
        if title is not None:
            editor._drag_filter = PanelDragFilter(self, title, key)
        if not floating:
            controls = self.docks['controls']
            self.host.splitDockWidget(dock, controls, Qt.Horizontal)
            self.host.resizeDocks([dock,controls], [360,300], Qt.Horizontal)
        def finished(result):
            if key not in self.parameters: return
            if result == QDialog.Accepted:
                try: callback(editor.get_draft())
                except Exception as error:
                    from qt_compat.QtWidgets import QMessageBox
                    QMessageBox.warning(self.window,'保存指令失败',str(error));editor.show();return
            self.parameters.pop(key, None);self.docks.pop(key,None)
            self.host.removeDockWidget(dock);dock.hide();dock.deleteLater()
            self.schedule_save()
        editor.finished.connect(finished)
        editor.show();dock.show()
        if floating: self.float_panel(key, True)

    def update_controls_layout(self):
        dock = self.docks['controls']
        horizontal = not self.suspended and not dock.isFloating() and self.host.dockWidgetArea(dock) in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea)
        if horizontal == self.controls_horizontal: return
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
        if hasattr(self,'scalers'):
            self.scalers[1].last_size = None
            self.scalers[1].timer.start()

    def float_parameters(self, key, floating):
        self.float_panel(key, floating)

    def float_panel(self, key, floating):
        dock = self.ensure_dock(key)
        if dock is None: return
        self._set_floating(dock, floating)
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
        if event.type() in (QEvent.Resize,QEvent.LayoutRequest): self.schedule_save()
        return False
