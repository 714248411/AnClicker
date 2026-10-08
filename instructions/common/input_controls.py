"""Focused key capture and text-only clipboard compatibility for editors."""
import sys

from qt_compat.QtCore import QEvent, Qt
from qt_compat.QtGui import QKeySequence, QTextDocument
from qt_compat.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QLabel, QMenu,
    QPlainTextEdit, QVBoxLayout, QWidget,
)


def event_key_name(event):
    key = event.key()
    names = {
        Qt.Key.Key_Control: 'command' if sys.platform == 'darwin' else 'ctrl', Qt.Key.Key_Shift: 'shift',
        Qt.Key.Key_Alt: 'alt', Qt.Key.Key_Meta: 'ctrl' if sys.platform == 'darwin' else 'win',
        Qt.Key.Key_AltGr: 'altright', Qt.Key.Key_Return: 'enter', Qt.Key.Key_Enter: 'enter',
        Qt.Key.Key_Escape: 'esc', Qt.Key.Key_Tab: 'tab', Qt.Key.Key_Backtab: 'tab',
        Qt.Key.Key_Backspace: 'backspace', Qt.Key.Key_Delete: 'delete',
        Qt.Key.Key_Insert: 'insert', Qt.Key.Key_Home: 'home', Qt.Key.Key_End: 'end',
        Qt.Key.Key_PageUp: 'pageup', Qt.Key.Key_PageDown: 'pagedown',
        Qt.Key.Key_Left: 'left', Qt.Key.Key_Right: 'right', Qt.Key.Key_Up: 'up', Qt.Key.Key_Down: 'down',
        Qt.Key.Key_Space: 'space', Qt.Key.Key_CapsLock: 'capslock',
        Qt.Key.Key_NumLock: 'numlock', Qt.Key.Key_ScrollLock: 'scrolllock',
        Qt.Key.Key_Print: 'printscreen', Qt.Key.Key_Pause: 'pause', Qt.Key.Key_Menu: 'apps',
        Qt.Key.Key_VolumeUp: 'volumeup', Qt.Key.Key_VolumeDown: 'volumedown',
        Qt.Key.Key_VolumeMute: 'volumemute', Qt.Key.Key_MediaPlay: 'playpause',
        Qt.Key.Key_MediaStop: 'stop', Qt.Key.Key_MediaNext: 'nexttrack', Qt.Key.Key_MediaPrevious: 'prevtrack',
    }
    if key in names:
        return names[key]
    if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        return 'f' + str(key - Qt.Key.Key_F1 + 1)
    if event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
        keypad = {Qt.Key.Key_Plus: 'add', Qt.Key.Key_Minus: 'subtract', Qt.Key.Key_Asterisk: 'multiply',
                  Qt.Key.Key_Slash: 'divide', Qt.Key.Key_Period: 'decimal'}
        if key in keypad:
            return keypad[key]
    if 32 <= key <= 126:
        return chr(key).lower()
    return None


class KeyCaptureDialog(QDialog):
    """No global listener: capture only while this modal window has focus."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = ''
        self.setWindowTitle('捕获键盘按键')
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        label = QLabel('请按下单键或组合键，然后用鼠标点击“使用此按键”。\n'
                       'Esc、Tab、Enter 也会被记录；取消请点击按钮。\n'
                       '系统保留组合键（如 Alt+Tab）和硬件 Fn 可能无法捕获。', self)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.preview = QLabel('等待按键…', self)
        self.preview.setMinimumHeight(48)
        layout.addWidget(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.use_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.use_button.setText('使用此按键')
        self.use_button.setEnabled(False)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if not isinstance(watched, QWidget) or (watched is not self and not self.isAncestorOf(watched)):
            return False
        if not self.isVisible():
            return False
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyRelease:
            return True
        if event.type() != QEvent.Type.KeyPress:
            return False
        if event.isAutoRepeat():
            return True
        name = event_key_name(event)
        if name is None:
            self.value = ''
            self.preview.setText('暂不支持此按键，请换一个按键或取消后手动输入。')
            self.use_button.setEnabled(False)
            return True
        modifiers = event.modifiers()
        keys = []
        # Qt swaps Control/Meta semantics on macOS; keep physical backend names.
        control = 'command' if sys.platform == 'darwin' else 'ctrl'
        meta = 'ctrl' if sys.platform == 'darwin' else 'win'
        for flag, text in ((Qt.KeyboardModifier.ControlModifier, control),
                           (Qt.KeyboardModifier.AltModifier, 'alt'),
                           (Qt.KeyboardModifier.ShiftModifier, 'shift'),
                           (Qt.KeyboardModifier.MetaModifier, meta)):
            if modifiers & flag and text != name:
                keys.append(text)
        # '+' is the persisted chord separator; express the US-layout plus key
        # as Shift+=. Keypad plus has its own unambiguous 'add' name.
        if name == '+':
            if 'shift' not in keys:
                keys.append('shift')
            name = '='
        keys.append(name)
        self.value = '+'.join(keys)
        self.preview.setText(self.value)
        self.use_button.setEnabled(True)
        return True


def clipboard_text():
    """Read on explicit paste only; do not poll or replace clipboard contents."""
    clipboard = QApplication.clipboard()
    mime = clipboard.mimeData()
    if mime is not None:
        if mime.hasText():
            value = mime.text()
            if value:
                return value
        if mime.hasHtml():
            document = QTextDocument()
            document.setHtml(mime.html())
            value = document.toPlainText()
            if value:
                return value
    # Qt can have stale/delayed native MIME metadata (e.g. external apps/RDP).
    # On Windows use the existing native Unicode-text clipboard backend.
    if sys.platform == 'win32':
        try:
            import pyperclip
            value = pyperclip.paste()
            if isinstance(value, str):
                return value
        except Exception:
            pass
    return ''


class PasteTextEdit(QPlainTextEdit):
    def paste(self):
        if self.isReadOnly():
            return
        value = clipboard_text()
        if value:
            self.insertPlainText(value)
            self.setToolTip('')
        else:
            self.setToolTip('剪贴板中没有可读取的文本。请先复制文字；图片不能直接粘贴为文字。')
        if getattr(self, 'paste_status', None) is not None:
            self.paste_status.setText('已粘贴文本' if value else self.toolTip())

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        for title, callback, enabled in (
            ('撤销', self.undo, self.document().isUndoAvailable()),
            ('重做', self.redo, self.document().isRedoAvailable()),
            ('剪切', self.cut, self.textCursor().hasSelection() and not self.isReadOnly()),
            ('复制', self.copy, self.textCursor().hasSelection()),
            ('粘贴文本', self.paste, not self.isReadOnly()),
            ('全选', self.selectAll, bool(self.toPlainText())),
        ):
            action = menu.addAction(title, callback)
            action.setEnabled(enabled)
        menu.exec(event.globalPos())
        menu.deleteLater()
