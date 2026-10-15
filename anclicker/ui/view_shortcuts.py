"""Editable shortcuts for the View menu (active in the main window)."""
import json
from anclicker.platform.qt_compat.QtCore import QEvent, Qt
from anclicker.platform.qt_compat.QtGui import QAction, QKeySequence
from anclicker.platform.qt_compat.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QDialogButtonBox, QMessageBox, QWidget, QScrollArea, QCheckBox,
)

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'apply_settings_theme': ('from', 'anclicker.ui.settings_theme', ('apply_settings_theme',), 0),
})


SETTING = '视图快捷键'


class ShortcutInput(QLineEdit):
    def __init__(self, sequence, parent=None):
        super().__init__(parent)
        self.sequence = QKeySequence(sequence)
        self.setReadOnly(True)
        self.setPlaceholderText('点击后按键；可用单键或组合键')
        self.setText(self.sequence.toString(QKeySequence.SequenceFormat.NativeText))

    def event(self, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key not in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_unknown):
                modifiers = event.modifiers()
                value = modifiers.value if hasattr(modifiers, 'value') else int(modifiers)
                self.sequence = QKeySequence(value | int(key))
                self.setText(self.sequence.toString(QKeySequence.SequenceFormat.NativeText))
            event.accept()
            return True
        return super().event(event)

    def clear_sequence(self):
        self.sequence = QKeySequence()
        self.clear()


def install_view_shortcuts(window, menu, actions):
    defaults = {name: action.shortcut().toString(QKeySequence.SequenceFormat.PortableText)
                for name, action in actions.items()}
    try:
        saved = json.loads(window.db.get_setting_value(SETTING) or '{}')
    except (ValueError, TypeError):
        saved = {}
    for name, action in actions.items():
        value = saved.get(name, defaults[name]) if isinstance(saved, dict) else defaults[name]
        if isinstance(value, dict):
            key = value.get('key', defaults[name])
            enabled = value.get('enabled', True) is not False
        else:
            key = value if isinstance(value, str) else defaults[name]
            enabled = True
        if not isinstance(key, str):
            key = defaults[name]
        action.setProperty('configuredShortcut', key)
        action.setProperty('shortcutEnabled', enabled)
        action.setShortcut(QKeySequence(key) if enabled else QKeySequence())
    window.open_view_shortcut_settings = lambda parent=None: edit_view_shortcuts(
        window, actions, defaults, dialog_parent=parent)
    edit = menu.addAction('快捷键设置…')
    edit.triggered.connect(lambda: window.open_view_shortcut_settings())


def edit_view_shortcuts(window, actions, defaults, dialog_parent=None):
    dialog = QDialog(dialog_parent if dialog_parent is not None else window)
    dialog.setWindowTitle('视图快捷键设置')
    dialog.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    dialog.resize(600, 480)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(10)
    hint = QLabel('点击输入框后按下任意单键或组合键。取消勾选可停用并保留按键，清除可移除按键。\n快捷键在主窗口使用。', dialog)
    hint.setWordWrap(True)
    hint.setObjectName('settingsHint')
    layout.addWidget(hint)
    body = QWidget(dialog)
    body.setObjectName('settingsBody')
    form = QFormLayout(body)
    form.setContentsMargins(8, 8, 8, 8)
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(6)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    inputs = {}
    enabled_boxes = {}
    for name, action in actions.items():
        row = QWidget(body)
        row.setObjectName('settingsRow')
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        enabled = QCheckBox('启用', row)
        enabled.setChecked(action.property('shortcutEnabled') is not False)
        enabled_boxes[name] = enabled
        row_layout.addWidget(enabled)
        entry = ShortcutInput(action.property('configuredShortcut') or '', row)
        inputs[name] = entry
        row_layout.addWidget(entry, 1)
        clear = QPushButton('清除', row)
        clear.clicked.connect(entry.clear_sequence)
        row_layout.addWidget(clear)
        label = QLabel(name, body)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setBuddy(entry)
        form.addRow(label, row)
    scroll = QScrollArea(dialog)
    scroll.setObjectName('settingsScroll')
    scroll.viewport().setObjectName('settingsViewport')
    scroll.setWidgetResizable(True)
    scroll.setWidget(body)
    layout.addWidget(scroll)
    restore = QPushButton('恢复默认快捷键', dialog)
    layout.addWidget(restore)

    def reset():
        for name, entry in inputs.items():
            enabled_boxes[name].setChecked(True)
            entry.sequence = QKeySequence(defaults[name])
            entry.setText(entry.sequence.toString(QKeySequence.SequenceFormat.NativeText))
    restore.clicked.connect(reset)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.button(QDialogButtonBox.StandardButton.Save).setText('保存')
    buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName('settingsSave')
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
    layout.addWidget(buttons)
    buttons.rejected.connect(dialog.reject)

    def save():
        proposed = {name: entry.sequence for name, entry in inputs.items()}
        occupied = []
        for action in window.findChildren(QAction):
            if action not in actions.values():
                occupied.extend((action.text().replace('&', ''), sequence) for sequence in action.shortcuts()
                                if not sequence.isEmpty())
        # Include globally registered run/stop/pause shortcuts as well.
        for name, keys in (window.db.get_global_shortcut() or {}).items():
            if isinstance(keys, (list, tuple)):
                sequence = QKeySequence('+'.join('Ctrl' if str(k).lower() == 'control' else str(k) for k in keys))
                if not sequence.isEmpty():
                    occupied.append((name, sequence))
        for name, sequence in proposed.items():
            if sequence.isEmpty() or not enabled_boxes[name].isChecked():
                continue
            for other_name, other in occupied:
                if (sequence.matches(other) != QKeySequence.SequenceMatch.NoMatch or
                        other.matches(sequence) != QKeySequence.SequenceMatch.NoMatch):
                    notice = QMessageBox(QMessageBox.Icon.Warning, '快捷键冲突',
                                         f'“{name}”与“{other_name}”的快捷键冲突，请更换或清除。',
                                         QMessageBox.StandardButton.Ok, dialog)
                    notice.button(QMessageBox.StandardButton.Ok).setText('确定')
                    notice.exec()
                    return
            occupied.append((name, sequence))
        window.db.set_setting_value(SETTING, json.dumps(
            {name: {'key': seq.toString(QKeySequence.SequenceFormat.PortableText),
                    'enabled': enabled_boxes[name].isChecked()} for name, seq in proposed.items()},
            ensure_ascii=False))
        for name, sequence in proposed.items():
            enabled = enabled_boxes[name].isChecked()
            actions[name].setProperty('configuredShortcut', sequence.toString(QKeySequence.SequenceFormat.PortableText))
            actions[name].setProperty('shortcutEnabled', enabled)
            actions[name].setShortcut(sequence if enabled else QKeySequence())
        dialog.accept()

    buttons.accepted.connect(save)
    apply_settings_theme = _module_imports.load('apply_settings_theme')
    apply_settings_theme(dialog, window)
    dialog.exec()
