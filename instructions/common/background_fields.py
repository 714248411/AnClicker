"""Foreground-style fields backed by the unchanged background argument contract."""
import math
from qt_compat.QtCore import Qt, QSignalBlocker
from qt_compat.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QLabel, QPushButton, QComboBox, QSlider, QDialog, QMessageBox)
from .input_controls import PasteTextEdit, KeyCaptureDialog


def row(parent, *widgets):
    body = QWidget(parent)
    layout = QHBoxLayout(body)
    layout.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        layout.addWidget(widget, 1 if isinstance(widget, (QLineEdit, QComboBox, QSlider)) else 0)
    return body


class CoordinateField(QLineEdit):
    """Show x,y or x,y,width,height; keep corner coordinates in saved projects."""
    def __init__(self, controls, changed, parent=None):
        super().__init__(parent)
        self.controls, self.changed = controls, changed
        self.region = len(controls) == 4
        self._syncing = False
        self.error = ''
        self.setObjectName('backgroundRegion' if self.region else 'backgroundPoint')
        self.setMinimumHeight(32)
        for control in controls:
            control.textChanged.connect(self.refresh)
        self.textChanged.connect(self.apply_text)
        self.refresh()

    def refresh(self, *_):
        if self._syncing:
            return
        self.error = ''
        values = [c.text() for c in self.controls]
        self.setPlaceholderText('x,y,宽度,高度' if self.region else 'x,y；支持 {{变量名}}')
        if self.region:
            try:
                x1, y1, x2, y2 = [int(v, 16 if v.strip().lower().startswith('0x') else 10) for v in values]
                values = [str(v) for v in (x1, y1, x2-x1, y2-y1)]
            except ValueError:
                values = []
                self.setPlaceholderText('已使用变量坐标；展开高级设置编辑')
        blocked = QSignalBlocker(self)
        self.setText(','.join(values))
        blocked.unblock()

    def apply_text(self, text):
        values = [v.strip() for v in text.strip().strip('()[]').replace('，', ',').split(',')]
        try:
            if len(values) != len(self.controls) or not all(values):
                raise ValueError('识别范围请填写 x,y,宽度,高度' if self.region else '坐标请填写 x,y')
            if self.region:
                try:
                    x, y, width, height = [int(v) for v in values]
                except ValueError:
                    raise ValueError('范围请填写整数；变量坐标请在高级设置中填写') from None
                if width <= 0 or height <= 0:
                    raise ValueError('识别范围的宽度和高度必须大于零')
                values = [str(v) for v in (x, y, x+width, y+height)]
            self.error = ''
        except ValueError as error:
            self.error = str(error)
            return
        self._syncing = True
        try:
            for control, value in zip(self.controls, values):
                blocked = QSignalBlocker(control)
                control.setText(value)
                blocked.unblock()
        finally:
            self._syncing = False
        self.changed()

    def validate(self):
        if self.error:
            raise ValueError(self.error)


class PrecisionField(QWidget):
    def __init__(self, raw, maximum, parent=None):
        super().__init__(parent)
        self.raw, self.maximum = raw, maximum
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setObjectName('backgroundConfidenceSlider')
        self.slider.setRange(0, 100)
        self.percent = QLabel(self)
        raw.setMinimumWidth(80)
        raw.setMaximumWidth(130)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.percent)
        layout.addWidget(raw)
        raw.textChanged.connect(self.refresh)
        self.slider.valueChanged.connect(lambda value: raw.setText(format(value*maximum/100, '.12g')))
        self.refresh()

    def refresh(self, *_):
        try:
            value = float(self.raw.text()) / self.maximum * 100
            valid = math.isfinite(value) and 0 <= value <= 100
        except ValueError:
            valid = False
        self.slider.setEnabled(valid)
        self.percent.setText(format(value, '.5g')+'%' if valid else '自定义')
        if valid:
            blocked = QSignalBlocker(self.slider)
            self.slider.setValue(round(value))
            blocked.unblock()


