"""Small, resizable execution console using the original controls and log."""
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt, QTimer, QRect
from anclicker.platform.qt_compat.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLayout

from anclicker.ui.compact_position import place_compact_window, save_compact_position, resize_compact_window, save_compact_size


class CompactWorkspace(QObject):
    def __init__(self, workspace):
        super().__init__(workspace.window)
        self.workspace = workspace
        self.window = workspace.window
        self.active = False
        self._position_ready=False
        self.position_timer=QTimer(self);self.position_timer.setSingleShot(True)
        self.position_timer.setInterval(300);self.position_timer.timeout.connect(self._save_position)
        self.window.installEventFilter(self)
        workspace.title_bar.compact_button.toggled.connect(self.set_active)

    def set_active(self, enabled):
        if self.active == enabled:
            return
        w, view = self.window, self.workspace
        if not enabled:
            self.position_timer.stop()
            self._save_position()
        self._position_ready=False
        self.active = enabled
        button = view.title_bar.compact_button
        button.setChecked(enabled)
        button.setToolTip('还原完整界面' if enabled else '小化：仅显示控制与操作')
        button.setAccessibleName(button.toolTip())
        if enabled:
            self.geometry = w.saveGeometry()
            self.normal_rect = QRect(getattr(w, '_restore_client_geometry', w.normalGeometry()) if w.isMaximized() else w.geometry())
            self.was_maximized = w.isMaximized()
            if hasattr(view, 'docking'): view.docking.suspend()
            self.workspace_sizes = view.workspace_splitter.sizes() if hasattr(view,'workspace_splitter') else None
            self.controls_hidden = getattr(view, 'controls_scroll', w.groupBox_3).isHidden()
            if hasattr(view, 'controls_scroll'):
                self.controls_minimum = view.controls_scroll.minimumSize()
                view.controls_scroll.setMinimumWidth(0)
                view.controls_scroll.show()
            self.compact_margins=w.gridLayout_4.contentsMargins()
            w.gridLayout_4.setContentsMargins(self.compact_margins.left(),3,self.compact_margins.right(),self.compact_margins.bottom())
            self.dock_title=None
            if hasattr(view,'docking'):
                self.dock_title=view.docking.docks['controls'].titleBarWidget()
                self.dock_title_limits=(self.dock_title.minimumHeight(),self.dock_title.maximumHeight())
                self.dock_title.setFixedHeight(0)
            self.minimum = w.minimumSize()
            self.control_style = w.groupBox_3.styleSheet()
            # Compact mode shares the same execution settings. Do not disable
            # hide-on-run or later overwrite changes made in the small console.
            self.hidden = [(item, item.isHidden()) for item in
                           (view.tabs, w.instructionPaletteHost, w.toolBar, w.menubar, w.statusBar)]
            for item, _ in self.hidden:
                item.hide()
            self.log = view.table_splitter.widget(1)
            self.table_sizes = view.table_splitter.sizes()
            self.saved_minimums = [(item, item.minimumSize()) for item in
                                   [w.groupBox_3, self.log] + w.groupBox_3.findChildren(QWidget) + self.log.findChildren(QWidget)]
            for item, _ in self.saved_minimums:
                item.setMinimumSize(0, 0)
            self.spacer = w.gridLayout_2.takeAt(w.gridLayout_2.indexOf(w.verticalSpacer_4))
            self.row_stretches = [w.gridLayout_2.rowStretch(i) for i in range(8)]
            for i in range(8):
                w.gridLayout_2.setRowStretch(i, 0)
            self.actions = QWidget()
            action_layout = QVBoxLayout(self.actions)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(3)
            self.actions.setMinimumHeight(72)
            for item in (w.pushButton_5, w.pushButton_7, w.pushButton_6):
                action_layout.addWidget(item)
            self.splitter = QSplitter(Qt.Orientation.Vertical)
            self.splitter.setChildrenCollapsible(False)
            self.splitter.addWidget(self.log)
            self.splitter.addWidget(self.actions)
            w.gridLayout_2.addWidget(self.splitter, 4, 0, 1, 2)
            w.gridLayout_2.setRowStretch(4, 1)
            self.columns = [w.gridLayout_4.columnStretch(i) for i in range(3)]
            for i in range(3):
                w.gridLayout_4.setColumnStretch(i, int(i == 2))
            self.constraint = w.layout().sizeConstraint()
            w.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
            w.setMinimumSize(280, 350)
            w.showNormal()
            resize_compact_window(w)
            self.scale_controls()
            self.splitter.setSizes([180, 100])
            place_compact_window(w)
            self._position_ready=True
            self._save_position()
        else:
            w.gridLayout_4.setContentsMargins(self.compact_margins)
            if self.dock_title is not None:
                self.dock_title.setMinimumHeight(self.dock_title_limits[0]);self.dock_title.setMaximumHeight(self.dock_title_limits[1])
            view.table_splitter.addWidget(self.log)
            self.log.show()
            view.table_splitter.setSizes(self.table_sizes)
            for row, item in enumerate((w.pushButton_5, w.pushButton_7, w.pushButton_6), 5):
                w.gridLayout_2.addWidget(item, row, 0, 1, 2)
                item.show()
            w.gridLayout_2.removeWidget(self.splitter)
            self.splitter.hide(); self.splitter.deleteLater()
            w.gridLayout_2.addItem(self.spacer, 4, 0, 1, 2)
            for i, stretch in enumerate(self.row_stretches):
                w.gridLayout_2.setRowStretch(i, stretch)
            for i, stretch in enumerate(self.columns):
                w.gridLayout_4.setColumnStretch(i, stretch)
            for item, minimum in self.saved_minimums:
                item.setMinimumSize(minimum)
            w.groupBox_3.setStyleSheet(self.control_style)
            for item, hidden in self.hidden:
                item.setVisible(not hidden)
            w.layout().setSizeConstraint(self.constraint)
            if hasattr(view, 'controls_scroll'):
                view.controls_scroll.setMinimumSize(self.controls_minimum)
                view.controls_scroll.setVisible(not getattr(view, 'controls_collapsed', self.controls_hidden))
            w.setMinimumSize(self.minimum)
            # Small-window maximize/restore must not replace the main
            # window's client restore rectangle.
            w._restore_client_geometry=QRect(self.normal_rect)
            w.showNormal()
            w.setGeometry(self.normal_rect)
            if self.was_maximized:w.showMaximized()
            if self.workspace_sizes is not None: view.workspace_splitter.setSizes(self.workspace_sizes)
            view.title_bar.setFixedHeight(34)
            view.title_bar.hBoxLayout.setSpacing(2)
            view.title_bar.updateButton.setFixedHeight(28)
            w.setContentsMargins(0, view.title_bar.height(), 0, 0)
            for item in (view.title_bar.compact_button, view.title_bar.schedule_button, view.title_bar.theme_button,
                         view.title_bar.minBtn, view.title_bar.maxBtn, view.title_bar.closeBtn):
                item.setFixedSize(28, 28)
            if hasattr(view, 'docking'): view.docking.resume()
            view.title_bar.apply_theme(view.theme_mode, view.THEMES[view.theme_mode])

    def scale_controls(self):
        if not self.active:
            return
        w = self.window
        size = max(9, min(14, round(min(w.width()/340, w.height()/460) * 12)))
        padding = max(1, size // 4)
        w.groupBox_3.setStyleSheet(f'''
            QGroupBox#groupBox_3, QGroupBox#groupBox_3 * {{ font-size: {size}px; }}
            QGroupBox#groupBox_3 QPushButton, QGroupBox#groupBox_3 QToolButton {{ padding: {padding}px 4px; min-height: 0px; }}
            QGroupBox#groupBox_3 QSpinBox {{ padding: 2px 16px 2px 4px; min-height: 0px; }}
            QGroupBox#groupBox_3 QRadioButton, QGroupBox#groupBox_3 QCheckBox {{ spacing: 3px; }}
            QGroupBox#groupBox_3 QRadioButton::indicator, QGroupBox#groupBox_3 QCheckBox::indicator {{ width: {size}px; height: {size}px; }}
        ''')
        bar = self.workspace.title_bar
        bar.setFixedHeight(34 if w.width() < 400 else 40)
        bar.hBoxLayout.setSpacing(2 if w.width() < 400 else 4)
        bar.updateButton.setFixedHeight(24 if w.width() < 400 else 32)
        w.setContentsMargins(0, bar.height(), 0, 0)
        bar.titleLabel.setStyleSheet(f'font-size: {size}px;')
        for item in (bar.compact_button, bar.schedule_button, bar.theme_button, bar.minBtn, bar.maxBtn, bar.closeBtn):
            item.setFixedSize(24 if w.width() < 400 else 30, 24 if w.width() < 400 else 30)

    def _save_position(self):
        if self.active and self._position_ready:
            save_compact_position(self.window)
            save_compact_size(self.window)

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QEvent.Type.Move and self.active and self._position_ready:
            self.position_timer.start()
        if watched is self.window and event.type() == QEvent.Type.Resize and self.active:
            self.scale_controls()
            if self._position_ready:self.position_timer.start()
        elif watched is self.window and event.type() == QEvent.Type.Close and self.active:
            # Persist normal geometry and the user's current hide preference.
            self.set_active(False)
        return False
