# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '网页正文提取.ui'
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
        InstructionEditor.resize(680, 700)
        InstructionEditor.setMinimumSize(QSize(560, 480))
        self.rootLayout = QVBoxLayout(InstructionEditor)
        self.rootLayout.setObjectName(u"rootLayout")
        self.titleLabel = QLabel(InstructionEditor)
        self.titleLabel.setObjectName(u"titleLabel")

        self.rootLayout.addWidget(self.titleLabel)

        self.parameterGroupBox = QGroupBox(InstructionEditor)
        self.parameterGroupBox.setObjectName(u"parameterGroupBox")
        self.parameterFormLayout = QFormLayout(self.parameterGroupBox)
        self.parameterFormLayout.setObjectName(u"parameterFormLayout")
        self.parameterLabel_0 = QLabel(self.parameterGroupBox)
        self.parameterLabel_0.setObjectName(u"parameterLabel_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.LabelRole, self.parameterLabel_0)

        self.parameter_0 = QLineEdit(self.parameterGroupBox)
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.parameterLabel_1 = QLabel(self.parameterGroupBox)
        self.parameterLabel_1.setObjectName(u"parameterLabel_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.parameterLabel_1)

        self.parameter_1 = QComboBox(self.parameterGroupBox)
        self.parameter_1.addItem("")
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.parameterLabel_2 = QLabel(self.parameterGroupBox)
        self.parameterLabel_2.setObjectName(u"parameterLabel_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.parameterLabel_2)

        self.parameter_2 = QLineEdit(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.parameterLabel_3 = QLabel(self.parameterGroupBox)
        self.parameterLabel_3.setObjectName(u"parameterLabel_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.parameterLabel_3)

        self.parameter_3 = QLineEdit(self.parameterGroupBox)
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.parameterLabel_4 = QLabel(self.parameterGroupBox)
        self.parameterLabel_4.setObjectName(u"parameterLabel_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.parameterLabel_4)

        self.parameter_4 = QSpinBox(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setMinimum(5)
        self.parameter_4.setMaximum(180)
        self.parameter_4.setValue(60)

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.parameterLabel_5 = QLabel(self.parameterGroupBox)
        self.parameterLabel_5.setObjectName(u"parameterLabel_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.parameterLabel_5)

        self.parameter_5 = QSpinBox(self.parameterGroupBox)
        self.parameter_5.setObjectName(u"parameter_5")
        self.parameter_5.setMinimum(500)
        self.parameter_5.setMaximum(200000)
        self.parameter_5.setValue(20000)

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.parameterLabel_6 = QLabel(self.parameterGroupBox)
        self.parameterLabel_6.setObjectName(u"parameterLabel_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.parameterLabel_6)

        self.parameterContainer_6 = QWidget(self.parameterGroupBox)
        self.parameterContainer_6.setObjectName(u"parameterContainer_6")
        self.parameterLayout_6 = QHBoxLayout(self.parameterContainer_6)
        self.parameterLayout_6.setObjectName(u"parameterLayout_6")
        self.parameterLayout_6.setContentsMargins(0, 0, 0, 0)
        self.parameter_6 = QComboBox(self.parameterContainer_6)
        self.parameter_6.addItem("")
        self.parameter_6.setObjectName(u"parameter_6")
        self.parameter_6.setEditable(True)

        self.parameterLayout_6.addWidget(self.parameter_6)

        self.auxiliary_6 = QPushButton(self.parameterContainer_6)
        self.auxiliary_6.setObjectName(u"auxiliary_6")

        self.parameterLayout_6.addWidget(self.auxiliary_6)


        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameterContainer_6)


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
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u7f51\u9875\u6b63\u6587\u63d0\u53d6", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u7f51\u9875\u6b63\u6587\u63d0\u53d6", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u7f51\u9875\u6b63\u6587\u63d0\u53d6\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u7f51\u9875\u5730\u5740 *", None))
        self.parameter_0.setText("")
        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u63d0\u53d6\u5185\u5bb9", None))
        self.parameter_1.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6b63\u6587", None))

        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u5185\u5bb9 CSS \u9009\u62e9\u5668\uff08\u53ef\u9009\uff09", None))
        self.parameter_2.setText("")
        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u7b49\u5f85 CSS \u5143\u7d20\uff08\u53ef\u9009\uff09", None))
        self.parameter_3.setText("")
        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u9875\u9762\u8d85\u65f6\uff08\u79d2\uff09", None))
        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u6700\u5927\u5b57\u7b26\u6570", None))
        self.parameterLabel_6.setText(QCoreApplication.translate("InstructionEditor", u"\u4fdd\u5b58\u5230\u53d8\u91cf *", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u7f51\u9875\u6b63\u6587", None))

        self.auxiliary_6.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

