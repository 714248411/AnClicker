"""Small, resizable execution console using the original controls and log."""
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLayout


class CompactWorkspace(QObject):
    def __init__(self, workspace):
        super().__init__(workspace.window)
        self.workspace = workspace
        self.window = workspace.window
        self.active = False
        self.window.installEventFilter(self)
        workspace.title_bar.compact_button.toggled.connect(self.set_active)

    def set_active(self, enabled):
        if self.active == enabled:
            return
        w, view = self.window, self.workspace
        self.active = enabled
        button = view.title_bar.compact_button
        button.setChecked(enabled)
        button.setToolTip('还原完整界面' if enabled else '小化：仅显示控制与操作')
        button.setAccessibleName(button.toolTip())
        if enabled:
            self.geometry = w.saveGeometry()
            self.normal_rect = w.geometry()
            self.was_maximized = w.isMaximized()
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
            w.resize(340, 460)
            self.scale_controls()
            self.splitter.setSizes([180, 100])
        else:
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
            w.setMinimumSize(self.minimum)
            w.restoreGeometry(self.geometry)
            if not self.was_maximized:
                w.setGeometry(self.normal_rect)
            view.title_bar.setFixedHeight(44)
            for item in (view.title_bar.compact_button, view.title_bar.theme_button,
                         view.title_bar.minimize_button, view.title_bar.maximize_button, view.title_bar.close_button):
                item.setFixedSize(32, 32)
            view.title_bar.title.setStyleSheet('')

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
        bar.title.setStyleSheet(f'font-size: {size}px;')
        for item in (bar.compact_button, bar.theme_button, bar.minimize_button, bar.maximize_button, bar.close_button):
            item.setFixedSize(24 if w.width() < 400 else 30, 24 if w.width() < 400 else 30)

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QEvent.Type.Resize and self.active:
            self.scale_controls()
        elif watched is self.window and event.type() == QEvent.Type.Close and self.active:
            # Persist normal geometry and the user's current hide preference.
            self.set_active(False)
        return False
