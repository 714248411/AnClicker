"""Segmented local date/time input for scheduled tasks."""
from qt_compat.QtCore import Qt, QDate, QTime, QDateTime, QEvent, Signal, QLocale, QRectF, QPoint, QPointF
from qt_compat.QtGui import QIntValidator, QPainter, QColor, QPen, QIcon, QTextCharFormat
from qt_compat.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
                               QPushButton, QFrame, QCalendarWidget, QToolButton)


class CalendarDropButton(QPushButton):
    """Draw the chevron at the button center, independent of font baselines."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.palette().buttonText().color(), 1.5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        center = QRectF(self.rect()).center()
        painter.drawLine(QPointF(center.x()-3.5, center.y()-1.75),
                         QPointF(center.x(), center.y()+1.75))
        painter.drawLine(QPointF(center.x(), center.y()+1.75),
                         QPointF(center.x()+3.5, center.y()-1.75))


class CalendarPopup(QFrame):
    def __init__(self, owner):
        super().__init__(owner, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName('scheduleCalendarPopup')
        self.setFrameShape(QFrame.NoFrame)
        self.calendar = QCalendarWidget(self)
        self.calendar.setLocale(QLocale(QLocale.Chinese, QLocale.China))
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.setGridVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.calendar)
        self.apply_theme(False)

    def apply_theme(self, dark):
        self._background = '#2c2c2c' if dark else '#ffffff'
        self._border = '#424248' if dark else '#dfe4eb'
        text = '#ededf0' if dark else '#202938'
        muted = '#a4a4ad' if dark else '#77808d'
        hover = '#414149' if dark else '#edf1f6'
        self.setStyleSheet(f'''
            QFrame#scheduleCalendarPopup {{background:transparent;border:none;}}
            QCalendarWidget {{background:{self._background};color:{text};border:none;}}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{background:{self._background};border:none;}}
            QCalendarWidget QToolButton {{background:transparent;color:{text};border:none;border-radius:5px;
                padding:2px 6px;margin:0;min-width:0;min-height:0;font-size:12px;}}
            QCalendarWidget QToolButton:hover {{background:{hover};}}
            QCalendarWidget QToolButton::menu-indicator {{width:0;height:0;}}
            QCalendarWidget QSpinBox {{background:{hover};color:{text};border:none;border-radius:4px;padding:2px;font-size:12px;}}
            QCalendarWidget QAbstractItemView {{background:{self._background};alternate-background-color:{self._background};color:{text};
                selection-background-color:#5266dc;selection-color:white;border:none;outline:0;font-size:12px;}}
            QCalendarWidget QAbstractItemView:disabled {{color:{muted};}}
        ''')
        header = QTextCharFormat()
        header.setForeground(QColor(muted))
        header.setBackground(QColor(self._background))
        self.calendar.setHeaderTextFormat(header)
        weekend = QTextCharFormat()
        weekend.setForeground(QColor(muted))
        for day in (Qt.Saturday, Qt.Sunday):
            self.calendar.setWeekdayTextFormat(day, weekend)
        for name, label in (('qt_calendar_prevmonth', '‹'), ('qt_calendar_nextmonth', '›')):
            button = self.calendar.findChild(QToolButton, name)
            if button is not None:
                button.setIcon(QIcon())
                button.setText(label)
                button.setFixedSize(28, 26)
                button.setStyleSheet('QToolButton {font-size:18px;padding:0;}')
        for name in ('qt_calendar_monthbutton', 'qt_calendar_yearbutton'):
            button = self.calendar.findChild(QToolButton, name)
            if button is not None:
                button.setFixedHeight(26)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self._background))
        painter.setPen(QPen(QColor(self._border), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 10, 10)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)


class DateTimeSection(QLineEdit):
    def __init__(self, owner, name, digits, maximum):
        super().__init__(owner)
        self.owner, self.name, self.digits = owner, name, digits
        self._wheel_remainder = 0
        self._clicked_since_focus = False
        self._select_after_click = False
        self._point_editing = False
        self.setObjectName('scheduleDateSection')
        self.setAccessibleName(name)
        self.setToolTip(f'{name}：单击全选，再次点击输入；滚轮向下增加，向上减少')
        self.setMaxLength(digits)
        self.setValidator(QIntValidator(1 if name in ('年', '月', '日') else 0, maximum, self))
        self.setAlignment(Qt.AlignLeft)
        self.editingFinished.connect(lambda: owner.commit(self))

    def mousePressEvent(self, event):
        first_click = not self._clicked_since_focus
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._clicked_since_focus = True
            self._select_after_click = first_click
            self._point_editing = not first_click

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._select_after_click:
            self.selectAll()
            self._select_after_click = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._clicked_since_focus = False
        self._point_editing = False
        self.owner.active_section = self
        self.selectAll()

    def wheelEvent(self, event):
        self.owner.commit(self)
        self._wheel_remainder += event.angleDelta().y()
        steps = -int(self._wheel_remainder / 120)
        if steps:
            self._wheel_remainder += steps * 120
            self.owner.step_section(self.name, steps)
        self.setFocus(Qt.MouseFocusReason)
        self.selectAll()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.owner.commit(self)
            self.owner.step_section(self.name, 1 if event.key() == Qt.Key_Down else -1)
            self.selectAll()
            event.accept()
            return
        # The section is fixed-width. A second click edits digits at the caret
        # instead of rejecting input because the existing text fills maxLength.
        if (self._point_editing and event.text().isascii() and event.text().isdigit()
                and not event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)
                and not self.hasSelectedText() and len(self.text()) >= self.maxLength()):
            position = min(self.cursorPosition(), self.maxLength() - 1)
            self.setSelection(position, 1)
        super().keyPressEvent(event)


class SegmentedDateTimeEdit(QWidget):
    dateTimeChanged = Signal(QDateTime)

    def __init__(self, value=None, parent=None):
        super().__init__(parent)
        self.setObjectName('scheduleDateTime')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._value = QDateTime(value or QDateTime.currentDateTime())
        self.active_section = None
        self.sections = {}
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 5, 8, 5)
        row.setSpacing(0)
        for name, digits, maximum, separator in (
            ('年', 4, 9999, '-'), ('月', 2, 12, '-'), ('日', 2, 31, '  '),
            ('时', 2, 23, ':'), ('分', 2, 59, ':'), ('秒', 2, 59, ''),
        ):
            field = DateTimeSection(self, name, digits, maximum)
            self.sections[name] = field
            row.addWidget(field)
            if separator:
                label = QLabel(separator, self)
                label.setObjectName('scheduleDateSeparator')
                row.addWidget(label)
        row.addStretch()
        self.calendar_popup = CalendarPopup(self)
        self.calendar = self.calendar_popup.calendar
        self.calendar.clicked.connect(self._select_date)
        self.calendar.activated.connect(self._select_date)
        self.calendar_button = CalendarDropButton('', self)
        self.calendar_button.setAccessibleName('选择日期')
        self.calendar_button.setToolTip('展开日历选择日期')
        self.calendar_button.setAutoDefault(False)
        self.calendar_button.setFixedSize(24, 28)
        self.calendar_button.setStyleSheet(
            'QPushButton {background:transparent;border:none;padding:0;font-size:18px;}'
            'QPushButton:hover {background:rgba(100,120,180,35);border-radius:5px;}'
        )
        self.calendar_button.clicked.connect(self.show_calendar)
        row.addWidget(self.calendar_button, 0, Qt.AlignVCenter)
        self.refresh_button = QPushButton('↻', self)
        self.refresh_button.setObjectName('scheduleTimeRefresh')
        self.refresh_button.setAccessibleName('刷新为当前时间')
        self.refresh_button.setToolTip('刷新为当前时间')
        self.refresh_button.setAutoDefault(False)
        self.refresh_button.setFixedSize(28, 28)
        self.refresh_button.setStyleSheet(
            'QPushButton {background:transparent;border:none;padding:0;font-size:20px;}'
            'QPushButton:hover {background:rgba(100,120,180,35);border-radius:5px;}'
        )
        self.refresh_button.clicked.connect(lambda: self.setDateTime(QDateTime.currentDateTime()))
        row.addWidget(self.refresh_button)
        self.setFocusProxy(self.sections['年'])
        self._refresh()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange) and hasattr(self, 'sections'):
            self._size_sections()

    def showEvent(self, event):
        super().showEvent(event)
        self._size_sections()

    def hideEvent(self, event):
        self.calendar_popup.hide()
        super().hideEvent(event)

    def show_calendar(self):
        if self.calendar_popup.isVisible():
            self.calendar_popup.hide()
            return
        current = self.dateTime()
        self.calendar.setSelectedDate(current.date())
        self.calendar.setCurrentPage(current.date().year(), current.date().month())
        self.calendar_popup.apply_theme(getattr(self.window(), 'theme_mode', '') == 'dark')
        self.calendar_popup.adjustSize()
        available = self.screen().availableGeometry()
        point = self.mapToGlobal(QPoint(self.width() - self.calendar_popup.width(), self.height() + 4))
        if point.y() + self.calendar_popup.height() > available.bottom() + 1:
            point.setY(self.mapToGlobal(QPoint(0, 0)).y() - self.calendar_popup.height() - 4)
        point.setX(max(available.left(), min(point.x(), available.right() + 1 - self.calendar_popup.width())))
        point.setY(max(available.top(), min(point.y(), available.bottom() + 1 - self.calendar_popup.height())))
        self.calendar_popup.move(point)
        self.calendar_popup.show()
        self.calendar.setFocus()

    def _select_date(self, date):
        self.setDateTime(QDateTime(date, self._value.time()))
        self.calendar_popup.hide()

    def _size_sections(self):
        for field in self.sections.values():
            field.setFixedWidth(field.fontMetrics().horizontalAdvance('0' * field.digits) + 10)

    def _refresh(self):
        date, time = self._value.date(), self._value.time()
        values = (date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())
        for field, value in zip(self.sections.values(), values):
            field.setText(str(value).zfill(field.digits))

    def dateTime(self):
        if self.active_section is not None:
            self.commit(self.active_section)
        return QDateTime(self._value)

    def setDateTime(self, value):
        value = QDateTime(value)
        if not value.isValid() or not 1 <= value.date().year() <= 9999:
            return
        changed = value != self._value
        self._value = value
        self._refresh()
        if changed:
            self.dateTimeChanged.emit(QDateTime(value))

    def commit(self, field):
        date, time = self._value.date(), self._value.time()
        year, month, day = date.year(), date.month(), date.day()
        hour, minute, second = time.hour(), time.minute(), time.second()
        current = {'年': year, '月': month, '日': day, '时': hour, '分': minute, '秒': second}[field.name]
        if field.text() == str(current).zfill(field.digits):
            return
        if field.hasAcceptableInput():
            value = int(field.text())
            if field.name == '年': year = value
            elif field.name == '月': month = value
            elif field.name == '日': day = value
            elif field.name == '时': hour = value
            elif field.name == '分': minute = value
            elif field.name == '秒': second = value
            day = min(day, QDate(year, month, 1).daysInMonth())
            self.setDateTime(QDateTime(QDate(year, month, day), QTime(hour, minute, second)))
        else:
            self._refresh()

    def step_section(self, name, steps):
        if name == '年': value = self._value.addYears(steps)
        elif name == '月': value = self._value.addMonths(steps)
        elif name == '日': value = self._value.addDays(steps)
        else: value = self._value.addSecs(steps * {'时': 3600, '分': 60, '秒': 1}[name])
        self.setDateTime(value)
