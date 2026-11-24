from anclicker.platform.qt_compat.QtCore import Signal
from anclicker.ui.instruction_editors.window_settings_footer import add_window_footer
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QSpinBox,QLineEdit,QLabel,QPushButton,QDialogButtonBox,QMessageBox)
from anclicker.domain.instruction_interfaces import InstructionEditorInterface
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.background_window_picker import pick_background_window
from anclicker.platform.background_runtime import Windows
from anclicker.instructions.窗口键鼠.窗口位置与大小.schema import FIELDS,OPERATIONS

class InstructionEditor(QDialog,InstructionEditorInterface):
    test_requested = Signal(object)
    TYPE_ID = DISPLAY_NAME = '窗口位置与大小'
    FIELDS = FIELDS

    def __init__(self,parent=None,draft=None,context=None):
        super().__init__(parent)
        self.context=context;self.target={}
        self.setWindowTitle(self.DISPLAY_NAME);self.resize(500,440)
        layout=QVBoxLayout(self)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定');buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        row=QHBoxLayout();layout.addLayout(row)
        self.select=QPushButton('点选目标窗口');self.select.setAutoDefault(False)
        self.target_label=QLabel('未选择窗口');self.target_label.setWordWrap(True)
        row.addWidget(self.select);row.addWidget(self.target_label,1)
        self.select.clicked.connect(self.select_window)
        form=QFormLayout();layout.addLayout(form)
        self.operation=QComboBox();self.operation.addItems(OPERATIONS);form.addRow('操作:',self.operation)
        self.read_button=QPushButton('读取窗口当前位置和大小');self.read_button.setAutoDefault(False)
        form.addRow(self.read_button);self.read_button.clicked.connect(self.read_geometry)
        self.fields={};self.rows={}
        for key,minimum in [('X',-100000),('Y',-100000),('宽度',1),('高度',1)]:
            spin=QSpinBox();spin.setRange(minimum,100000);spin.setSuffix(' px')
            form.addRow(('屏幕 '+key if key in ('X','Y') else '窗口'+key)+':',spin)
            self.fields[key]=spin;self.rows[key]=(form.labelForField(spin),spin)
        self.record=QLineEdit('窗口位置记录');form.addRow('记录变量:',self.record)
        self.rows['记录名称']=(form.labelForField(self.record),self.record)
        self.hint=QLabel();self.hint.setWordWrap(True);layout.addWidget(self.hint)
        self.repeat=QSpinBox();self.repeat.setRange(1,1000000)
        self.policy=QComboBox();self.policy.addItems(['提示异常并暂停','提示异常并停止','自动跳过'])
        self.note=QLineEdit()
        form.addRow('重复次数:',self.repeat);form.addRow('异常处理:',self.policy);form.addRow('备注:',self.note)
        self.operation.currentTextChanged.connect(self.update_fields)
        add_window_footer(self, layout, buttons)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def update_fields(self,*_):
        op=self.operation.currentText();record=op in OPERATIONS[3:]
        for key,widgets in self.rows.items():
            visible=record if key=='记录名称' else (not record and (op!='仅调整大小' if key in ('X','Y') else op!='仅移动位置'))
            for widget in widgets:widget.setVisible(visible)
        self.read_button.setVisible(not record);self.read_button.setEnabled(bool(self.target))
        self.hint.setText('运行记录指令时保存状态；恢复指令填写相同记录变量。可恢复普通、最大化、最小化和置顶状态。' if record else '位置为屏幕绝对坐标，允许负数；尺寸包含标题栏和边框。最大化或最小化窗口会先恢复普通状态再调整。')

    def select_window(self):
        try:
            target=pick_background_window(self)
            if target:
                self.target=target;self.show_target();self.update_fields()
        except Exception as error:QMessageBox.warning(self,self.DISPLAY_NAME,str(error))

    def show_target(self):
        self.target_label.setText(self.target.get('窗口标题') or self.target.get('窗口类名') or '未选择窗口')

    def read_geometry(self):
        try:
            windows=Windows();target=windows.resolve(self.target)
            left,top,right,bottom=windows.gui.GetWindowRect(int(target['窗口句柄']))
            for key,value in zip(('X','Y','宽度','高度'),(left,top,right-left,bottom-top)):self.fields[key].setValue(value)
        except Exception as error:QMessageBox.warning(self,self.DISPLAY_NAME,str(error))

    def load_draft(self,draft):
        draft=draft if isinstance(draft,InstructionDraft) else InstructionDraft.from_mapping(draft)
        p=draft.parameters;self.target=dict(p.get('窗口') or {});self.show_target()
        self.operation.setCurrentText(p.get('操作',OPERATIONS[0]))
        for key,widget in self.fields.items():widget.setValue(int(p.get(key,800 if key=='宽度' else 600 if key=='高度' else 0)))
        self.record.setText(p.get('记录名称','窗口位置记录'));self.repeat.setValue(draft.repeat_count)
        if self.policy.findText(draft.error_policy)<0:self.policy.addItem(draft.error_policy)
        self.policy.setCurrentText(draft.error_policy);self.note.setText(draft.note);self.update_fields()

    def get_draft(self):
        p={'窗口':dict(self.target),'操作':self.operation.currentText(),'记录名称':self.record.text().strip()}
        p.update({key:widget.value() for key,widget in self.fields.items()})
        return InstructionDraft(self.TYPE_ID,p,repeat_count=self.repeat.value(),error_policy=self.policy.currentText(),note=self.note.text())

    def accept(self):
        if not self.target or (self.operation.currentText() in OPERATIONS[3:] and not self.record.text().strip()):
            QMessageBox.warning(self,self.DISPLAY_NAME,'请先选择窗口，并为记录或恢复填写记录变量名称');return
        super().accept()
