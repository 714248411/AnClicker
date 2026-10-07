import importlib
import os
import sys
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtCore import QMimeData, Qt, QTimer
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog
from instructions.common.input_controls import KeyCaptureDialog, PasteTextEdit, clipboard_text
from instructions.models import InstructionDraft
from test.test_hidden_stop import host


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize('key,mods,expected', [
    (Qt.Key.Key_W, Qt.KeyboardModifier.ControlModifier, 'command+w' if sys.platform == 'darwin' else 'ctrl+w'),
    (Qt.Key.Key_F10, Qt.KeyboardModifier.NoModifier, 'f10'),
    (Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier, 'esc'),
    (Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier, 'tab'),
    (Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier, 'enter'),
    (Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier, 'delete'),
    (Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier, 'shift+left'),
    (Qt.Key.Key_Plus, Qt.KeyboardModifier.NoModifier, 'shift+='),
    (Qt.Key.Key_Plus, Qt.KeyboardModifier.KeypadModifier, 'add'),
])
def test_physical_key_capture_does_not_activate_dialog_buttons(app, key, mods, expected):
    dialog = KeyCaptureDialog()
    dialog.show()
    app.processEvents()
    QTest.keyClick(dialog, key, mods)
    assert dialog.value == expected
    assert dialog.isVisible()
    assert dialog.use_button.isEnabled()
    dialog.reject()
    dialog.deleteLater()


def test_capture_dialog_keeps_last_chord_after_releases(app):
    dialog = KeyCaptureDialog()
    dialog.show()
    QTest.keyClick(dialog.use_button, Qt.Key.Key_A, Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier)
    assert dialog.value == 'alt+shift+a'
    dialog.reject()
    dialog.deleteLater()


def test_keyboard_presets_and_manual_duration_roundtrip(app):
    cls = importlib.import_module('instructions.键鼠.按下键盘.按下键盘').InstructionEditor
    dialog = cls(draft=InstructionDraft('按下键盘', {'按键': 'ctrl+w', '按压时长': 37}))
    assert dialog.get_draft().parameters['按压时长'] == 37
    for value in (5, 10, 20, 30, 50, 100):
        index = dialog.duration_presets.findData(value)
        assert index >= 0
        dialog.apply_duration_preset(index)
        assert dialog.get_draft().parameters['按压时长'] == value
    dialog._controls['按压时长'].setValue(123)
    assert dialog.get_draft().parameters['按压时长'] == 123
    assert dialog.get_draft().parameters['按键'] == 'ctrl+w'
    dialog.deleteLater()


def test_capture_button_applies_and_cancel_keeps_existing_value(app):
    cls = importlib.import_module('instructions.键鼠.按下键盘.按下键盘').InstructionEditor
    editor = cls()
    def capture():
        dialog = QApplication.activeModalWidget()
        QTest.keyClick(dialog, Qt.Key.Key_F8)
        dialog.accept()
    QTimer.singleShot(30, capture)
    editor.capture_keys()
    assert editor._controls['按键'].text() == 'f8'
    QTimer.singleShot(30, lambda: QApplication.activeModalWidget().reject())
    editor.capture_keys()
    assert editor._controls['按键'].text() == 'f8'
    editor.deleteLater()


def test_text_paste_keyboard_and_context_menu_preserve_unicode_and_newlines(app):
    cls = importlib.import_module('instructions.键鼠.文本输入.文本输入').InstructionEditor
    editor = cls()
    editor.show()
    control = editor._controls['内容']
    text = '中文与 emoji 🙂\n第二行\tvalue'
    QApplication.clipboard().setText(text)
    QTest.keyClick(control, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    assert editor.get_draft().parameters['内容'] == text
    control.selectAll()
    def select_paste():
        menu = QApplication.activePopupWidget()
        next(a for a in menu.actions() if a.text() == '粘贴文本').trigger()
        menu.close()
    QTimer.singleShot(20, select_paste)
    pos = control.rect().center()
    control.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos, control.mapToGlobal(pos)))
    assert control.toPlainText() == text
    control.undo()
    editor.close()
    editor.deleteLater()
    QApplication.clipboard().clear()


def test_html_only_clipboard_becomes_plain_text(app):
    mime = QMimeData()
    mime.setHtml('<p>第一行</p><p><b>第二行</b></p>')
    QApplication.clipboard().setMimeData(mime)
    assert clipboard_text() == '第一行\n第二行'
    QApplication.clipboard().clear()


def test_native_clipboard_fallback_and_empty_feedback(app):
    QApplication.clipboard().clear()
    with patch('instructions.common.input_controls.sys.platform', 'win32'), patch('pyperclip.paste', return_value='外部程序文字'):
        assert clipboard_text() == '外部程序文字'
    editor = PasteTextEdit()
    editor.setPlainText('保留')
    with patch('instructions.common.input_controls.clipboard_text', return_value=''):
        editor.paste()
    assert editor.toPlainText() == '保留'
    assert '没有可读取的文本' in editor.toolTip()
    editor.deleteLater()


def test_capture_temporarily_unregisters_and_restores_app_hotkeys(host):
    cls = importlib.import_module('instructions.键鼠.按下键盘.按下键盘').InstructionEditor
    editor = cls(parent=host)
    before = set(host.hk_stop.callbacks)
    observations = []
    def capture():
        observations.append(set(host.hk_stop.callbacks))
        dialog = QApplication.activeModalWidget()
        QTest.keyClick(dialog, Qt.Key.Key_F10)
        dialog.accept()
    QTimer.singleShot(30, capture)
    editor.capture_keys()
    assert observations == [set()]
    assert set(host.hk_stop.callbacks) == before
    assert not host.command_thread.isRunning()
    assert editor._controls['按键'].text() == 'f10'
    editor.deleteLater()
