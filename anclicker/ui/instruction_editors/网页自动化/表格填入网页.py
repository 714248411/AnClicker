from anclicker.ui.instruction_editors.rpa_instruction import RpaInstructionEditor
from anclicker.ui.generated.instructions.Excel.打开Excel.打开Excel_ui import Ui_InstructionEditor as BaseUi
from anclicker.platform.qt_compat.QtWidgets import QLineEdit,QComboBox,QLabel
from anclicker.instructions.网页自动化.表格填入网页.schema import FIELDS
class FillUi(BaseUi):
 def setupUi(self,dialog):
  super().setupUi(dialog)
  form=self.parameterFormLayout
  while form.rowCount():form.removeRow(0)
  self.titleLabel.setText('表格填入网页')
  for i,field in enumerate(FIELDS):
   control=QComboBox(dialog) if field.kind=='choice' else QLineEdit(dialog)
   if field.kind=='choice':control.addItems(list(field.choices));control.setCurrentText(field.default)
   else:control.setText(field.default)
   setattr(self,'parameter_'+str(i),control)
   if hasattr(self,'auxiliary_'+str(i)):delattr(self,'auxiliary_'+str(i))
   label=QLabel(field.label,dialog);setattr(self,'label_'+str(i),label);form.addRow(label,control)
class InstructionEditor(RpaInstructionEditor):
 TYPE_ID='表格填入网页'
 DISPLAY_NAME='表格填入网页'
 COMMAND_ID='excelFillWeb'
 UI_CLASS=FillUi
 FIELDS=FIELDS
