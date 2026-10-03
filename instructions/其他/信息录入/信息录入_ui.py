# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '信息录入.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

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

        self.parameterContainer_0 = QWidget(self.parameterGroupBox)
        self.parameterContainer_0.setObjectName(u"parameterContainer_0")
        self.parameterLayout_0 = QHBoxLayout(self.parameterContainer_0)
        self.parameterLayout_0.setObjectName(u"parameterLayout_0")
        self.parameterLayout_0.setContentsMargins(0, 0, 0, 0)
        self.parameter_0 = QLineEdit(self.parameterContainer_0)
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterLayout_0.addWidget(self.parameter_0)

        self.auxiliary_0 = QPushButton(self.parameterContainer_0)
        self.auxiliary_0.setObjectName(u"auxiliary_0")

        self.parameterLayout_0.addWidget(self.auxiliary_0)


        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameterContainer_0)

        self.parameterLabel_1 = QLabel(self.parameterGroupBox)
        self.parameterLabel_1.setObjectName(u"parameterLabel_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.parameterLabel_1)

        self.parameterContainer_1 = QWidget(self.parameterGroupBox)
        self.parameterContainer_1.setObjectName(u"parameterContainer_1")
        self.parameterLayout_1 = QHBoxLayout(self.parameterContainer_1)
        self.parameterLayout_1.setObjectName(u"parameterLayout_1")
        self.parameterLayout_1.setContentsMargins(0, 0, 0, 0)
        self.parameter_1 = QLineEdit(self.parameterContainer_1)
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterLayout_1.addWidget(self.parameter_1)

        self.auxiliary_1 = QPushButton(self.parameterContainer_1)
        self.auxiliary_1.setObjectName(u"auxiliary_1")

        self.parameterLayout_1.addWidget(self.auxiliary_1)


        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameterContainer_1)

        self.parameterLabel_2 = QLabel(self.parameterGroupBox)
        self.parameterLabel_2.setObjectName(u"parameterLabel_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.parameterLabel_2)

        self.parameter_2 = QLineEdit(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.parameterLabel_3 = QLabel(self.parameterGroupBox)
        self.parameterLabel_3.setObjectName(u"parameterLabel_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.parameterLabel_3)

        self.parameterContainer_3 = QWidget(self.parameterGroupBox)
        self.parameterContainer_3.setObjectName(u"parameterContainer_3")
        self.parameterLayout_3 = QHBoxLayout(self.parameterContainer_3)
        self.parameterLayout_3.setObjectName(u"parameterLayout_3")
        self.parameterLayout_3.setContentsMargins(0, 0, 0, 0)
        self.parameter_3 = QLineEdit(self.parameterContainer_3)
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterLayout_3.addWidget(self.parameter_3)

        self.auxiliary_3 = QPushButton(self.parameterContainer_3)
        self.auxiliary_3.setObjectName(u"auxiliary_3")

        self.parameterLayout_3.addWidget(self.auxiliary_3)


        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameterContainer_3)

        self.parameterLabel_4 = QLabel(self.parameterGroupBox)
        self.parameterLabel_4.setObjectName(u"parameterLabel_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.parameterLabel_4)

        self.parameter_4 = QCheckBox(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setChecked(False)

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.parameterLabel_5 = QLabel(self.parameterGroupBox)
        self.parameterLabel_5.setObjectName(u"parameterLabel_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.parameterLabel_5)

        self.parameter_5 = QCheckBox(self.parameterGroupBox)
        self.parameter_5.setObjectName(u"parameter_5")
        self.parameter_5.setChecked(False)

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.parameterLabel_6 = QLabel(self.parameterGroupBox)
        self.parameterLabel_6.setObjectName(u"parameterLabel_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.parameterLabel_6)

        self.parameter_6 = QLineEdit(self.parameterGroupBox)
        self.parameter_6.setObjectName(u"parameter_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameter_6)

        self.parameterLabel_7 = QLabel(self.parameterGroupBox)
        self.parameterLabel_7.setObjectName(u"parameterLabel_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.parameterLabel_7)

        self.parameter_7 = QComboBox(self.parameterGroupBox)
        self.parameter_7.addItem("")
        self.parameter_7.addItem("")
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameter_7)


        self.rootLayout.addWidget(self.parameterGroupBox)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

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

        self.footerSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.footerSpacer)

        self.buttonBox = QDialogButtonBox(InstructionEditor)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.footerLayout.addWidget(self.buttonBox)


        self.rootLayout.addLayout(self.footerLayout)


        self.retranslateUi(InstructionEditor)

        self.parameter_7.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u4fe1\u606f\u5f55\u5165", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u4fe1\u606f\u5f55\u5165", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u4fe1\u606f\u5f55\u5165\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u8f93\u5165\u4f4d\u7f6e\u56fe\u50cf *", None))
        self.parameter_0.setText("")
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u56fe\u50cf", None))
        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u5de5\u4f5c\u7c3f\u8def\u5f84 *", None))
        self.parameter_1.setText("")
        self.auxiliary_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8Excel", None))
        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u5de5\u4f5c\u8868", None))
        self.parameter_2.setText("")
        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u5355\u5143\u683c *", None))
        self.parameter_3.setText(QCoreApplication.translate("InstructionEditor", u"A1", None))
        self.auxiliary_3.setText(QCoreApplication.translate("InstructionEditor", u"\u8f93\u5165\u5355\u5143\u683c", None))
        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u6309\u5faa\u73af\u6b21\u6570\u9012\u589e\u884c", None))
        self.parameter_4.setText(QCoreApplication.translate("InstructionEditor", u"\u542f\u7528", None))
        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u9010\u5b57\u7b26\u6a21\u62df\u8f93\u5165", None))
        self.parameter_5.setText(QCoreApplication.translate("InstructionEditor", u"\u542f\u7528", None))
        self.parameterLabel_6.setText(QCoreApplication.translate("InstructionEditor", u"\u56fe\u50cf\u67e5\u627e\u8d85\u65f6", None))
        self.parameter_6.setText(QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u7565\u8fc7", None))
        self.parameterLabel_7.setText(QCoreApplication.translate("InstructionEditor", u"Excel\u7a7a\u503c\u5904\u7406", None))
        self.parameter_7.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u629b\u51fa\u5f02\u5e38", None))
        self.parameter_7.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))

        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

