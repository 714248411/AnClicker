from anclicker.platform.qt_compat.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QLineEdit, QLabel, QDialogButtonBox, QMessageBox)
from anclicker.domain.instruction_interfaces import InstructionEditorInterface
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import validate_parameters
from anclicker.instructions.流程.折叠步骤.schema import FIELDS


class InstructionEditor(QDialog, InstructionEditorInterface):
    TYPE_ID = '折叠步骤'
    DISPLAY_NAME = '折叠以下指令'
    FIELDS = FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent)
        self.setWindowTitle(self.DISPLAY_NAME)
        self.resize(440, 270)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.by_count = QCheckBox('折叠下方条数')
        self.count = QSpinBox()
        self.count.setRange(1, 1000000)
        self.count.setSuffix(' 条')
        self.by_range = QCheckBox('从下一步折叠至')
        self.ranges = QSpinBox()
        self.ranges.setRange(1, 1000000)
        self.ranges.setPrefix('第 ')
        self.ranges.setSuffix(' 步')
        self.collapsed = QCheckBox('折叠（取消勾选则展开）')
        self.note = QLineEdit()
        form.addRow(self.by_count, self.count)
        form.addRow(self.by_range, self.ranges)
        form.addRow(self.collapsed)
        form.addRow('备注', self.note)
        layout.addLayout(form)
        hint = QLabel('可勾选一种或同时勾选两种方法，同时勾选取并集。\n'
                      '范围从本指令下一行开始，连续折叠至指定步骤。\n'
                      '范围内插入、删除时自动增减，末尾跟随原指令。\n'
                      '折叠仅影响显示，步骤仍正常执行。右键可折叠/展开，双击设置。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.by_count.toggled.connect(self.count.setEnabled)
        self.by_range.toggled.connect(self.ranges.setEnabled)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def load_draft(self, draft):
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        p = draft.parameters
        self.by_count.setChecked(bool(p.get('按条数', True)))
        self.count.setValue(int(p.get('下方条数', 1)))
        self.by_range.setChecked(bool(p.get('按范围', False)))
        from anclicker.domain.step_folding import parse_ranges
        try:
            end = int(p['终止步骤']) if '终止步骤' in p else max(b for a, b in parse_ranges(p.get('步骤范围', '7-9')))
        except (ValueError, TypeError):
            end = 1
        self.ranges.setValue(end)
        self.collapsed.setChecked(bool(p.get('已折叠', True)))
        self.note.setText(draft.note)
        self.count.setEnabled(self.by_count.isChecked())
        self.ranges.setEnabled(self.by_range.isChecked())
        self.error_policy = draft.error_policy
        self.group_locked = bool(p.get('整体锁定', False))

    def get_draft(self):
        p = {'按条数': self.by_count.isChecked(), '下方条数': self.count.value(),
             '按范围': self.by_range.isChecked(), '终止步骤': self.ranges.value(), '动态范围': True,
             '已折叠': self.collapsed.isChecked(), '整体锁定': self.group_locked}
        validate_parameters(p)
        return InstructionDraft(self.TYPE_ID, p, error_policy=self.error_policy, note=self.note.text())

    def accept(self):
        try:
            self.get_draft()
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, '折叠设置', str(error))
            return
        super().accept()
