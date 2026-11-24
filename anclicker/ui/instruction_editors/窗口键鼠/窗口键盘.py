from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口键盘.schema import FIELDS, OPERATIONS
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtGui import QKeySequence
from anclicker.platform.qt_compat.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit


class KeyCapture(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('读取按键')
        self.codes, self.names, self.held = [], [], set()
        layout = QVBoxLayout(self)
        self.hint = QLabel('请按下单键或组合键，全部松开后自动读取。')
        layout.addWidget(self.hint)
        cancel = QPushButton('取消读取')
        cancel.setFocusPolicy(Qt.NoFocus)
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)
        self.setFocusPolicy(Qt.StrongFocus)

    def event(self, event):
        # Consume Tab, Escape and shortcuts instead of moving focus/closing.
        if event.type() in (event.KeyPress, event.KeyRelease, event.ShortcutOverride):
            if event.type() == event.ShortcutOverride:
                event.accept()
            elif event.type() == event.KeyPress:
                self.keyPressEvent(event)
            else:
                self.keyReleaseEvent(event)
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        code = int(event.nativeVirtualKey())
        if not 1 <= code <= 255 or code == 231:
            self.hint.setText('未读取到实体按键，请关闭输入法后重试；文字可使用输入内容。')
            return
        self.held.add(code)
        if code not in self.codes:
            self.codes.append(code)
            self.names.append(QKeySequence(event.key()).toString() or ('VK ' + str(code)))
        self.hint.setText(' + '.join(self.names))

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        self.held.discard(int(event.nativeVirtualKey()))
        if self.codes and not self.held:
            self.accept()


class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口键盘'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
    DEFAULT_OPERATION = OPERATIONS[0]

    def __init__(self, *args, **kwargs):
        self.recorded_codes = []
        super().__init__(*args, **kwargs)
        self.record_button = QPushButton('读取按键 / 组合键')
        self.record_button.setAutoDefault(False)
        self.record_button.clicked.connect(self.capture_keys)
        self.content = QPlainTextEdit()
        self.content.setPlaceholderText('输入文字，支持中文、多行及 {{变量名}}')
        self.content.setMinimumHeight(100)
        self.layout().insertWidget(3, self.record_button)
        self.layout().insertWidget(4, self.content)
        self.keys.addItems([chr(code) for code in range(ord('a'), ord('z') + 1)] +
                           [str(number) for number in range(10)] +
                           ['f' + str(number) for number in range(1, 25)] +
                           ['space', 'backspace', 'delete', 'insert', 'home', 'end', 'pageup', 'pagedown',
                            'up', 'down', 'left', 'right', 'shift', 'ctrl', 'alt', 'win', 'printscreen', 'capslock', 'numlock'])
        self.keys.setToolTip('可读取实体按键，也可输入 ctrl+shift+s 或 win32:96（小键盘 0）。')
        self.keys.editTextChanged.connect(self.clear_recording)
        self.load_draft(kwargs.get('draft') or (args[1] if len(args) > 1 else None) or self.get_draft())

    def clear_recording(self, *_):
        self.recorded_codes = []

    def capture_keys(self):
        dialog = KeyCapture(self)
        if dialog.exec() == QDialog.Accepted:
            self.keys.setCurrentText(' + '.join(dialog.names))
            self.recorded_codes = list(dialog.codes)
        dialog.deleteLater()

    def update_fields(self, *_):
        super().update_fields()
        for widgets in self.rows.values():
            for widget in widgets:
                widget.setVisible(widgets is self.rows['按键'] and self.operation.currentText() == '组合键')
        self.pick_start.hide()
        self.pick_end.hide()
        if hasattr(self, 'content'):
            text_mode = self.operation.currentText() == '输入内容'
            self.content.setVisible(text_mode)
            self.record_button.setVisible(not text_mode)

    def load_draft(self, draft):
        super().load_draft(draft)
        from anclicker.domain.instructions import InstructionDraft
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        if hasattr(self, 'content'):
            self.content.setPlainText(str(draft.parameters.get('内容', '')))
        self.recorded_codes = list(draft.parameters.get('按键码') or [])
        self.update_fields()

    def get_draft(self):
        draft = super().get_draft()
        if self.operation.currentText() == '输入内容':
            binding = {key:draft.parameters[key] for key in ('绑定方案','图像模式','鼠标模式','键盘模式','绑定模式','绑定等待') if key in draft.parameters}
            draft.parameters = {**binding, '窗口': dict(self.target), '模式': self.mode.currentText(), '操作': '输入内容',
                                '内容': self.content.toPlainText() if hasattr(self, 'content') else ''}
        elif self.recorded_codes:
            draft.parameters['按键码'] = list(self.recorded_codes)
        return draft
