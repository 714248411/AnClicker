# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OCR复制.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
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
        self.parameter_0 = QComboBox(self.parameterContainer_0)
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterLayout_0.addWidget(self.parameter_0)


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

        self.parameterContainer_2 = QWidget(self.parameterGroupBox)
        self.parameterContainer_2.setObjectName(u"parameterContainer_2")
        self.parameterLayout_2 = QHBoxLayout(self.parameterContainer_2)
        self.parameterLayout_2.setObjectName(u"parameterLayout_2")
        self.parameterLayout_2.setContentsMargins(0, 0, 0, 0)
        self.parameter_2 = QComboBox(self.parameterContainer_2)
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterLayout_2.addWidget(self.parameter_2)


        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameterContainer_2)

        self.parameterLabel_3 = QLabel(self.parameterGroupBox)
        self.parameterLabel_3.setObjectName(u"parameterLabel_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.parameterLabel_3)

        self.parameterContainer_3 = QWidget(self.parameterGroupBox)
        self.parameterContainer_3.setObjectName(u"parameterContainer_3")
        self.parameterLayout_3 = QHBoxLayout(self.parameterContainer_3)
        self.parameterLayout_3.setObjectName(u"parameterLayout_3")
        self.parameterLayout_3.setContentsMargins(0, 0, 0, 0)
        self.parameter_3 = QDoubleSpinBox(self.parameterContainer_3)
        self.parameter_3.setObjectName(u"parameter_3")
        self.parameter_3.setMinimum(0.000000000000000)
        self.parameter_3.setMaximum(1.000000000000000)
        self.parameter_3.setValue(0.500000000000000)
        self.parameter_3.setDecimals(2)

        self.parameterLayout_3.addWidget(self.parameter_3)


        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameterContainer_3)

        self.parameterLabel_4 = QLabel(self.parameterGroupBox)
        self.parameterLabel_4.setObjectName(u"parameterLabel_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.parameterLabel_4)

        self.parameterContainer_4 = QWidget(self.parameterGroupBox)
        self.parameterContainer_4.setObjectName(u"parameterContainer_4")
        self.parameterLayout_4 = QHBoxLayout(self.parameterContainer_4)
        self.parameterLayout_4.setObjectName(u"parameterLayout_4")
        self.parameterLayout_4.setContentsMargins(0, 0, 0, 0)
        self.parameter_4 = QComboBox(self.parameterContainer_4)
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.setObjectName(u"parameter_4")

        self.parameterLayout_4.addWidget(self.parameter_4)


        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameterContainer_4)

        self.parameterLabel_5 = QLabel(self.parameterGroupBox)
        self.parameterLabel_5.setObjectName(u"parameterLabel_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.parameterLabel_5)

        self.parameterContainer_5 = QWidget(self.parameterGroupBox)
        self.parameterContainer_5.setObjectName(u"parameterContainer_5")
        self.parameterLayout_5 = QHBoxLayout(self.parameterContainer_5)
        self.parameterLayout_5.setObjectName(u"parameterLayout_5")
        self.parameterLayout_5.setContentsMargins(0, 0, 0, 0)
        self.parameter_5 = QDoubleSpinBox(self.parameterContainer_5)
        self.parameter_5.setObjectName(u"parameter_5")
        self.parameter_5.setMinimum(1.000000000000000)
        self.parameter_5.setMaximum(300.000000000000000)
        self.parameter_5.setValue(30.000000000000000)
        self.parameter_5.setDecimals(2)

        self.parameterLayout_5.addWidget(self.parameter_5)


        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameterContainer_5)


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

        self.parameter_0.setCurrentIndex(0)
        self.parameter_2.setCurrentIndex(1)
        self.parameter_4.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"OCR\u590d\u5236", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"OCR\u590d\u5236", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"OCR\u590d\u5236\u53c2\u6570\uff08\u79bb\u7ebf\uff09", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u79bb\u7ebf\u5f15\u64ce", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"RapidOCR", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5fae\u4fe1OCR", None))

        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u8bc6\u522b\u533a\u57df x,y,w,h\uff08\u7a7a\u4e3a\u5168\u5c4f\uff09 *", None))
        self.parameter_1.setText("")
        self.auxiliary_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6846\u9009\u533a\u57df", None))
        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u8bc6\u522b\u540e\u64cd\u4f5c\uff08\u65e0\u9700\u53d8\u91cf\uff09", None))
        self.parameter_2.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u4ec5\u4fdd\u5b58\u6700\u8fd1OCR\u7ed3\u679c", None))
        self.parameter_2.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u590d\u5236\u5230\u526a\u8d34\u677f", None))
        self.parameter_2.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u590d\u5236\u5e76\u7c98\u8d34", None))

        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u6700\u4f4e\u8bc6\u522b\u7f6e\u4fe1\u5ea6 0\u20131", None))
        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u672a\u627e\u5230\u6587\u5b57\u65f6", None))
        self.parameter_4.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519", None))
        self.parameter_4.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u8fd4\u56de\u7a7a\u503c", None))

        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u5355\u6b21\u8bc6\u522b\u8d85\u65f6\uff08\u79d2\uff0c\u542b\u5f15\u64ce\u542f\u52a8\uff09", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

