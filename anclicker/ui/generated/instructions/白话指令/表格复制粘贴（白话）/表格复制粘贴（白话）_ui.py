# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '表格复制粘贴（白话）.ui'
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

        self.container_3 = QWidget(self.parameterGroupBox)
        self.container_3.setObjectName(u"container_3")
        self.fieldLayout_3 = QHBoxLayout(self.container_3)
        self.fieldLayout_3.setObjectName(u"fieldLayout_3")
        self.fieldLayout_3.setContentsMargins(0, 0, 0, 0)
        self.parameter_3 = QLineEdit(self.container_3)
        self.parameter_3.setObjectName(u"parameter_3")

        self.fieldLayout_3.addWidget(self.parameter_3)

        self.auxiliary_3 = QPushButton(self.container_3)
        self.auxiliary_3.setObjectName(u"auxiliary_3")

        self.fieldLayout_3.addWidget(self.auxiliary_3)


        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.container_3)

        self.label_4 = QLabel(self.parameterGroupBox)
        self.label_4.setObjectName(u"label_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.parameter_4 = QLineEdit(self.parameterGroupBox)
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

        self.parameter_6.setCurrentIndex(0)
        self.parameter_7.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u8868\u683c\u590d\u5236\u7c98\u8d34(\u767d\u8bdd)", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u6307\u4ee4\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u2460 \u6e90\u8868\u683c\u8def\u5f84(\u53ef\u628aExcel\u6587\u4ef6\u62d6\u8fdb\u6765)", None))
        self.parameter_0.setText("")
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u2026", None))
        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u2461 \u590d\u5236\u54ea\u51e0\u5217/\u533a\u57df(\u5982 A1-A9,B2-B4\uff1b\u7559\u7a7a=\u6574\u4e2a\u8868\u683c)", None))
        self.parameter_1.setText("")
        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u2462 \u6e90\u5de5\u4f5c\u8868\u540d(\u7559\u7a7a=\u7b2c\u4e00\u4e2a\u8868)", None))
        self.parameter_2.setText("")
        self.label_3.setText(QCoreApplication.translate("InstructionEditor", u"\u2463 \u76ee\u6807\u8868\u683c\u8def\u5f84(\u53ef\u62d6\u6587\u4ef6\u8fdb\u6765\uff0c\u7559\u7a7a=\u65b0\u5efa\u5230\u684c\u9762)", None))
        self.parameter_3.setText("")
        self.auxiliary_3.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u2026", None))
        self.label_4.setText(QCoreApplication.translate("InstructionEditor", u"\u2464 \u76ee\u6807\u5de5\u4f5c\u8868\u540d(\u7559\u7a7a=\u7b2c\u4e00\u4e2a\u8868)", None))
        self.parameter_4.setText("")
        self.label_5.setText(QCoreApplication.translate("InstructionEditor", u"\u2465 \u4ece\u54ea\u4e2a\u5355\u5143\u683c\u5f00\u59cb\u7c98\u8d34(\u5982 B1\u3001D2)", None))
        self.parameter_5.setText(QCoreApplication.translate("InstructionEditor", u"A1", None))
        self.label_6.setText(QCoreApplication.translate("InstructionEditor", u"\u2466 \u7c98\u8d34\u65b9\u5f0f", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u53ea\u7c98\u8d34\u6587\u672c", None))
        self.parameter_6.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5168\u90e8\u7c98\u8d34", None))
        self.parameter_6.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u53ea\u7c98\u8d34\u503c", None))
        self.parameter_6.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u53ea\u7c98\u8d34\u516c\u5f0f", None))
        self.parameter_6.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u53ea\u7c98\u8d34\u683c\u5f0f", None))
        self.parameter_6.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u4fdd\u7559\u516c\u5f0f", None))
        self.parameter_6.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u503c\u4e0e\u6570\u5b57\u683c\u5f0f", None))
        self.parameter_6.setItemText(7, QCoreApplication.translate("InstructionEditor", u"\u516c\u5f0f\u4e0e\u6570\u5b57\u683c\u5f0f", None))
        self.parameter_6.setItemText(8, QCoreApplication.translate("InstructionEditor", u"\u4e0d\u8986\u76d6\u539f\u6709\u5185\u5bb9", None))

        self.label_7.setText(QCoreApplication.translate("InstructionEditor", u"\u2467 \u7c98\u8d34\u540e\u662f\u5426\u4fdd\u5b58\u8868\u683c", None))
        self.parameter_7.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u4fdd\u5b58", None))
        self.parameter_7.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4e0d\u4fdd\u5b58", None))

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

