"""Chinese scheduled-project settings, matching the compact rounded task card."""
from datetime import datetime
from pathlib import Path
from qt_compat.QtCore import Qt, QDateTime, QRectF, QPoint, QSize, Signal, Slot, QTimer, QEvent
from qt_compat.QtGui import QPainter, QColor, QPen, QPalette, QIcon, QPixmap, QPainterPath
from qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QMenu, QFileDialog, QMessageBox,
    QWidget, QFormLayout, QListWidget, QListWidgetItem, QFrame, QSpinBox, QScrollArea, QSizePolicy, QSplitter, QToolButton)


class TaskCardLabel(QLabel):
    """Keep the status and edit corner visible when a task title is long."""
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.WindowText))
        text = self.fontMetrics().elidedText(self.text(), Qt.ElideRight, self.contentsRect().width())
        painter.drawText(self.contentsRect(), Qt.AlignLeft | Qt.AlignVCenter, text)


class ScheduleTaskCard(QWidget):
    editRequested = Signal()

    def __init__(self, title, details, *, enabled, editable, dark, parent=None):
        super().__init__(parent)
        self.setObjectName('scheduleTaskCard')
        self._dark = dark
        foreground = '#eef0f6' if dark else '#202534'
        muted = '#b5bdcc' if dark else '#647084'
        state_color = ('#90d9b0' if dark else '#287247') if enabled else muted
        self.setStyleSheet(f'''
            QWidget#scheduleTaskCard {{background:transparent;border:none;}}
            QLabel {{background:transparent;color:{foreground};font-size:12px;padding:0;}}
            QLabel#taskCardDetails {{color:{muted};font-size:11px;}}
            QLabel#taskCardState {{color:{state_color};font-size:11px;}}
            QToolButton {{background:transparent;color:{foreground};border:none;border-radius:4px;padding:0;font-size:13px;}}
            QToolButton:hover {{background:rgba(125,140,180,40);}}
            QToolButton:disabled {{color:{muted};}}
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 5)
        layout.setSpacing(1)
        top = QHBoxLayout()
        top.setSpacing(4)
        self.title_label = TaskCardLabel(title, self)
        self.edit_button = QToolButton(self)
        self.edit_button.setText('🖊')
        self.edit_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.edit_button.setIconSize(QSize(16, 16))
        self.edit_button.setFixedSize(20, 20)
        self.edit_button.setAccessibleName(f'编辑任务：{title}')
        self.edit_button.setToolTip('编辑任务' if editable else '任务正在执行，结束后可编辑')
        self.edit_button.setEnabled(editable)
        self.set_editing(False)
        self.edit_button.clicked.connect(self.editRequested.emit)
        top.addWidget(self.edit_button, 0, Qt.AlignLeft)
        top.addWidget(self.title_label, 1)
        layout.addLayout(top)
        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        self.details_label = TaskCardLabel(details, self)
        self.details_label.setObjectName('taskCardDetails')
        self.state_label = QLabel('开启' if enabled else '未开启', self)
        self.state_label.setObjectName('taskCardState')
        self.state_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.state_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        bottom.addWidget(self.details_label, 1)
        bottom.addWidget(self.state_label, 0, Qt.AlignRight)
        layout.addLayout(bottom)

    def set_editing(self, editing):
        editing = bool(editing and self.edit_button.isEnabled())
        self.edit_button.setProperty('editing', editing)
        color = ('#8db7ff' if self._dark else '#275fd4') if editing else ('#b5bdcc' if self._dark else '#647084')
        # Draw a monochrome pen so color works even with native color-emoji fonts.
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(2, 2)
        painter.setPen(QPen(QColor(color), 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QPainterPath()
        path.moveTo(2.5, 13.5)
        for x, y in ((3.5, 9.5), (11, 2), (14, 5), (6.5, 12.5), (2.5, 13.5)):
            path.lineTo(x, y)
        path.moveTo(9, 4)
        path.lineTo(12, 7)
        painter.drawPath(path)
        painter.end()
        self.edit_button.setIcon(QIcon(pixmap))
        self.edit_button.setStyleSheet('QToolButton {background:rgba(82,102,220,45);border-radius:4px;}' if editing else '')
        self.edit_button.setToolTip('正在编辑，点击保存后退出编辑' if editing else
                                   '编辑任务' if self.edit_button.isEnabled() else '任务正在执行，结束后可编辑')
        self.edit_button.setAccessibleDescription('编辑状态' if editing else '非编辑状态')


class ProjectPathEdit(QLineEdit):
    """只接收单个本地项目或目录，不把 URL 文本混入现有路径。"""
    directoryDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText('选择或拖入 .xlsx 项目文件 / 文件夹')
        self.setToolTip('拖入项目文件直接填写路径；拖入文件夹后，从该目录选择项目。')

    @staticmethod
    def dropped_path(mime):
        urls = mime.urls() if mime.hasUrls() else []
        if len(urls) != 1 or not urls[0].isLocalFile():
            return None
        path = Path(urls[0].toLocalFile())
        try:
            if path.is_dir() or (path.suffix.lower() == '.xlsx' and path.is_file()):
                return path
        except OSError:
            pass
        return None

    def dragEnterEvent(self, event):
        if self.dropped_path(event.mimeData()) is not None:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        path = self.dropped_path(event.mimeData())
        if path is None:
            event.ignore()
            return
        event.setDropAction(Qt.CopyAction)
        event.accept()
        if path.is_dir():
            self.directoryDropped.emit(str(path))
        else:
            self.setText(str(path))


class RepeatSelector(QPushButton):
    """Use the rounded menu surface, avoiding Qt 5's native combo popup frame."""
    currentTextChanged = Signal(str)

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.popup_menu = QMenu(self)
        self._values = []
        self._current = ''
        self.setAutoDefault(False)
        self.setAccessibleName('重复方式')
        self.setStyleSheet('QPushButton {text-align:right; background:transparent; border:none; padding:5px 8px;}')
        self.clicked.connect(self.showPopup)
        self.popup_menu.triggered.connect(lambda action: self.setCurrentText(action.text()))

    def addItems(self, values):
        for value in values:
            self._values.append(value)
            self.popup_menu.addAction(value).setCheckable(True)
        if not self._current and self._values:
            self.setCurrentText(self._values[0])

    def count(self):
        return len(self._values)

    def currentText(self):
        return self._current

    def setCurrentText(self, value):
        if value not in self._values:
            return
        changed = value != self._current
        self._current = value
        self.setText(value + '  ⌄')
        for action in self.popup_menu.actions():
            action.setChecked(action.text() == value)
        if changed:
            self.currentTextChanged.emit(value)

    def showPopup(self):
        from context_menu_style import style_context_menu
        style_context_menu(self.popup_menu, self.owner)
        size = self.popup_menu.sizeHint()
        self.popup_menu.popup(self.mapToGlobal(QPoint(max(0, self.width()-size.width()), self.height()+3)))
        selected = next((a for a in self.popup_menu.actions() if a.isChecked()), None)
        self.popup_menu.setActiveAction(selected)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Down, Qt.Key_Up):
            self.showPopup()
            event.accept()
            return
        super().keyPressEvent(event)


class ResizableDescription(QPlainTextEdit):
    heightRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_start = None
        self.grip = QLabel('━', self)
        self.grip.setAlignment(Qt.AlignCenter)
        self.grip.setCursor(Qt.SizeVerCursor)
        self.grip.setToolTip('上下拖动调整说明高度，最少保留两行')
        self.grip.setStyleSheet('QLabel {background:transparent; color:#85858d; font-size:10px; padding:0;}')
        self.grip.installEventFilter(self)

    def two_line_height(self):
        chrome = max(0, self.height()-self.viewport().height())
        return int(2*self.fontMetrics().lineSpacing() + 2*self.document().documentMargin() + chrome + 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'grip'):
            self.grip.setGeometry(10, max(0, self.height()-10), max(1, self.width()-20), 8)
            self.grip.raise_()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange) and hasattr(self, 'grip'):
            QTimer.singleShot(0, self._ensure_two_lines)

    def _ensure_two_lines(self):
        minimum = self.two_line_height()
        if self.height() < minimum:
            self.heightRequested.emit(minimum)

    def eventFilter(self, watched, event):
        if watched is self.grip:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._resize_start = (event.globalPos().y(), self.height())
                return True
            if event.type() == QEvent.MouseMove and self._resize_start is not None:
                y, height = self._resize_start
                self.heightRequested.emit(max(self.two_line_height(), height+event.globalPos().y()-y))
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self._resize_start = None
                return True
        return super().eventFilter(watched, event)


class ScheduleDialog(QDialog):
    projectReplacementRequested = Signal(str, str)

    def __init__(self, scheduler):
        super().__init__(scheduler.window)
        self.scheduler = scheduler
        self.theme_mode = scheduler.window.view_workspace.theme_mode
        self.setWindowTitle('定时任务')
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._drag_origin = None
        self._resize_start = None
        self.setMouseTracking(True)
        self._task_id = None
        self._editing = True
        self._replacement_pending = False
        self.projectReplacementRequested.connect(self._replace_readonly_project, Qt.QueuedConnection)
        self.resize(960, 500)
        self.setMinimumSize(760, 410)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(3)
        root.addWidget(self.splitter)
        self._build_sidebar()
        self.editor_panel = QWidget(self)
        self.editor_panel.setObjectName('scheduleEditor')
        self.editor_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.editor_panel.setAcceptDrops(True)
        self.editor_panel.setMinimumWidth(500)
        self.splitter.addWidget(self.editor_panel)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([230, 680])
        layout = QVBoxLayout(self.editor_panel)
        layout.setContentsMargins(16, 6, 8, 6)
        title = QLabel('新建定时任务')
        self.title_label = title
        title.setObjectName('scheduleTitle')
        header = QHBoxLayout()
        header.addWidget(title, 1)
        close = QPushButton("×")
        close.setFixedSize(28, 28)
        close.setStyleSheet("QPushButton {padding:0; border:none; background:transparent; font-size:18px;}")
        close.setToolTip("关闭")
        close.clicked.connect(self.reject)
        header.addWidget(close)
        layout.addLayout(header)
        self.description = ResizableDescription(self)
        self.description.setPlaceholderText('说明…（可填写任务名称或用途）')
        self.description.setFixedHeight(self.description.two_line_height())
        self.description.heightRequested.connect(self._resize_description)
        layout.addWidget(self.description)
        card = QFrame()
        card.setObjectName('scheduleCard')
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.form_card = card
        form = QFormLayout(card)
        form.setContentsMargins(16, 14, 16, 14)
        form.setSpacing(14)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        self.path = ProjectPathEdit(self)
        # Return from the native drop before opening a modal file picker.
        self.path.directoryDropped.connect(self._browse_dropped_directory, Qt.QueuedConnection)
        browse = QPushButton('选择文件')
        browse.clicked.connect(lambda: self.browse())
        row_layout.addWidget(self.path, 1)
        row_layout.addWidget(browse)
        form.addRow('项目文件', row)
        self.repeat = RepeatSelector(scheduler.window, self)
        self.repeat.addItems(['每天', '工作日', '每周', '自定义', '仅一次'])
        form.addRow('重复', self.repeat)
        from schedule_datetime import SegmentedDateTimeEdit
        self.when = SegmentedDateTimeEdit(QDateTime.currentDateTime().addSecs(300), self)
        form.addRow('时间', self.when)
        self.interval = QSpinBox()
        self.interval.setRange(1, 525600)
        self.interval.setValue(60)
        self.interval.setSuffix(' 分钟')
        form.addRow('间隔', self.interval)
        interval_row = form.rowCount()-1
        form.setRowVisible(interval_row, False)
        self.repeat.currentTextChanged.connect(lambda value: form.setRowVisible(interval_row, value == '自定义'))
        timezone = QLabel('使用本机时间；从所选日期开始；工作日为周一至周五。')
        timezone.setWordWrap(True)
        form.addRow('', timezone)
        layout.addWidget(card)
        self.advanced_button = QPushButton('高级  ⌄')
        self.advanced_button.setCheckable(True)
        self.advanced_button.setFlat(True)
        self.advanced_button.setAutoDefault(False)
        advanced_actions = QHBoxLayout()
        advanced_actions.addWidget(self.advanced_button, 0, Qt.AlignLeft)
        advanced_actions.addStretch()
        self.save_button = QPushButton('保存')
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(lambda: self.save_task(self.enable_button.isChecked()))
        advanced_actions.addWidget(self.save_button, 0, Qt.AlignRight)
        layout.addLayout(advanced_actions)
        self.advanced = QWidget()
        self.advanced.setObjectName("scheduleAdvancedBody")
        advanced_layout = QVBoxLayout(self.advanced)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setAlignment(Qt.AlignTop)
        advanced_layout.setSpacing(8)
        details = QLabel('到达安全暂停点后运行，完成后继续主任务；手动暂停的主任务仍保持暂停。\n'
            '多个到期任务依次执行。录制期间延后执行；按“结束任务”取消当前及待运行任务。\n'
            '程序需保持打开。关闭期间错过的任务，下次打开补执行一次；不会重复补跑。')
        details.setWordWrap(True)
        details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.advanced_details = details
        advanced_layout.addWidget(details)
        self.advanced.hide()
        self.advanced_button.toggled.connect(self._toggle_advanced)
        self.advanced_scroll = QScrollArea(self)
        self.advanced_scroll.setObjectName('scheduleAdvancedScroll')
        self.advanced_scroll.setFrameShape(QFrame.NoFrame)
        self.advanced_scroll.setWidgetResizable(True)
        self.advanced_scroll.setWidget(self.advanced)
        self.advanced_scroll.setStyleSheet('QScrollArea#scheduleAdvancedScroll {background:transparent; border:none;}')
        self.advanced_scroll.viewport().setObjectName('scheduleAdvancedViewport')
        self.advanced_scroll.viewport().setAutoFillBackground(False)
        self.advanced_scroll.hide()
        layout.addWidget(self.advanced_scroll)
        layout.addStretch()
        actions = QHBoxLayout()
        actions.addStretch()
        self.disable_button = QPushButton('未开启')
        self.disable_button.setCheckable(True)
        self.disable_button.clicked.connect(lambda: self._choose_enabled(False))
        self.enable_button = QPushButton('开启')
        self.enable_button.setCheckable(True)
        self.enable_button.clicked.connect(lambda: self._choose_enabled(True))
        for button in (self.disable_button, self.enable_button):
            button.setObjectName('scheduleStateButton')
            button.setAutoDefault(False)
        actions.addWidget(self.disable_button)
        actions.addWidget(self.enable_button)
        layout.addLayout(actions)
        # Disabled form controls still need to receive the gesture that unlocks
        # details. Filter both their surfaces and parents for native Qt routing.
        for widget in (self.editor_panel, self.description, self.form_card, self.advanced):
            widget.installEventFilter(self)
            if widget is not self.editor_panel:
                for child in widget.findChildren(QWidget):
                    child.installEventFilter(self)
        scheduler.changed.connect(self.refresh)
        from settings_theme import apply_settings_theme
        apply_settings_theme(self, scheduler.window)
        dark = scheduler.window.view_workspace.theme_mode == 'dark'
        self._surface = '#2c2c2c' if dark else '#ffffff'
        self._border = '#424248' if dark else '#dfe4eb'
        self.setStyleSheet(self.styleSheet() + (
            'QDialog {background:transparent;}'
            'QPlainTextEdit, QListWidget {background:'+self._surface+';color:'+('#f1f1f3' if dark else '#202938')+';border:1px solid '+self._border+';border-radius:10px;padding:8px;}'
            'QFrame#scheduleCard {border:1px solid '+('#424248' if dark else '#dfe4eb')+';border-radius:16px;}'
            'QLabel#scheduleTitle {font-size:18px;font-weight:600;}'
            'QPlainTextEdit {border-radius:16px;padding:12px;}'))
        # Explicit brushes prevent native light scroll-content backgrounds.
        for widget in (self.advanced, self.advanced_scroll, self.advanced_scroll.viewport(), self.entries.viewport()):
            palette = widget.palette()
            palette.setColor(QPalette.Window, QColor(self._surface))
            palette.setColor(QPalette.Base, QColor(self._surface))
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)
        self.advanced.setAttribute(Qt.WA_StyledBackground, True)
        self.advanced_scroll.setStyleSheet('QScrollArea#scheduleAdvancedScroll, QWidget#scheduleAdvancedViewport {background:'+self._surface+';border:none;}')
        self.setStyleSheet(self.styleSheet() +
            'QWidget#scheduleAdvancedBody {background:'+self._surface+';border:none;}'
            'QListWidget#scheduleTaskList {padding:4px;}'
            'QListWidget#scheduleTaskList::item {padding:6px;border:none;}'
            'QScrollBar:vertical {background:transparent;width:8px;margin:0;}'
            'QScrollBar::handle:vertical {background:'+self._border+';border-radius:4px;min-height:24px;}'
            'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}'
            'QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background:transparent;}')
        self.setStyleSheet(self.styleSheet() + f'''
            QFrame#scheduleSidebar {{background:{'#242424' if dark else '#f5f6fa'};border:none;border-radius:14px;}}
            QSplitter::handle {{background:transparent;}}
            QListWidget#scheduleTaskList {{background:transparent;border:none;padding:0;outline:0;}}
            QListWidget#scheduleTaskList::item {{border:none;border-radius:7px;padding:0;margin:0;}}
            QListWidget#scheduleTaskList::item:selected {{background:{'#3b4255' if dark else '#e2e7ff'};}}
            QListWidget#scheduleTaskList::item:hover {{background:{'#34343b' if dark else '#eceef5'};}}
            QWidget#scheduleDateTime {{background:{self._surface};border:1px solid {self._border};border-radius:10px;}}
            QLineEdit#scheduleDateSection {{background:transparent;border:none;border-radius:2px;padding:2px 0;
                selection-background-color:#176fd1;selection-color:white;}}
            QLabel#scheduleDateSeparator {{padding:0;background:transparent;}}
            QPushButton#scheduleStateButton:checked {{background:#5266dc;color:white;border-color:#5266dc;}}
        ''')
        self.sidebar.setStyleSheet(f'''
            QFrame#scheduleSidebar {{background:{'#242424' if dark else '#f5f6fa'};border:none;border-radius:14px;}}
            QLabel#scheduleTitle {{font-size:18px;font-weight:600;}}
        ''')
        self.entries.setStyleSheet(f'''
            QListWidget {{background:transparent;border:none;padding:0;outline:0;}}
            QListWidget::item {{border:none;border-radius:7px;padding:0;margin:0;}}
            QListWidget::item:selected {{background:{'#3b4255' if dark else '#e2e7ff'};color:{'#eef0f6' if dark else '#202534'};}}
            QListWidget::item:hover {{background:{'#34343b' if dark else '#eceef5'};}}
        ''')
        self.refresh()
        if self.scheduler.tasks:
            self.load_task(self.scheduler.tasks[0]['id'])
        else:
            self.new_task()
        QTimer.singleShot(0, self.description._ensure_two_lines)

    def _resize_description(self, height):
        old_height = self.description.height()
        available = self.screen().availableGeometry()
        room = max(0, available.bottom()-self.y()+1-self.height())
        height = max(self.description.two_line_height(), min(int(height), old_height+room))
        delta = height-old_height
        if not delta:
            return
        window_height = self.height()
        self.description.setFixedHeight(height)
        if hasattr(self, '_collapsed_height'):
            self._collapsed_height = max(self.minimumHeight(), self._collapsed_height+delta)
        self.layout().invalidate()
        self.layout().activate()
        self.resize(self.width(), max(self.minimumHeight(), window_height+delta, self.minimumSizeHint().height()))

    def _toggle_advanced(self, expanded):
        if expanded:
            self._collapsed_height = self.height()
        if expanded:
            self.advanced_scroll.verticalScrollBar().setValue(0)
        self.advanced.setVisible(expanded)
        self.advanced_scroll.setVisible(expanded)
        self.advanced_button.setText('高级  ⌃' if expanded else '高级  ⌄')
        self.layout().invalidate()
        self.layout().activate()
        # Wait for Qt to release the expanded layout's minimum size when hiding.
        QTimer.singleShot(0, self._fit_advanced_height)

    def _fit_advanced_height(self):
        self.layout().activate()
        base_height = getattr(self, '_collapsed_height', self.height())
        height = base_height
        if self.advanced_button.isChecked():
            available = self.screen().availableGeometry()
            self.advanced_details.setFixedHeight(self.advanced_details.heightForWidth(max(100, self.advanced_scroll.width()-10)))
            self.advanced.layout().invalidate()
            desired = self.advanced.minimumSizeHint().height()
            # Preserve the header position; scroll advanced content if room below is limited.
            room = max(0, available.bottom() - self.y() + 1 - base_height - self.layout().spacing())
            extra = min(desired, room)
            self.advanced_scroll.setFixedHeight(extra)
            height += extra + self.layout().spacing()
        self.layout().activate()
        self.resize(self.width(), max(height, self.minimumSizeHint().height(), self.minimumHeight()))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self._surface))
        painter.setPen(QPen(QColor(self._border), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 24, 24)
        painter.end()

    def mousePressEvent(self, event):
        edges = self._resize_edges(event.pos())
        if event.button() == Qt.LeftButton and edges:
            self._resize_start = (event.globalPos(), self.geometry(), edges)
            self._drag_origin = None
            self.grabMouse()
            event.accept()
            return
        if event.button() == Qt.LeftButton and event.pos().y() < 60:
            self._drag_origin = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_start is not None and event.buttons() & Qt.LeftButton:
            start, original, edges = self._resize_start
            delta = event.globalPos() - start
            rect = original.adjusted(0, 0, 0, 0)
            minimum = self.minimumSize().expandedTo(self.minimumSizeHint())
            if edges & Qt.LeftEdge:
                width = max(minimum.width(), min(self.maximumWidth(), original.width() - delta.x()))
                rect.setLeft(original.right() - width + 1)
            elif edges & Qt.RightEdge:
                rect.setWidth(max(minimum.width(), min(self.maximumWidth(), original.width() + delta.x())))
            if edges & Qt.TopEdge:
                height = max(minimum.height(), min(self.maximumHeight(), original.height() - delta.y()))
                rect.setTop(original.bottom() - height + 1)
            elif edges & Qt.BottomEdge:
                rect.setHeight(max(minimum.height(), min(self.maximumHeight(), original.height() + delta.y())))
            self.setGeometry(rect)
            event.accept()
            return
        self._set_resize_cursor(self._resize_edges(event.pos()))
        if self._drag_origin is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_start is not None and event.button() == Qt.LeftButton:
            self._resize_start = None
            self.releaseMouse()
            if self.advanced_button.isChecked():
                self._collapsed_height = max(self.minimumHeight(), self.height() - self.advanced_scroll.height() - self.layout().spacing())
            else:
                self._collapsed_height = self.height()
            self._set_resize_cursor(self._resize_edges(event.pos()))
            event.accept()
            return
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def _resize_edges(self, position):
        edges = Qt.Edge(0)
        if not self.rect().contains(position):
            return edges
        if position.x() < 10:
            edges |= Qt.LeftEdge
        elif position.x() >= self.width() - 10:
            edges |= Qt.RightEdge
        if position.y() < 10:
            edges |= Qt.TopEdge
        elif position.y() >= self.height() - 10:
            edges |= Qt.BottomEdge
        return edges

    def _set_resize_cursor(self, edges):
        if edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edges & (Qt.LeftEdge | Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edges & (Qt.TopEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.unsetCursor()

    def leaveEvent(self, event):
        if self._resize_start is None:
            self.unsetCursor()
        super().leaveEvent(event)

    def hideEvent(self, event):
        if self._resize_start is not None:
            self._resize_start = None
            self.releaseMouse()
        self._drag_origin = None
        super().hideEvent(event)

    @Slot(str)
    def _browse_dropped_directory(self, directory):
        if self.isVisible():
            self.browse(directory)

    def browse(self, directory=None):
        if directory is None:
            current = self.path.text().strip().strip('"')
            path = Path(current) if current else None
            directory = str(path if path.is_dir() else path.parent) if path is not None else ''
        path, _ = QFileDialog.getOpenFileName(self, '选择项目文件', directory, '项目文件 (*.xlsx)')
        if path:
            self.path.setText(path)

    def _build_sidebar(self):
        self.sidebar = QFrame(self)
        self.sidebar.setObjectName('scheduleSidebar')
        self.sidebar.setAttribute(Qt.WA_StyledBackground, True)
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(320)
        self.splitter.addWidget(self.sidebar)
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        heading = QHBoxLayout()
        title = QLabel('定时任务', self.sidebar)
        title.setObjectName('scheduleTitle')
        heading.addWidget(title, 1)
        search = QPushButton('搜索', self.sidebar)
        search.setFlat(True)
        search.setAutoDefault(False)
        heading.addWidget(search)
        layout.addLayout(heading)
        self.search = QLineEdit(self.sidebar)
        self.search.setPlaceholderText('搜索任务或项目文件')
        self.search.textChanged.connect(self.refresh)
        self.search.hide()
        layout.addWidget(self.search)
        search.clicked.connect(self._toggle_search)
        self.new_button = QPushButton('＋  新建任务', self.sidebar)
        self.new_button.setAutoDefault(False)
        self.new_button.clicked.connect(self.new_task)
        layout.addWidget(self.new_button)
        layout.addWidget(QLabel('即将执行', self.sidebar))
        self.entries = QListWidget(self.sidebar)
        self.entries.setObjectName('scheduleTaskList')
        self.entries.setSpacing(2)
        self.entries.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entries.customContextMenuRequested.connect(self._show_task_menu)
        self.entries.currentItemChanged.connect(self._select_task)
        layout.addWidget(self.entries, 1)
        self.empty_tasks = QLabel('暂无定时任务，点击“新建任务”添加。', self.sidebar)
        self.empty_tasks.setWordWrap(True)
        layout.addWidget(self.empty_tasks)

    def _toggle_search(self):
        self.search.setVisible(not self.search.isVisible())
        if self.search.isVisible():
            self.search.setFocus()
        else:
            self.search.clear()

    def _select_task(self, current, previous=None):
        if current is not None:
            self.load_task(current.data(Qt.UserRole))

    def _set_editable(self, editable):
        self._editing = editable
        self.description.setReadOnly(not editable)
        self.form_card.setEnabled(editable)
        self.save_button.setEnabled(editable)
        self.save_button.setToolTip('保存修改并退出编辑' if editable else '双击详情区域或点击任务的笔形图标后编辑')
        self._apply_editor_surface()
        self._sync_edit_icons()

    def _apply_editor_surface(self):
        surface = ('#242424' if self.theme_mode == 'dark' else '#f5f6fa') if self._editing else self._surface
        self.editor_panel.setStyleSheet(f'''
            QWidget#scheduleEditor {{background:{surface};border:none;border-radius:14px;}}
            QPlainTextEdit, QFrame#scheduleCard, QWidget#scheduleDateTime,
            QWidget#scheduleAdvancedBody {{background:{surface};}}
        ''')
        for widget in (self.description.viewport(), self.advanced, self.advanced_scroll, self.advanced_scroll.viewport()):
            palette = widget.palette()
            palette.setColor(QPalette.Window, QColor(surface))
            palette.setColor(QPalette.Base, QColor(surface))
            widget.setPalette(palette)
        self.advanced_scroll.setStyleSheet(
            f'QScrollArea#scheduleAdvancedScroll, QWidget#scheduleAdvancedViewport {{background:{surface};border:none;}}')

    def _sync_edit_icons(self):
        for index in range(self.entries.count()):
            item = self.entries.item(index)
            card = self.entries.itemWidget(item)
            if card is not None:
                card.set_editing(self._editing and item.data(Qt.UserRole) == self._task_id)

    def eventFilter(self, watched, event):
        if (not self._editing and self._task_id is not None
                and event.type() in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop)):
            path = ProjectPathEdit.dropped_path(event.mimeData())
            if path is None:
                event.ignore()
                return True
            event.setDropAction(Qt.CopyAction)
            event.accept()
            if event.type() == QEvent.Drop and not self._replacement_pending:
                self._replacement_pending = True
                # Let the native drop finish before showing confirmation or a picker.
                self.projectReplacementRequested.emit(self._task_id, str(path))
            return True
        if (event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton
                and self._task_id is not None and not self._editing):
            self._edit_task(self._task_id)
            return True
        return super().eventFilter(watched, event)

    def _confirm_project_replacement(self, path):
        box = QMessageBox(self)
        box.setWindowTitle('更换项目目录')
        box.setIcon(QMessageBox.Question)
        box.setTextFormat(Qt.PlainText)
        box.setText('是否更换项目目录？')
        choice = '确认后从该目录选择项目文件，进入编辑，点击“保存”后生效。' if path.is_dir() else '确认后进入编辑，点击“保存”后生效。'
        box.setInformativeText(f'当前项目：{self.path.text()}\n拖入路径：{path}\n\n{choice}')
        replace = box.addButton('更换目录', QMessageBox.AcceptRole)
        cancel = box.addButton('取消', QMessageBox.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        from settings_theme import apply_settings_theme
        apply_settings_theme(box, self.scheduler.window)
        box.exec_()
        accepted = box.clickedButton() is replace
        box.deleteLater()
        return accepted

    def _replacement_target_available(self, task_id):
        if not self.isVisible() or self._task_id != task_id or self._editing:
            return False
        try:
            self.scheduler.task_by_id(task_id)
        except ValueError:
            return False
        if self.scheduler.active and self.scheduler.active['id'] == task_id:
            QMessageBox.information(self, '任务正在执行', '请结束任务后再更换项目目录。')
            return False
        return True

    @Slot(str, str)
    def _replace_readonly_project(self, task_id, dropped_path):
        try:
            if not self._replacement_target_available(task_id):
                return
            path = Path(dropped_path)
            if not self._confirm_project_replacement(path):
                return
            if not self._replacement_target_available(task_id):
                return
            if path.is_dir():
                selected, _ = QFileDialog.getOpenFileName(self, '选择项目文件', str(path), '项目文件 (*.xlsx)')
                if not selected:
                    return
                path = Path(selected)
            if not self._replacement_target_available(task_id):
                return
            if not path.is_file() or path.suffix.lower() != '.xlsx':
                QMessageBox.warning(self, '无法更换项目目录', '请选择存在的 .xlsx 项目文件。')
                return
            self.load_task(task_id, editable=True)
            self.path.setText(str(path))
        except OSError as exc:
            QMessageBox.warning(self, '无法更换项目目录', str(exc))
        finally:
            self._replacement_pending = False

    def _edit_task(self, task_id):
        if self._task_id == task_id and self._editing:
            return
        self.load_task(task_id, editable=True)

    def _choose_enabled(self, enabled):
        if self._editing:
            self._show_enabled_state(enabled)
        else:
            self.save_task(enabled)

    def _show_enabled_state(self, enabled):
        self.enable_button.setChecked(bool(enabled))
        self.disable_button.setChecked(not enabled)

    def new_task(self):
        self._task_id = None
        self._set_editable(True)
        self.title_label.setText('新建定时任务')
        self.description.clear()
        self.path.clear()
        self.repeat.setCurrentText('每天')
        self.when.setDateTime(QDateTime.currentDateTime().addSecs(300))
        self.interval.setValue(60)
        self.entries.blockSignals(True)
        self.entries.setCurrentRow(-1)
        self.entries.blockSignals(False)
        self.enable_button.setToolTip('保存后启用任务')
        self.disable_button.setToolTip('保存后暂不启用任务')
        self._show_enabled_state(True)

    def load_task(self, task_id, *, editable=False):
        try:
            task = self.scheduler.task_by_id(task_id)
        except ValueError:
            self.new_task()
            return
        active = self.scheduler.active and self.scheduler.active['id'] == task_id
        if editable and active:
            QMessageBox.information(self, '任务正在执行', '请结束任务后再编辑。')
            return
        self._task_id = task_id
        self._set_editable(editable)
        self.title_label.setText('编辑定时任务' if editable else '定时任务详情')
        self.description.setPlainText(task.get('description', ''))
        self.path.setText(task['path'])
        self.repeat.setCurrentText(task['repeat'])
        self.when.setDateTime(QDateTime.fromString(task['next_run'], Qt.ISODate))
        self.interval.setValue(task.get('interval_minutes', 60))
        self.enable_button.setToolTip('保存后启用任务' if editable else '启用此任务')
        self.disable_button.setToolTip('保存后暂不启用任务' if editable else '不启用此任务')
        self._show_enabled_state(task.get('enabled', True))
        self.entries.blockSignals(True)
        for index in range(self.entries.count()):
            if self.entries.item(index).data(Qt.UserRole) == task_id:
                self.entries.setCurrentRow(index)
                break
        self.entries.blockSignals(False)

    def refresh(self, *_):
        if not hasattr(self, 'entries'):
            return
        scroll = self.entries.verticalScrollBar().value()
        query = self.search.text().strip().casefold()
        tasks = sorted(self.scheduler.tasks, key=lambda task: (not task.get('enabled', True), task['next_run']))
        self.entries.blockSignals(True)
        self.entries.clear()
        for task in tasks:
            title = task.get('description', '').strip().split('\n')[0] or Path(task['path']).name
            if query and query not in (title + ' ' + task['path']).casefold():
                continue
            due = datetime.fromisoformat(task['next_run'])
            day = '今天' if due.date() == datetime.now().date() else due.strftime('%m月%d日')
            repeat = task['repeat']
            if repeat == '自定义':
                repeat = f"每 {task.get('interval_minutes', 60)} 分钟"
            details = f'{day} {due:%H:%M:%S} · {repeat}'
            enabled = task.get('enabled', True)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, task['id'])
            item.setData(Qt.AccessibleTextRole, f"{title}，{details}，{'开启' if enabled else '未开启'}")
            item.setToolTip(f"{task['path']}\n{task.get('status', '')}\n右击可编辑")
            self.entries.addItem(item)
            active = bool(self.scheduler.active and self.scheduler.active['id'] == task['id'])
            card = ScheduleTaskCard(title, details, enabled=enabled, editable=not active,
                                    dark=self.theme_mode == 'dark', parent=self.entries)
            card.editRequested.connect(lambda task_id=task['id']: self._edit_task(task_id))
            card.set_editing(self._editing and task['id'] == self._task_id)
            self.entries.setItemWidget(item, card)
            card.ensurePolished()
            item.setSizeHint(QSize(0, max(card.sizeHint().height(), card.minimumSizeHint().height())))
            if task['id'] == self._task_id:
                self.entries.setCurrentItem(item)
        self.entries.blockSignals(False)
        self.entries.verticalScrollBar().setValue(scroll)
        self.empty_tasks.setText('没有匹配的任务。' if query else '暂无定时任务，点击“新建任务”添加。')
        self.empty_tasks.setVisible(self.entries.count() == 0)
        if self._task_id and not self._editing:
            self.load_task(self._task_id)

    def build_task_menu(self, task_id):
        task = self.scheduler.task_by_id(task_id)
        active = bool(self.scheduler.active and self.scheduler.active['id'] == task_id)
        menu = QMenu(self)
        edit = menu.addAction('编辑')
        edit.setEnabled(not active)
        edit.triggered.connect(lambda: self._edit_task(task_id))
        toggle = menu.addAction('未开启' if task.get('enabled', True) else '开启')
        toggle.triggered.connect(lambda: self._toggle_task(task_id))
        menu.addSeparator()
        delete = menu.addAction('删除任务')
        delete.setEnabled(not active)
        delete.triggered.connect(lambda: self.delete_task(task_id))
        from context_menu_style import style_context_menu
        style_context_menu(menu, self.scheduler.window)
        return menu

    def _show_task_menu(self, position):
        item = self.entries.itemAt(position)
        if item is None:
            return
        menu = self.build_task_menu(item.data(Qt.UserRole))
        menu.exec_(self.entries.viewport().mapToGlobal(position))
        menu.deleteLater()

    def _toggle_task(self, task_id):
        try:
            task = self.scheduler.task_by_id(task_id)
            self.scheduler.set_enabled(task_id, not task.get('enabled', True))
        except ValueError as exc:
            QMessageBox.warning(self, '无法更改定时任务', str(exc))

    def save_task(self, enabled):
        try:
            if self._task_id is not None and not self._editing:
                self.scheduler.set_enabled(self._task_id, enabled)
                self._show_enabled_state(self.scheduler.task_by_id(self._task_id).get('enabled', True))
                return
            values = dict(description=self.description.toPlainText().strip(), path=self.path.text().strip(),
                repeat=self.repeat.currentText(), interval_minutes=self.interval.value(), enabled=enabled,
                next_run=self.when.dateTime().toString('yyyy-MM-ddTHH:mm:ss'))
            task_id = (self.scheduler.update_task(self._task_id, values) if self._task_id is not None
                       else self.scheduler.add(values))
        except (ValueError, OSError) as exc:
            task = next((task for task in self.scheduler.tasks if task['id'] == self._task_id), None)
            self._show_enabled_state(enabled if self._editing else task.get('enabled', True) if task else True)
            QMessageBox.warning(self, '无法保存定时任务', str(exc))
            return
        self.load_task(task_id)

    def create_task(self):
        self.save_task(True)

    def delete_task(self, task_id=None):
        if task_id is None:
            item = self.entries.currentItem()
            task_id = item.data(Qt.UserRole) if item else None
        if task_id is None:
            return
        try:
            self.scheduler.remove_task(task_id)
        except ValueError as exc:
            QMessageBox.warning(self, '无法删除定时任务', str(exc))
            return
        if self._task_id == task_id:
            self.new_task()