class ChoiceField(QComboBox):
    """Keep variables, legacy numbers and values outside the suggestion list editable."""
    def __init__(self, raw, choices, parent=None):
        super().__init__(parent)
        self.raw = raw
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        for title, value in choices:
            self.addItem(title, str(value))
        raw.setParent(self)
        raw.hide()
        self.setMinimumHeight(32)
        self.refresh()
        self.currentTextChanged.connect(self.apply_text)
        raw.textChanged.connect(self.refresh)

    def refresh(self, *_):
        value = self.raw.text()
        index = self.findData(value)
        blocked = QSignalBlocker(self)
        self.setCurrentIndex(index)
        if index < 0:
            self.setEditText(value)
        blocked.unblock()

    def apply_text(self, text):
        index = self.findText(text)
        self.raw.setText(self.itemData(index) if index >= 0 else text)


class KeyField(ChoiceField):
    def __init__(self, raw, virtual, parent=None):
        from background_runtime import BackgroundInput
        self.virtual = virtual
        names = ('enter', 'tab', 'space', 'esc', 'backspace', 'delete',
                 'up', 'down', 'left', 'right', 'ctrl', 'shift', 'alt',
                 'home', 'end', 'pageup', 'pagedown') + tuple('f'+str(i) for i in range(1, 13)) + tuple('abcdefghijklmnopqrstuvwxyz0123456789')
        super().__init__(raw, [(key, BackgroundInput._key(key) if virtual else key) for key in names], parent)
        self.lineEdit().setPlaceholderText('选择或输入单个按键；支持变量')

    def apply_text(self, text):
        from background_runtime import BackgroundInput
        if self.virtual and self.findText(text) < 0 and not any(v in text for v in ('{{', '☾')):
            try:
                value = str(BackgroundInput._key(text))
            except ValueError:
                value = text
            self.raw.setText(value)
        else:
            super().apply_text(text)

    def apply_capture(self, text):
        from background_runtime import BackgroundInput
        # Single backend key operations must never silently discard a chord.
        if '+' in text:
            raise ValueError('此操作只接收单个按键；组合键请在绑定后使用“按下键盘”指令。')
        code = BackgroundInput._key(text)
        self.raw.setText(str(code) if self.virtual else text)


def capture_key(editor, field):
    owner = getattr(editor.context, 'metadata', {}).get('main_window')
    if owner is None:
        owner = editor.parentWidget()
        while owner is not None and not hasattr(owner, 'unregister_global_shortcut_keys'):
            owner = owner.parentWidget()
    thread = getattr(owner, 'command_thread', None)
    if thread is not None and thread.isRunning():
        QMessageBox.information(editor, '请先停止任务', '运行时不能捕获按键，请先停止任务。')
        return
    dialog = KeyCaptureDialog(editor)
    suspended = False
    try:
        if owner is not None and hasattr(owner, 'unregister_global_shortcut_keys'):
            owner.unregister_global_shortcut_keys()
            suspended = True
        if dialog.exec() == QDialog.Accepted and dialog.value:
            try:
                field.apply_capture(dialog.value)
            except ValueError as error:
                QMessageBox.warning(editor, '按键不适用', str(error))
    finally:
        dialog.deleteLater()
        if suspended:
            owner.register_global_shortcut_keys()


class TextField(QWidget):
    def __init__(self, raw, parent=None):
        super().__init__(parent)
        self.raw = raw
        raw.setParent(self)
        raw.hide()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.editor = PasteTextEdit(self)
        self.editor.setObjectName('backgroundInputText')
        self.editor.setMinimumHeight(100)
        self.editor.setMaximumHeight(180)
        self.editor.setPlaceholderText('输入内容；支持多行文字和 {{变量名}}')
        self.editor.setPlainText(raw.text())
        self.editor.paste_status = QLabel('', self)
        self.editor.paste_status.setWordWrap(True)
        self.paste_button = QPushButton('粘贴文本', self)
        self.paste_button.setAutoDefault(False)
        self.paste_button.clicked.connect(self.editor.paste)
        for widget in (self.editor, self.paste_button, self.editor.paste_status):
            layout.addWidget(widget)
        self.editor.textChanged.connect(lambda: raw.setText(self.editor.toPlainText()))
        raw.textChanged.connect(self.refresh)

    def refresh(self, text):
        if text != self.editor.toPlainText():
            blocked = QSignalBlocker(self.editor)
            self.editor.setPlainText(text)
            blocked.unblock()
