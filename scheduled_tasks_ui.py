"""Chinese scheduled-project settings, matching the compact rounded task card."""
from datetime import datetime, timedelta
from qt_compat.QtCore import Qt, QDateTime, QRectF, QPoint, Signal, QTimer, QEvent, QLocale
from qt_compat.QtGui import QPainter, QColor, QPen, QTextCharFormat, QPalette
from qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QMenu, QDateTimeEdit, QFileDialog, QMessageBox,
    QWidget, QFormLayout, QListWidget, QCheckBox, QFrame, QSpinBox, QScrollArea, QSizePolicy, QCalendarWidget, QToolButton)


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
    def __init__(self, scheduler):
        super().__init__(scheduler.window)
        self.scheduler = scheduler
        self.theme_mode = scheduler.window.view_workspace.theme_mode
        self.setWindowTitle('定时任务')
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._drag_origin = None
        self.resize(680, 490)
        self.setMinimumSize(520, 440)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        title = QLabel('设置定时任务')
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
        self.description.setFixedHeight(125)
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
        self.path = QLineEdit()
        self.path.setPlaceholderText('选择要运行的 .xlsx 项目文件')
        browse = QPushButton('选择文件')
        browse.clicked.connect(self.browse)
        row_layout.addWidget(self.path, 1)
        row_layout.addWidget(browse)
        form.addRow('项目文件', row)
        self.repeat = RepeatSelector(scheduler.window, self)
        self.repeat.addItems(['每天', '工作日', '每周', '自定义', '仅一次'])
        form.addRow('重复', self.repeat)
        self.when = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        self.when.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.when.setCalendarPopup(True)
        self.calendar = QCalendarWidget(self.when)
        self.calendar.setLocale(QLocale(QLocale.Chinese, QLocale.China))
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.setGridVisible(False)
        self.when.setCalendarWidget(self.calendar)
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
        layout.addWidget(self.advanced_button, 0, Qt.AlignLeft)
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
        self.entries = QListWidget()
        self.entries.setFixedHeight(110)
        self.entries.setObjectName("scheduleTaskList")
        self.empty_tasks = QLabel("暂无定时任务，在上方选择项目和时间后点击创建。")
        self.empty_tasks.setWordWrap(True)
        advanced_layout.addWidget(self.empty_tasks)
        advanced_layout.addWidget(self.entries, 1)
        manage = QHBoxLayout()
        toggle = QPushButton('启用 / 停用')
        toggle.clicked.connect(self.toggle_task)
        delete = QPushButton('删除任务')
        delete.clicked.connect(self.delete_task)
        manage.addWidget(toggle)
        manage.addWidget(delete)
        manage.addStretch()
        advanced_layout.addLayout(manage)
        layout.addStretch()
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton('取消')
        cancel.clicked.connect(self.reject)
        create = QPushButton('创建')
        create.setObjectName('settingsSave')
        create.clicked.connect(self.create_task)
        actions.addWidget(cancel)
        actions.addWidget(create)
        layout.addLayout(actions)
        scheduler.changed.connect(self.refresh)
        from settings_theme import apply_settings_theme
        apply_settings_theme(self, scheduler.window)
        dark = scheduler.window.view_workspace.theme_mode == 'dark'
        self._surface = '#2c2c2c' if dark else '#ffffff'
        self._border = '#424248' if dark else '#dfe4eb'
        self.setStyleSheet(self.styleSheet() + (
            'QDialog {background:transparent;}'
            'QPlainTextEdit, QListWidget, QDateTimeEdit {background:'+self._surface+';color:'+('#f1f1f3' if dark else '#202938')+';border:1px solid '+self._border+';border-radius:10px;padding:8px;}'
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
            'QDateTimeEdit::drop-down {subcontrol-origin:padding;subcontrol-position:top right;width:24px;border:none;background:transparent;}'
            'QScrollBar:vertical {background:transparent;width:8px;margin:0;}'
            'QScrollBar::handle:vertical {background:'+self._border+';border-radius:4px;min-height:24px;}'
            'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}'
            'QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background:transparent;}')
        self.refresh()
        self._style_calendar()

    def _style_calendar(self):
        dark = self.theme_mode == 'dark'
        background = '#2c2c2c' if dark else '#ffffff'
        text = '#ededf0' if dark else '#202938'
        muted = '#a4a4ad' if dark else '#77808d'
        hover = '#414149' if dark else '#edf1f6'
        selected = '#446eae' if dark else '#e0ebfc'
        self.calendar.setMinimumWidth(280)
        self.calendar.layout().setContentsMargins(8, 8, 8, 8)
        popup = self.calendar.window()
        if popup is not self and popup is not self.scheduler.window:
            popup.setObjectName("scheduleCalendarPopup")
            popup.setWindowFlag(Qt.FramelessWindowHint, True)
            popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            popup.setAttribute(Qt.WA_TranslucentBackground, True)
            popup.setAutoFillBackground(False)
            popup.setStyleSheet("QWidget#scheduleCalendarPopup {background:transparent; border:none;}")
            from context_menu_style import _RoundedMenuBackground
            popup._rounded_background = _RoundedMenuBackground(popup, background, self._border)
            popup.installEventFilter(popup._rounded_background)
        self.calendar.setStyleSheet(f'''
            QCalendarWidget {{background:{background}; color:{text}; border:1px solid {self._border}; border-radius:10px; padding:6px;}}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{background:{background}; border:none;}}
            QCalendarWidget QToolButton {{background:transparent; color:{text}; border:none; border-radius:5px;
                padding:2px 6px; margin:0; min-width:0; min-height:0; font-size:12px;}}
            QCalendarWidget QToolButton:hover {{background:{hover};}}
            QCalendarWidget QToolButton::menu-indicator {{width:0; height:0;}}
            QCalendarWidget QSpinBox {{background:{hover}; color:{text}; border:none; border-radius:4px; padding:2px; min-height:0; font-size:12px;}}
            QCalendarWidget QAbstractItemView {{background:{background}; alternate-background-color:{background}; color:{text};
                selection-background-color:{selected}; selection-color:{text}; border:none; outline:0; font-size:12px;}}
            QCalendarWidget QAbstractItemView:disabled {{color:{muted};}}
        ''')
        header = QTextCharFormat()
        header.setForeground(QColor(muted))
        header.setBackground(QColor(background))
        self.calendar.setHeaderTextFormat(header)
        weekend = QTextCharFormat()
        weekend.setForeground(QColor(muted))
        for day in (Qt.Saturday, Qt.Sunday):
            self.calendar.setWeekdayTextFormat(day, weekend)
        for name, label in (('qt_calendar_prevmonth', '‹'), ('qt_calendar_nextmonth', '›')):
            button = self.calendar.findChild(QToolButton, name)
            if button is not None:
                from qt_compat.QtGui import QIcon
                button.setIcon(QIcon())
                button.setText(label)
                button.setFixedSize(28, 26)
                button.setStyleSheet("QToolButton {font-size:18px; padding:0;}")
        for name in ('qt_calendar_monthbutton', 'qt_calendar_yearbutton'):
            button = self.calendar.findChild(QToolButton, name)
            if button is not None:
                button.setFixedHeight(26)
        from context_menu_style import style_context_menu
        for menu in self.calendar.findChildren(QMenu):
            style_context_menu(menu, self.scheduler.window)

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
        if event.button() == Qt.LeftButton and event.pos().y() < 60:
            self._drag_origin = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_origin)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择项目文件', '', '项目文件 (*.xlsx)')
        if path:
            self.path.setText(path)

    def refresh(self):
        selected = self.entries.currentRow()
        self.entries.clear()
        for task in self.scheduler.tasks:
            title = task.get('description') or task['path'].replace('\\', '/').rsplit('/', 1)[-1]
            state = '启用' if task.get('enabled', True) else '停用'
            self.entries.addItem(f"{title}  ·  {task['repeat']}  {task['next_run'].replace('T', ' ')}  ·  {state}\n{task.get('status', '')}")
            self.entries.item(self.entries.count()-1).setToolTip(task['path'])
        self.empty_tasks.setVisible(not self.entries.count())
        self.entries.setVisible(bool(self.entries.count()))
        if self.advanced_button.isChecked():
            QTimer.singleShot(0, self._fit_advanced_height)
        if self.entries.count():
            self.entries.setCurrentRow(max(0, min(selected, self.entries.count()-1)))

    def create_task(self):
        try:
            self.scheduler.add(dict(description=self.description.toPlainText().strip(), path=self.path.text().strip(),
                repeat=self.repeat.currentText(), interval_minutes=self.interval.value(), next_run=self.when.dateTime().toString('yyyy-MM-ddTHH:mm:ss')))
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, '无法创建定时任务', str(exc))
            return
        self.description.clear()
        self.refresh()

    def toggle_task(self):
        row = self.entries.currentRow()
        if row < 0:
            return
        task = self.scheduler.tasks[row]
        if not task.get('enabled', True) and datetime.fromisoformat(task['next_run']) <= datetime.now():
            from scheduled_tasks import next_occurrence
            value = next_occurrence(task, datetime.now())
            if value is None:
                QMessageBox.information(self, '设置时间', '单次任务的时间已过去，请在上方选择新的时间创建任务。')
                return
            task['next_run'] = value
        task['enabled'] = not task.get('enabled', True)
        self.scheduler.save()

    def delete_task(self):
        row = self.entries.currentRow()
        if row < 0:
            return
        task = self.scheduler.tasks[row]
        if self.scheduler.active and self.scheduler.active['id'] == task['id']:
            QMessageBox.information(self, '任务正在执行', '请先结束当前定时任务，再删除。')
            return
        self.scheduler.queue[:] = [item for item in self.scheduler.queue if item['id'] != task['id']]
        self.scheduler.tasks.pop(row)
        self.scheduler.save()
