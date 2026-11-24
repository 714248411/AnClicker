from anclicker.ui.instruction_editors.窗口键鼠.窗口键盘 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口文本输入.schema import FIELDS, OPERATIONS

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口文本输入'
    DEFAULT_OPERATION = '输入内容'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS

    def update_fields(self, *_):
        super().update_fields()
        for key in ('X','Y'):
            for widget in self.rows[key]: widget.show()
        self.pick_start.setText('点选输入位置')
        self.pick_start.show()
        self.pick_start.setEnabled(bool(self.target))

    def get_draft(self):
        draft = super().get_draft()
        draft.parameters.update({'X':self.fields['X'].value(), 'Y':self.fields['Y'].value()})
        return draft
