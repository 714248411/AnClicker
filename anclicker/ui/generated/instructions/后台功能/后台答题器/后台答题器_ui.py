# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '后台答题器.ui'
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

        self.parameter_1 = QComboBox(self.parameterGroupBox)
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
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

        self.parameter_3 = QComboBox(self.parameterGroupBox)
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.label_4 = QLabel(self.parameterGroupBox)
        self.label_4.setObjectName(u"label_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.label_4)

        self.parameter_4 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setMinimum(0.010000000000000)
        self.parameter_4.setMaximum(1.000000000000000)
        self.parameter_4.setValue(0.850000000000000)

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.label_5 = QLabel(self.parameterGroupBox)
        self.label_5.setObjectName(u"label_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.label_5)

        self.parameter_5 = QComboBox(self.parameterGroupBox)
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.setObjectName(u"parameter_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.label_6 = QLabel(self.parameterGroupBox)
        self.label_6.setObjectName(u"label_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.label_6)

        self.fieldLayout_6 = QHBoxLayout()
        self.fieldLayout_6.setObjectName(u"fieldLayout_6")
        self.parameter_6 = QComboBox(self.parameterGroupBox)
        self.parameter_6.addItem("")
        self.parameter_6.setObjectName(u"parameter_6")
        self.parameter_6.setEditable(True)

        self.fieldLayout_6.addWidget(self.parameter_6)

        self.auxiliary_6 = QPushButton(self.parameterGroupBox)
        self.auxiliary_6.setObjectName(u"auxiliary_6")

        self.fieldLayout_6.addWidget(self.auxiliary_6)


        self.parameterFormLayout.setLayout(6, QFormLayout.FieldRole, self.fieldLayout_6)


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
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u672c\u5730Word\u7b54\u9898\u5668", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u672c\u5730\u9898\u5e93", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"Word \u9898\u5e93 (.docx)", None))
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u9009\u62e9\u9898\u5e93\u2026", None))
        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u9898\u76ee\u6765\u6e90", None))
        self.parameter_1.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8f93\u5165\u9898\u76ee", None))
        self.parameter_1.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u6700\u8fd1OCR\u6587\u5b57", None))
        self.parameter_1.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf", None))

        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u9898\u76ee\u5185\u5bb9 / \u53d8\u91cf\u540d", None))
        self.label_3.setText(QCoreApplication.translate("InstructionEditor", u"\u5339\u914d\u65b9\u5f0f", None))
        self.parameter_3.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u7cbe\u51c6", None))
        self.parameter_3.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5305\u542b", None))
        self.parameter_3.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6a21\u7cca", None))

        self.label_4.setText(QCoreApplication.translate("InstructionEditor", u"\u6a21\u7cca\u5339\u914d\u76f8\u4f3c\u5ea6", None))
        self.label_5.setText(QCoreApplication.translate("InstructionEditor", u"\u672a\u627e\u5230\u7b54\u6848", None))
        self.parameter_5.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519", None))
        self.parameter_5.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u8fd4\u56de\u7a7a\u503c", None))

        self.label_6.setText(QCoreApplication.translate("InstructionEditor", u"\u7b54\u6848\u53d8\u91cf", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u7b54\u6848", None))

        self.auxiliary_6.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
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

