# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '绑定选择窗口.ui'
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

        self.fieldLayout_0 = QHBoxLayout()
        self.fieldLayout_0.setObjectName(u"fieldLayout_0")
        self.parameter_0 = QLineEdit(self.parameterGroupBox)
        self.parameter_0.setObjectName(u"parameter_0")

        self.fieldLayout_0.addWidget(self.parameter_0)

        self.auxiliary_0 = QPushButton(self.parameterGroupBox)
        self.auxiliary_0.setObjectName(u"auxiliary_0")

        self.fieldLayout_0.addWidget(self.auxiliary_0)


        self.parameterFormLayout.setLayout(0, QFormLayout.FieldRole, self.fieldLayout_0)

        self.label_1 = QLabel(self.parameterGroupBox)
        self.label_1.setObjectName(u"label_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label_1)

        self.parameter_1 = QLineEdit(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.label_2 = QLabel(self.parameterGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.parameter_2 = QLineEdit(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.label_3 = QLabel(self.parameterGroupBox)
        self.label_3.setObjectName(u"label_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.parameter_3 = QLineEdit(self.parameterGroupBox)
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.label_4 = QLabel(self.parameterGroupBox)
        self.label_4.setObjectName(u"label_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.parameter_4 = QSpinBox(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setMinimum(-1000000)
        self.parameter_4.setMaximum(2147483647)
        self.parameter_4.setValue(0)

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.label_5 = QLabel(self.parameterGroupBox)
        self.label_5.setObjectName(u"label_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.parameter_5 = QComboBox(self.parameterGroupBox)
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.setObjectName(u"parameter_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.label_6 = QLabel(self.parameterGroupBox)
        self.label_6.setObjectName(u"label_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.label_6)

        self.parameter_6 = QComboBox(self.parameterGroupBox)
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.setObjectName(u"parameter_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameter_6)

        self.label_7 = QLabel(self.parameterGroupBox)
        self.label_7.setObjectName(u"label_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.label_7)

        self.parameter_7 = QComboBox(self.parameterGroupBox)
        self.parameter_7.addItem("")
        self.parameter_7.addItem("")
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameter_7)

        self.label_8 = QLabel(self.parameterGroupBox)
        self.label_8.setObjectName(u"label_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.LabelRole, self.label_8)

        self.parameter_8 = QComboBox(self.parameterGroupBox)
        self.parameter_8.addItem("")
        self.parameter_8.addItem("")
        self.parameter_8.setObjectName(u"parameter_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.FieldRole, self.parameter_8)

        self.label_9 = QLabel(self.parameterGroupBox)
        self.label_9.setObjectName(u"label_9")

        self.parameterFormLayout.setWidget(9, QFormLayout.LabelRole, self.label_9)

        self.parameter_9 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_9.setObjectName(u"parameter_9")
        self.parameter_9.setMinimum(0.000000000000000)
        self.parameter_9.setMaximum(10.000000000000000)
        self.parameter_9.setValue(1.000000000000000)

        self.parameterFormLayout.setWidget(9, QFormLayout.FieldRole, self.parameter_9)

        self.label_10 = QLabel(self.parameterGroupBox)
        self.label_10.setObjectName(u"label_10")

        self.parameterFormLayout.setWidget(10, QFormLayout.LabelRole, self.label_10)

        self.parameter_10 = QComboBox(self.parameterGroupBox)
        self.parameter_10.addItem("")
        self.parameter_10.addItem("")
        self.parameter_10.addItem("")
        self.parameter_10.addItem("")
        self.parameter_10.addItem("")
        self.parameter_10.addItem("")
        self.parameter_10.setObjectName(u"parameter_10")

        self.parameterFormLayout.setWidget(10, QFormLayout.FieldRole, self.parameter_10)


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
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed1\u5b9a\u9009\u62e9\u7a97\u53e3", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u76ee\u6807\u7a97\u53e3\u53e5\u67c4", None))
        self.parameter_0.setText("")
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u9009\u62e9\u7a97\u53e3\u2026", None))
        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u7a97\u53e3\u6807\u9898", None))
        self.parameter_1.setText("")
        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u7a97\u53e3\u7c7b\u540d", None))
        self.parameter_2.setText("")
        self.label_3.setText(QCoreApplication.translate("InstructionEditor", u"\u8fdb\u7a0b\u8def\u5f84", None))
        self.parameter_3.setText("")
        self.label_4.setText(QCoreApplication.translate("InstructionEditor", u"\u8fdb\u7a0b ID", None))
        self.label_5.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u56fe\u50cf\u6a21\u5f0f", None))
        self.parameter_5.setItemText(0, QCoreApplication.translate("InstructionEditor", u"dx1", None))
        self.parameter_5.setItemText(1, QCoreApplication.translate("InstructionEditor", u"dx2", None))
        self.parameter_5.setItemText(2, QCoreApplication.translate("InstructionEditor", u"dx3", None))
        self.parameter_5.setItemText(3, QCoreApplication.translate("InstructionEditor", u"gdi", None))
        self.parameter_5.setItemText(4, QCoreApplication.translate("InstructionEditor", u"gdi2", None))
        self.parameter_5.setItemText(5, QCoreApplication.translate("InstructionEditor", u"dx", None))

        self.label_6.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u9f20\u6807\u6a21\u5f0f", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"dx", None))
        self.parameter_6.setItemText(1, QCoreApplication.translate("InstructionEditor", u"dx2", None))
        self.parameter_6.setItemText(2, QCoreApplication.translate("InstructionEditor", u"windows", None))
        self.parameter_6.setItemText(3, QCoreApplication.translate("InstructionEditor", u"windows2", None))
        self.parameter_6.setItemText(4, QCoreApplication.translate("InstructionEditor", u"windows3", None))

        self.label_7.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u952e\u76d8\u6a21\u5f0f", None))
        self.parameter_7.setItemText(0, QCoreApplication.translate("InstructionEditor", u"dx", None))
        self.parameter_7.setItemText(1, QCoreApplication.translate("InstructionEditor", u"windows", None))

        self.label_8.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed1\u5b9a\u65b9\u5f0f", None))
        self.parameter_8.setItemText(0, QCoreApplication.translate("InstructionEditor", u"0", None))
        self.parameter_8.setItemText(1, QCoreApplication.translate("InstructionEditor", u"2", None))

        self.label_9.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed1\u5b9a\u540e\u7b49\u5f85\uff08\u79d2\uff09", None))
        self.label_10.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed1\u5b9a\u65b9\u6848", None))
        self.parameter_10.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u4f18\u5148 DX1 \u2192 DX2", None))
        self.parameter_10.setItemText(1, QCoreApplication.translate("InstructionEditor", u"DX1", None))
        self.parameter_10.setItemText(2, QCoreApplication.translate("InstructionEditor", u"DX2", None))
        self.parameter_10.setItemText(3, QCoreApplication.translate("InstructionEditor", u"GDI \u517c\u5bb9", None))
        self.parameter_10.setItemText(4, QCoreApplication.translate("InstructionEditor", u"GDI2 \u517c\u5bb9", None))
        self.parameter_10.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u81ea\u5b9a\u4e49", None))

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

