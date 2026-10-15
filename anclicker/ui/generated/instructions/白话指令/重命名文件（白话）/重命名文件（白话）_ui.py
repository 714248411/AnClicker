# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '重命名文件（白话）.ui'
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

        self.container_0 = QWidget(self.parameterGroupBox)
        self.container_0.setObjectName(u"container_0")
        self.fieldLayout_0 = QHBoxLayout(self.container_0)
        self.fieldLayout_0.setObjectName(u"fieldLayout_0")
        self.fieldLayout_0.setContentsMargins(0, 0, 0, 0)
        self.parameter_0 = QLineEdit(self.container_0)
        self.parameter_0.setObjectName(u"parameter_0")

        self.fieldLayout_0.addWidget(self.parameter_0)

        self.auxiliary_0 = QPushButton(self.container_0)
        self.auxiliary_0.setObjectName(u"auxiliary_0")

        self.fieldLayout_0.addWidget(self.auxiliary_0)


        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.container_0)

        self.label_1 = QLabel(self.parameterGroupBox)
        self.label_1.setObjectName(u"label_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label_1)

        self.parameter_1 = QComboBox(self.parameterGroupBox)
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.label_2 = QLabel(self.parameterGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
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

        self.parameter_4 = QComboBox(self.parameterGroupBox)
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.setObjectName(u"parameter_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.label_5 = QLabel(self.parameterGroupBox)
        self.label_5.setObjectName(u"label_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.parameter_5 = QLineEdit(self.parameterGroupBox)
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
        self.parameter_6.setObjectName(u"parameter_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameter_6)

        self.label_7 = QLabel(self.parameterGroupBox)
        self.label_7.setObjectName(u"label_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.label_7)

        self.parameter_7 = QLineEdit(self.parameterGroupBox)
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameter_7)

        self.label_8 = QLabel(self.parameterGroupBox)
        self.label_8.setObjectName(u"label_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.LabelRole, self.label_8)

        self.parameter_8 = QLineEdit(self.parameterGroupBox)
        self.parameter_8.setObjectName(u"parameter_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.FieldRole, self.parameter_8)

        self.label_9 = QLabel(self.parameterGroupBox)
        self.label_9.setObjectName(u"label_9")

        self.parameterFormLayout.setWidget(9, QFormLayout.LabelRole, self.label_9)

        self.parameter_9 = QLineEdit(self.parameterGroupBox)
        self.parameter_9.setObjectName(u"parameter_9")

        self.parameterFormLayout.setWidget(9, QFormLayout.FieldRole, self.parameter_9)


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

        self.parameter_1.setCurrentIndex(0)
        self.parameter_2.setCurrentIndex(0)
        self.parameter_4.setCurrentIndex(0)
        self.parameter_6.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u547d\u540d\u6587\u4ef6(\u767d\u8bdd)", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u6307\u4ee4\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u54ea\u4e2a\u6587\u4ef6\u5939", None))
        self.parameter_0.setText("")
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u2026", None))
        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6309\u4ec0\u4e48\u6392\u5e8f", None))
        self.parameter_1.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6587\u4ef6\u540d", None))
        self.parameter_1.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4fee\u6539\u65f6\u95f4", None))
        self.parameter_1.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6587\u4ef6\u5927\u5c0f", None))

        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u6392\u5e8f\u65b9\u5411", None))
        self.parameter_2.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u4ece\u5c0f\u5230\u5927", None))
        self.parameter_2.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4ece\u5927\u5230\u5c0f", None))

        self.label_3.setText(QCoreApplication.translate("InstructionEditor", u"\u7b2c\u51e0\u4e2a\u6587\u4ef6(\u5982 1\u30011-3\u30011,3,5\u3001-1=\u5012\u6570\u7b2c1)", None))
        self.parameter_3.setText(QCoreApplication.translate("InstructionEditor", u"1", None))
        self.label_4.setText(QCoreApplication.translate("InstructionEditor", u"\u547d\u540d\u65b9\u5f0f", None))
        self.parameter_4.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u52a0\u524d\u7f00", None))
        self.parameter_4.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5220\u524d\u7f00", None))
        self.parameter_4.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u52a0\u540e\u7f00", None))
        self.parameter_4.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u5220\u540e\u7f00", None))
        self.parameter_4.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u66ff\u6362\u6587\u5b57", None))
        self.parameter_4.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u5220\u9664\u6587\u5b57", None))
        self.parameter_4.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u6309\u5206\u9694\u7b26\u91cd\u7ec4", None))

        self.label_5.setText(QCoreApplication.translate("InstructionEditor", u"\u6807\u8bc6\u5185\u5bb9(\u524d\u7f00/\u540e\u7f00/\u66ff\u6362\u6587\u5b57)", None))
        self.parameter_5.setText("")
        self.label_6.setText(QCoreApplication.translate("InstructionEditor", u"\u6807\u8bc6\u7c7b\u578b(\u7559\u7a7a=\u7528\u4e0a\u9762\u6587\u5b57)", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u5b9a\u4e49\u6587\u5b57", None))
        self.parameter_6.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u6570\u5b57\u5e8f\u53f7", None))
        self.parameter_6.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5b57\u6bcd\u5e8f\u53f7", None))
        self.parameter_6.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u65e5\u671f", None))

        self.label_7.setText(QCoreApplication.translate("InstructionEditor", u"\u5206\u9694\u7b26(\u91cd\u7ec4\u7528\uff0c\u5982 _ - \u7a7a\u683c)", None))
        self.parameter_7.setText(QCoreApplication.translate("InstructionEditor", u"_", None))
        self.label_8.setText(QCoreApplication.translate("InstructionEditor", u"\u53d6\u54ea\u51e0\u6bb5\u91cd\u7ec4(\u5982 2,1\uff0c\u7559\u7a7a=\u5168\u90e8)", None))
        self.parameter_8.setText("")
        self.label_9.setText(QCoreApplication.translate("InstructionEditor", u"\u66ff\u6362\u4e3a\uff08\u66ff\u6362\u6587\u5b57\u65f6\u4f7f\u7528\uff09", None))
        self.parameter_9.setText("")
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

