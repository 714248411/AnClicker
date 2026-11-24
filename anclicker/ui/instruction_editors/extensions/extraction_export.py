"""Compact save settings shared by extraction export commands."""
from anclicker.instructions.common import SchemaInstructionEditor
from anclicker.platform.extraction_export import EXTENSIONS
from anclicker.platform.qt_compat.QtWidgets import (QVBoxLayout,QHBoxLayout,QFormLayout,QGroupBox,QLabel,QLineEdit,QComboBox,QSpinBox,QPushButton,QDialogButtonBox,QFileDialog)

class ExportUi:
    def setupUi(self, dialog):
        self.rootLayout=QVBoxLayout(dialog)
        self.titleLabel=QLabel(dialog.DISPLAY_NAME);self.rootLayout.addWidget(self.titleLabel)
        hint=QLabel('自动接收前面最近一次网页提取的结果，无需设置变量。请将此指令放在提取指令后。')
        self.hint=hint
        hint.setWordWrap(True);self.rootLayout.addWidget(hint)
        self.parameterGroupBox=QGroupBox('保存设置');self.rootLayout.addWidget(self.parameterGroupBox)
        self.parameterFormLayout=QFormLayout(self.parameterGroupBox)
        row=QHBoxLayout();self.parameter_0=QLineEdit();self.parameter_0.setPlaceholderText('选择文件保存位置')
        self.browse=QPushButton('另存为…');row.addWidget(self.parameter_0,1);row.addWidget(self.browse)
        self.parameterLabel_0=QLabel('保存为');self.parameterFormLayout.addRow(self.parameterLabel_0,row)
        self.parameter_1=QComboBox();self.parameter_1.addItems(['自动更名','覆盖','报错'])
        self.parameterLabel_1=QLabel('文件已存在');self.parameterFormLayout.addRow(self.parameterLabel_1,self.parameter_1)
        self.commonGroupBox=QGroupBox('通用参数');self.rootLayout.addWidget(self.commonGroupBox)
        self.commonFormLayout=QFormLayout(self.commonGroupBox)
        self.repeatSpinBox=QSpinBox();self.repeatSpinBox.setRange(1,999999)
        self.errorPolicyComboBox=QComboBox();self.errorPolicyComboBox.addItems(['提示异常并暂停','提示异常并停止','自动跳过'])
        self.noteEdit=QLineEdit()
        self.commonFormLayout.addRow('重复次数',self.repeatSpinBox)
        self.commonFormLayout.addRow('异常处理',self.errorPolicyComboBox)
        self.commonFormLayout.addRow('备注',self.noteEdit)
        self.footerLayout=QHBoxLayout();self.rootLayout.addLayout(self.footerLayout)
        self.testButton=QPushButton('测试指令');self.footerLayout.addWidget(self.testButton);self.footerLayout.addStretch()
        self.buttonBox=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);self.footerLayout.addWidget(self.buttonBox)
        dialog.resize(650,390)

class ExportEditor(SchemaInstructionEditor):
    UI_CLASS=ExportUi
    FORMAT=''
    def __init__(self,parent=None,draft=None,context=None):
        super().__init__(parent,draft,context)
        self.ui.browse.clicked.connect(self.browse_destination)
    def browse_destination(self):
        suffix=EXTENSIONS[self.FORMAT]
        path,_=QFileDialog.getSaveFileName(self,'另存为 '+self.FORMAT,self.ui.parameter_0.text() or '提取结果'+suffix,self.FORMAT+' (*'+suffix+')')
        if path:
            from pathlib import Path
            target=Path(path)
            self.ui.parameter_0.setText(str(target if target.suffix.lower()==suffix else target.with_suffix(suffix)))
