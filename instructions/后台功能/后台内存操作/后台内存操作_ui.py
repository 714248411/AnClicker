# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '后台内存操作.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qt_compat.QtCore import *
from qt_compat.QtGui import *
from qt_compat.QtWidgets import *


class Ui_InstructionEditor(object):
    def setupUi(self, InstructionEditor):
        if not InstructionEditor.objectName():
            InstructionEditor.setObjectName(u"InstructionEditor")
        self.rootLayout = QVBoxLayout(InstructionEditor)
        self.rootLayout.setObjectName(u"rootLayout")
        self.titleLabel = QLabel(InstructionEditor)
        self.titleLabel.setObjectName(u"titleLabel")

        self.rootLayout.addWidget(self.titleLabel)

        self.parameterGroupBox = QGroupBox(InstructionEditor)
        self.parameterGroupBox.setObjectName(u"parameterGroupBox")
        self.parameterFormLayout = QFormLayout(self.parameterGroupBox)
        self.parameterFormLayout.setObjectName(u"parameterFormLayout")
        self.label_0 = QLabel(self.parameterGroupBox)
        self.label_0.setObjectName(u"label_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.LabelRole, self.label_0)

        self.parameter_0 = QComboBox(self.parameterGroupBox)
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.label_1 = QLabel(self.parameterGroupBox)
        self.label_1.setObjectName(u"label_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label_1)

        self.parameter_1 = QPlainTextEdit(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.label_2 = QLabel(self.parameterGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.fieldLayout_2 = QHBoxLayout()
        self.fieldLayout_2.setObjectName(u"fieldLayout_2")
        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")
        self.parameter_2.setEditable(True)

        self.fieldLayout_2.addWidget(self.parameter_2)

        self.auxiliary_2 = QPushButton(self.parameterGroupBox)
        self.auxiliary_2.setObjectName(u"auxiliary_2")

        self.fieldLayout_2.addWidget(self.auxiliary_2)


        self.parameterFormLayout.setLayout(2, QFormLayout.FieldRole, self.fieldLayout_2)


        self.rootLayout.addWidget(self.parameterGroupBox)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.rootLayout.addItem(self.verticalSpacer)

        self.commonGroupBox = QGroupBox(InstructionEditor)
        self.commonGroupBox.setObjectName(u"commonGroupBox")
        self.commonFormLayout = QFormLayout(self.commonGroupBox)
        self.commonFormLayout.setObjectName(u"commonFormLayout")
        self.repeatLabel = QLabel(self.commonGroupBox)
        self.repeatLabel.setObjectName(u"repeatLabel")

        self.commonFormLayout.setWidget(0, QFormLayout.LabelRole, self.repeatLabel)

        self.repeatSpinBox = QSpinBox(self.commonGroupBox)
        self.repeatSpinBox.setObjectName(u"repeatSpinBox")
        self.repeatSpinBox.setMinimum(1)
        self.repeatSpinBox.setMaximum(999999)
        self.repeatSpinBox.setValue(1)

        self.commonFormLayout.setWidget(0, QFormLayout.FieldRole, self.repeatSpinBox)

        self.errorPolicyLabel = QLabel(self.commonGroupBox)
        self.errorPolicyLabel.setObjectName(u"errorPolicyLabel")

        self.commonFormLayout.setWidget(1, QFormLayout.LabelRole, self.errorPolicyLabel)

        self.errorPolicyComboBox = QComboBox(self.commonGroupBox)
        self.errorPolicyComboBox.addItem("")
        self.errorPolicyComboBox.addItem("")
        self.errorPolicyComboBox.addItem("")
        self.errorPolicyComboBox.setObjectName(u"errorPolicyComboBox")

        self.commonFormLayout.setWidget(1, QFormLayout.FieldRole, self.errorPolicyComboBox)

        self.noteLabel = QLabel(self.commonGroupBox)
        self.noteLabel.setObjectName(u"noteLabel")

        self.commonFormLayout.setWidget(2, QFormLayout.LabelRole, self.noteLabel)

        self.noteEdit = QLineEdit(self.commonGroupBox)
        self.noteEdit.setObjectName(u"noteEdit")

        self.commonFormLayout.setWidget(2, QFormLayout.FieldRole, self.noteEdit)


        self.rootLayout.addWidget(self.commonGroupBox)

        self.footerLayout = QHBoxLayout()
        self.footerLayout.setObjectName(u"footerLayout")
        self.testButton = QPushButton(InstructionEditor)
        self.testButton.setObjectName(u"testButton")

        self.footerLayout.addWidget(self.testButton)

        self.footerSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.footerLayout.addItem(self.footerSpacer)

        self.buttonBox = QDialogButtonBox(InstructionEditor)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.footerLayout.addWidget(self.buttonBox)


        self.rootLayout.addLayout(self.footerLayout)


        self.retranslateUi(InstructionEditor)

        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u5185\u5b58\u64cd\u4f5c", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u64cd\u4f5c", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6\u6574\u6570 \u00b7 ReadInt", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6\u5355\u7cbe\u5ea6\u6570\u503c \u00b7 ReadFloat", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6\u53cc\u7cbe\u5ea6\u6570\u503c \u00b7 ReadDouble", None))
        self.parameter_0.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6\u5b57\u7b26\u4e32 \u00b7 ReadString", None))
        self.parameter_0.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6\u5b57\u8282\u6570\u636e \u00b7 ReadData", None))
        self.parameter_0.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u5199\u5165\u6574\u6570 \u00b7 WriteInt", None))
        self.parameter_0.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u5199\u5165\u5355\u7cbe\u5ea6\u6570\u503c \u00b7 WriteFloat", None))
        self.parameter_0.setItemText(7, QCoreApplication.translate("InstructionEditor", u"\u5199\u5165\u53cc\u7cbe\u5ea6\u6570\u503c \u00b7 WriteDouble", None))
        self.parameter_0.setItemText(8, QCoreApplication.translate("InstructionEditor", u"\u5199\u5165\u5b57\u7b26\u4e32 \u00b7 WriteString", None))
        self.parameter_0.setItemText(9, QCoreApplication.translate("InstructionEditor", u"\u5199\u5165\u5b57\u8282\u6570\u636e \u00b7 WriteData", None))
        self.parameter_0.setItemText(10, QCoreApplication.translate("InstructionEditor", u"\u641c\u7d22\u6574\u6570 \u00b7 FindInt", None))
        self.parameter_0.setItemText(11, QCoreApplication.translate("InstructionEditor", u"\u641c\u7d22\u5355\u7cbe\u5ea6\u6570\u503c \u00b7 FindFloat", None))
        self.parameter_0.setItemText(12, QCoreApplication.translate("InstructionEditor", u"\u641c\u7d22\u53cc\u7cbe\u5ea6\u6570\u503c \u00b7 FindDouble", None))
        self.parameter_0.setItemText(13, QCoreApplication.translate("InstructionEditor", u"\u641c\u7d22\u5b57\u7b26\u4e32 \u00b7 FindString", None))
        self.parameter_0.setItemText(14, QCoreApplication.translate("InstructionEditor", u"\u641c\u7d22\u5b57\u8282\u6570\u636e \u00b7 FindData", None))
        self.parameter_0.setItemText(15, QCoreApplication.translate("InstructionEditor", u"FindIntEx", None))
        self.parameter_0.setItemText(16, QCoreApplication.translate("InstructionEditor", u"FindFloatEx", None))
        self.parameter_0.setItemText(17, QCoreApplication.translate("InstructionEditor", u"FindDoubleEx", None))
        self.parameter_0.setItemText(18, QCoreApplication.translate("InstructionEditor", u"FindStringEx", None))
        self.parameter_0.setItemText(19, QCoreApplication.translate("InstructionEditor", u"FindDataEx", None))
        self.parameter_0.setItemText(20, QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u6a21\u5757\u57fa\u5740 \u00b7 GetModuleBaseAddr", None))
        self.parameter_0.setItemText(21, QCoreApplication.translate("InstructionEditor", u"IntToData", None))
        self.parameter_0.setItemText(22, QCoreApplication.translate("InstructionEditor", u"FloatToData", None))
        self.parameter_0.setItemText(23, QCoreApplication.translate("InstructionEditor", u"DoubleToData", None))
        self.parameter_0.setItemText(24, QCoreApplication.translate("InstructionEditor", u"StringToData", None))

        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u63a5\u53e3\u53c2\u6570", None))
        self.parameter_1.setPlainText(QCoreApplication.translate("InstructionEditor", u"{}", None))
        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed3\u679c\u53d8\u91cf\uff08\u53ef\u9009\uff09", None))
        self.auxiliary_2.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
        pass
    # retranslateUi

