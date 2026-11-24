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
DEFAULT_ENABLED = {'新建空白页', '保存', '另存为 Excel', '显示工具栏', '中文编程提示'}


def install_all_menu_shortcuts(window):
    actions = dict(window._view_shortcut_actions)
    def collect(menu):
        for action in menu.actions():
            if action.isSeparator() or action.menu() is getattr(window, 'menuzv', None):
                continue
            label = (action.property('compactFullText') or action.text()).split('\t')[0].replace('&', '').strip()
            if action is window.action_new_blank: label = '新建空白页'
            elif action is window.actionx: label = '保存'
            elif action is window.actiona: label = '另存为 Excel'
            if label and action not in actions.values():
                actions[label] = action
            if action.menu() is not None:
                collect(action.menu())
    collect(window.menu)
    collect(window.menu_4)
    window._view_shortcut_actions = actions
    install_view_shortcuts(window, window.menu_4, actions)



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
    if isinstance(saved, dict):
        for old, new in {'导入指令': '导入单文件', '导入文件夹内所有表格文件…': '导入文件夹…',
                         '导入整体数据…': '导入项目…'}.items():
            if old in saved and new not in saved:
                saved[new] = saved[old]
    for name, action in actions.items():
        value = saved.get(name, defaults[name]) if isinstance(saved, dict) else defaults[name]
        if isinstance(value, dict):
            key = value.get('key', defaults[name])
            enabled = value.get('enabled', name in DEFAULT_ENABLED) is not False
        else:
            key = value if isinstance(value, str) else defaults[name]
            enabled = name in DEFAULT_ENABLED
        if not isinstance(key, str):
            key = defaults[name]
        action.setProperty('configuredShortcut', key)
        action.setProperty('shortcutEnabled', enabled)
        action.setShortcut(QKeySequence(key) if enabled else QKeySequence())
    window.open_view_shortcut_settings = lambda parent=None: edit_view_shortcuts(
        window, actions, defaults, dialog_parent=parent)
    edit = QAction('快捷键设置', menu)
    entries = menu.actions()
    advanced = next((action for action in entries if action.objectName() == 'advancedExecutionTiming'), None)
    index = entries.index(advanced) + 1 if advanced is not None else len(entries)
    menu.insertAction(entries[index] if index < len(entries) else None, edit)
    edit.triggered.connect(lambda: window.open_view_shortcut_settings())


def edit_view_shortcuts(window, actions, defaults, dialog_parent=None):
    dialog = QDialog(dialog_parent if dialog_parent is not None else window)
    dialog.setWindowTitle('快捷键设置')
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
        enabled.setObjectName('shortcutEnabled_' + name)
        enabled.setChecked(action.property('shortcutEnabled') is not False)
        enabled_boxes[name] = enabled
        row_layout.addWidget(enabled)
        entry = ShortcutInput(action.property('configuredShortcut') or '', row)
        entry.setObjectName('shortcutInput_' + name)
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
            enabled_boxes[name].setChecked(name in DEFAULT_ENABLED)
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


def active_shortcut_help(window):
    """Only advertise enabled, configured menu shortcuts and registered globals."""
    rows = []
    for name, action in getattr(window, '_view_shortcut_actions', {}).items():
        if action.isEnabled() and not action.shortcut().isEmpty():
            rows.append((action.shortcut().toString(QKeySequence.SequenceFormat.NativeText), name + '（主窗口）'))
    for name, key in getattr(window, '_registered_shortcut_help', {}).items():
        rows.append((QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText), name + '（全局）'))
    return rows
