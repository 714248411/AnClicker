# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '处理文件（白话）.ui'
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
        InstructionEditor.resize(720, 680)
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
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.label_1 = QLabel(self.parameterGroupBox)
        self.label_1.setObjectName(u"label_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label_1)

        self.container_1 = QWidget(self.parameterGroupBox)
        self.container_1.setObjectName(u"container_1")
        self.fieldLayout_1 = QHBoxLayout(self.container_1)
        self.fieldLayout_1.setObjectName(u"fieldLayout_1")
        self.fieldLayout_1.setContentsMargins(0, 0, 0, 0)
        self.parameter_1 = QLineEdit(self.container_1)
        self.parameter_1.setObjectName(u"parameter_1")

        self.fieldLayout_1.addWidget(self.parameter_1)

        self.auxiliary_1 = QPushButton(self.container_1)
        self.auxiliary_1.setObjectName(u"auxiliary_1")

        self.fieldLayout_1.addWidget(self.auxiliary_1)


        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.container_1)

        self.label_2 = QLabel(self.parameterGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.label_3 = QLabel(self.parameterGroupBox)
        self.label_3.setObjectName(u"label_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.label_3)

        self.parameter_3 = QComboBox(self.parameterGroupBox)
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.label_4 = QLabel(self.parameterGroupBox)
        self.label_4.setObjectName(u"label_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.parameter_4 = QLineEdit(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.label_5 = QLabel(self.parameterGroupBox)
        self.label_5.setObjectName(u"label_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.container_5 = QWidget(self.parameterGroupBox)
        self.container_5.setObjectName(u"container_5")
        self.fieldLayout_5 = QHBoxLayout(self.container_5)
        self.fieldLayout_5.setObjectName(u"fieldLayout_5")
        self.fieldLayout_5.setContentsMargins(0, 0, 0, 0)
        self.parameter_5 = QLineEdit(self.container_5)
        self.parameter_5.setObjectName(u"parameter_5")

        self.fieldLayout_5.addWidget(self.parameter_5)

        self.auxiliary_5 = QPushButton(self.container_5)
        self.auxiliary_5.setObjectName(u"auxiliary_5")

        self.fieldLayout_5.addWidget(self.auxiliary_5)


        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.container_5)


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

        self.parameter_0.setCurrentIndex(0)
        self.parameter_2.setCurrentIndex(0)
        self.parameter_3.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5904\u7406\u6587\u4ef6(\u767d\u8bdd)", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u6307\u4ee4\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u505a\u4ec0\u4e48", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u5220\u9664", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u590d\u5236", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u79fb\u52a8", None))
        self.parameter_0.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u5217\u51fa\u6587\u4ef6\u540d", None))

        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u54ea\u4e2a\u6587\u4ef6\u5939", None))
        self.parameter_1.setText("")
        self.auxiliary_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u2026", None))
        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u6309\u4ec0\u4e48\u6392\u5e8f", None))
        self.parameter_2.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6587\u4ef6\u540d", None))
        self.parameter_2.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4fee\u6539\u65f6\u95f4", None))
        self.parameter_2.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6587\u4ef6\u5927\u5c0f", None))

        self.label_3.setText(QCoreApplication.translate("InstructionEditor", u"\u6392\u5e8f\u65b9\u5411", None))
        self.parameter_3.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u4ece\u5c0f\u5230\u5927", None))
        self.parameter_3.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4ece\u5927\u5230\u5c0f", None))

        self.label_4.setText(QCoreApplication.translate("InstructionEditor", u"\u7b2c\u51e0\u4e2a\u6587\u4ef6(\u5982 1\u30011,3,5\u30011-3\u3001-1=\u5012\u6570\u7b2c1)", None))
        self.parameter_4.setText(QCoreApplication.translate("InstructionEditor", u"1", None))
        self.label_5.setText(QCoreApplication.translate("InstructionEditor", u"\u590d\u5236/\u79fb\u52a8\u5230\u54ea(\u6587\u4ef6\u5939\u6216\u65b0\u8def\u5f84)", None))
        self.parameter_5.setText("")
        self.auxiliary_5.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u2026", None))
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

