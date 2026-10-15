# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '后台键鼠操作.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from anclicker.platform.qt_compat.QtCore import *
from anclicker.platform.qt_compat.QtGui import *
from anclicker.platform.qt_compat.QtWidgets import *


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
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u952e\u9f20\u64cd\u4f5c", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u64cd\u4f5c", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u79fb\u52a8\u81f3\u5750\u6807 \u00b7 MoveTo", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u76f8\u5bf9\u79fb\u52a8 \u00b7 MoveR", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"MoveToEx", None))
        self.parameter_0.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u9f20\u6807\u5de6\u952e\u5355\u51fb \u00b7 LeftClick", None))
        self.parameter_0.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u9f20\u6807\u53f3\u952e\u5355\u51fb \u00b7 RightClick", None))
        self.parameter_0.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u9f20\u6807\u4e2d\u952e\u5355\u51fb \u00b7 MiddleClick", None))
        self.parameter_0.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u9f20\u6807\u5de6\u952e\u53cc\u51fb \u00b7 LeftDoubleClick", None))
        self.parameter_0.setItemText(7, QCoreApplication.translate("InstructionEditor", u"\u6309\u4f4f\u5de6\u952e \u00b7 LeftDown", None))
        self.parameter_0.setItemText(8, QCoreApplication.translate("InstructionEditor", u"\u677e\u5f00\u5de6\u952e \u00b7 LeftUp", None))
        self.parameter_0.setItemText(9, QCoreApplication.translate("InstructionEditor", u"\u6309\u4f4f\u53f3\u952e \u00b7 RightDown", None))
        self.parameter_0.setItemText(10, QCoreApplication.translate("InstructionEditor", u"\u677e\u5f00\u53f3\u952e \u00b7 RightUp", None))
        self.parameter_0.setItemText(11, QCoreApplication.translate("InstructionEditor", u"\u6eda\u8f6e\u5411\u4e0a \u00b7 WheelUp", None))
        self.parameter_0.setItemText(12, QCoreApplication.translate("InstructionEditor", u"\u6eda\u8f6e\u5411\u4e0b \u00b7 WheelDown", None))
        self.parameter_0.setItemText(13, QCoreApplication.translate("InstructionEditor", u"\u6309\u4f4f\u6309\u952e \u00b7 KeyDown", None))
        self.parameter_0.setItemText(14, QCoreApplication.translate("InstructionEditor", u"\u677e\u5f00\u6309\u952e \u00b7 KeyUp", None))
        self.parameter_0.setItemText(15, QCoreApplication.translate("InstructionEditor", u"\u6309\u4e00\u4e0b\u6309\u952e \u00b7 KeyPress", None))
        self.parameter_0.setItemText(16, QCoreApplication.translate("InstructionEditor", u"KeyDownChar", None))
        self.parameter_0.setItemText(17, QCoreApplication.translate("InstructionEditor", u"KeyUpChar", None))
        self.parameter_0.setItemText(18, QCoreApplication.translate("InstructionEditor", u"KeyPressChar", None))
        self.parameter_0.setItemText(19, QCoreApplication.translate("InstructionEditor", u"KeyPressStr", None))
        self.parameter_0.setItemText(20, QCoreApplication.translate("InstructionEditor", u"\u53d1\u9001\u6587\u672c \u00b7 SendString", None))
        self.parameter_0.setItemText(21, QCoreApplication.translate("InstructionEditor", u"\u53d1\u9001\u6587\u672c\uff08\u65b9\u5f0f\u4e8c\uff09 \u00b7 SendString2", None))
        self.parameter_0.setItemText(22, QCoreApplication.translate("InstructionEditor", u"SetMouseDelay", None))
        self.parameter_0.setItemText(23, QCoreApplication.translate("InstructionEditor", u"SetKeypadDelay", None))
        self.parameter_0.setItemText(24, QCoreApplication.translate("InstructionEditor", u"\u6309\u4f4f\u4e2d\u952e \u00b7 MiddleDown", None))
        self.parameter_0.setItemText(25, QCoreApplication.translate("InstructionEditor", u"\u677e\u5f00\u4e2d\u952e \u00b7 MiddleUp", None))

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

