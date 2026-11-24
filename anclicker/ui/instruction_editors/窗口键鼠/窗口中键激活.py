from anclicker.platform.qt_compat.QtCore import Signal
from anclicker.ui.instruction_editors.window_settings_footer import add_window_footer
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QDialogButtonBox,QSpinBox)
from anclicker.domain.instruction_interfaces import InstructionEditorInterface
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_editors.窗口键鼠.窗口键盘 import KeyCapture
from anclicker.instructions.窗口键鼠.窗口中键激活.schema import FIELDS

class InstructionEditor(QDialog,InstructionEditorInterface):
    test_requested = Signal(object)
    TYPE_ID = DISPLAY_NAME = '窗口中键激活'
    FIELDS = FIELDS

    def __init__(self,parent=None,draft=None,context=None):
        super().__init__(parent)
        self.context=context
        self.trigger_codes=[]
        self.setWindowTitle(self.DISPLAY_NAME)
        self.resize(450,260)
        layout=QVBoxLayout(self)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        layout.addWidget(QLabel('等待所选按键按下，结束等待后继续下一步。'))
        form=QFormLayout();layout.addLayout(form)
        self.operation=QComboBox();self.operation.addItems(['左键','右键','中键','键盘按键','任意键盘按键'])
        form.addRow('触发按键:',self.operation)
        self.read_key=QPushButton('读取触发按键');self.read_key.setAutoDefault(False)
        layout.addWidget(self.read_key)
        self.trigger_key=QLineEdit('f8');layout.addWidget(self.trigger_key)
        self.trigger_key.setPlaceholderText('填写单键名称，例如 f8；组合键请点击读取')
        common=QFormLayout();layout.addLayout(common)
        self.repeat=QSpinBox();self.repeat.setRange(1,1000000)
        self.policy=QComboBox();self.policy.addItems(['提示异常并暂停','提示异常并停止','自动跳过'])
        self.note=QLineEdit()
        common.addRow('等待次数:',self.repeat);common.addRow('异常处理:',self.policy);common.addRow('备注:',self.note)
        self.operation.currentTextChanged.connect(self.update_fields)
        self.trigger_key.textChanged.connect(self.clear_codes)
        self.read_key.clicked.connect(self.capture_trigger)
        add_window_footer(self, layout, buttons)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def clear_codes(self,*_):self.trigger_codes=[]

    def update_fields(self,*_):
        enabled=self.operation.currentText()=='键盘按键'
        self.read_key.setVisible(enabled);self.trigger_key.setVisible(enabled)

    def capture_trigger(self):
        dialog=KeyCapture(self)
        if dialog.exec()==QDialog.Accepted:
            self.trigger_key.setText(' + '.join(dialog.names));self.trigger_codes=list(dialog.codes)
        dialog.deleteLater()

    def load_draft(self,draft):
        draft=draft if isinstance(draft,InstructionDraft) else InstructionDraft.from_mapping(draft)
        self.operation.setCurrentText(draft.parameters.get('触发按键','中键'))
        self.trigger_key.setText(draft.parameters.get('触发键','f8'))
        self.trigger_codes=list(draft.parameters.get('触发键码') or [])
        self.repeat.setValue(draft.repeat_count)
        if self.policy.findText(draft.error_policy)<0:self.policy.addItem(draft.error_policy)
        self.policy.setCurrentText(draft.error_policy);self.note.setText(draft.note)
        self.update_fields()

    def get_draft(self):
        p={'触发按键':self.operation.currentText()}
        if p['触发按键']=='键盘按键':
            p['触发键']=self.trigger_key.text()
            if self.trigger_codes:p['触发键码']=list(self.trigger_codes)
        return InstructionDraft(self.TYPE_ID,p,repeat_count=self.repeat.value(),error_policy=self.policy.currentText(),note=self.note.text())
