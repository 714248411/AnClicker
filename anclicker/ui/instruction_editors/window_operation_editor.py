from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.domain.instructions import InstructionDraft
from anclicker.platform.qt_compat.QtWidgets import QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit

class WindowOperationEditor(BaseEditor):
    EXTRA_FIELDS = ()

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=None, context=context)
        self.extra = {}
        form = QFormLayout()
        for field in self.EXTRA_FIELDS:
            if field.kind == 'choice':
                widget = QComboBox()
                widget.addItems(field.choices)
            elif field.kind in ('int','float'):
                widget = QSpinBox() if field.kind == 'int' else QDoubleSpinBox()
                widget.setRange(field.minimum, field.maximum)
            else:
                widget = QLineEdit()
            self.extra[field.key] = widget
            form.addRow(field.label + ':', widget)
        self.layout().insertLayout(3, form)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def update_fields(self, *_):
        super().update_fields()
        if self.TYPE_ID == '窗口悬停后点击':
            for key in ('结束X','结束Y'):
                for widget in self.rows[key]: widget.show()
            self.pick_start.setText('点选悬停位置')
            self.pick_end.setText('点选点击位置')
            self.pick_end.show()
        elif self.TYPE_ID == '窗口OCR点击':
            for widgets in self.rows.values():
                for widget in widgets: widget.hide()
            self.pick_start.hide()
            self.pick_end.hide()

    def load_draft(self, draft):
        super().load_draft(draft)
        if not hasattr(self, 'extra'): return
        draft = draft if isinstance(draft,InstructionDraft) else InstructionDraft.from_mapping(draft)
        for field in self.EXTRA_FIELDS:
            value = draft.parameters.get(field.key,field.default)
            widget = self.extra[field.key]
            if field.kind == 'choice': widget.setCurrentText(str(value))
            elif field.kind in ('int','float'): widget.setValue(value)
            else: widget.setText(str(value))

    def get_draft(self):
        draft = super().get_draft()
        for field in self.EXTRA_FIELDS:
            widget = self.extra[field.key]
            draft.parameters[field.key] = (widget.currentText() if field.kind == 'choice' else
                widget.value() if field.kind in ('int','float') else widget.text())
        if self.TYPE_ID == '窗口悬停后点击':
            for key in ('结束X','结束Y'): draft.parameters[key] = self.fields[key].value()
        if self.TYPE_ID == '窗口OCR点击':
            draft.parameters.pop('X',None)
            draft.parameters.pop('Y',None)
        return draft
