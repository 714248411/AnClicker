# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '时间等待.ui'
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

        self.parameter_0 = QComboBox(self.parameterGroupBox)
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.parameterLabel_1 = QLabel(self.parameterGroupBox)
        self.parameterLabel_1.setObjectName(u"parameterLabel_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.parameterLabel_1)

        self.parameter_1 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")
        self.parameter_1.setDecimals(4)
        self.parameter_1.setMinimum(0.000000000000000)
        self.parameter_1.setMaximum(86400.000000000000000)
        self.parameter_1.setValue(1.000000000000000)

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.parameterLabel_2 = QLabel(self.parameterGroupBox)
        self.parameterLabel_2.setObjectName(u"parameterLabel_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.parameterLabel_2)

        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.parameterLabel_3 = QLabel(self.parameterGroupBox)
        self.parameterLabel_3.setObjectName(u"parameterLabel_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.parameterLabel_3)

        self.parameter_3 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_3.setObjectName(u"parameter_3")
        self.parameter_3.setDecimals(4)
        self.parameter_3.setMinimum(0.000000000000000)
        self.parameter_3.setMaximum(86400.000000000000000)
        self.parameter_3.setValue(1.000000000000000)

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.parameterLabel_4 = QLabel(self.parameterGroupBox)
        self.parameterLabel_4.setObjectName(u"parameterLabel_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.parameterLabel_4)

        self.parameter_4 = QComboBox(self.parameterGroupBox)
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.setObjectName(u"parameter_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.parameterLabel_5 = QLabel(self.parameterGroupBox)
        self.parameterLabel_5.setObjectName(u"parameterLabel_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.parameterLabel_5)

        self.parameter_5 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_5.setObjectName(u"parameter_5")
        self.parameter_5.setDecimals(4)
        self.parameter_5.setMinimum(0.000000000000000)
        self.parameter_5.setMaximum(86400.000000000000000)
        self.parameter_5.setValue(3.000000000000000)

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.parameterLabel_6 = QLabel(self.parameterGroupBox)
        self.parameterLabel_6.setObjectName(u"parameterLabel_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.parameterLabel_6)

        self.parameter_6 = QComboBox(self.parameterGroupBox)
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.addItem("")
        self.parameter_6.setObjectName(u"parameter_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameter_6)

        self.parameterLabel_7 = QLabel(self.parameterGroupBox)
        self.parameterLabel_7.setObjectName(u"parameterLabel_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.parameterLabel_7)

        self.parameter_7 = QLineEdit(self.parameterGroupBox)
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameter_7)

        self.parameterLabel_8 = QLabel(self.parameterGroupBox)
        self.parameterLabel_8.setObjectName(u"parameterLabel_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.LabelRole, self.parameterLabel_8)

        self.parameter_8 = QDoubleSpinBox(self.parameterGroupBox)
        self.parameter_8.setObjectName(u"parameter_8")
        self.parameter_8.setDecimals(4)
        self.parameter_8.setMinimum(0.010000000000000)
        self.parameter_8.setMaximum(60.000000000000000)
        self.parameter_8.setValue(0.200000000000000)

        self.parameterFormLayout.setWidget(8, QFormLayout.FieldRole, self.parameter_8)


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
        self.parameter_4.setCurrentIndex(1)
        self.parameter_6.setCurrentIndex(1)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u7b49\u5f85", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u7b49\u5f85", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u7b49\u5f85\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u7b49\u5f85\u7c7b\u578b", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u7b49\u5f85", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u968f\u673a\u7b49\u5f85", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5b9a\u65f6\u7b49\u5f85", None))

        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u65f6\u957f", None))
        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u5355\u4f4d", None))
        self.parameter_2.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6beb\u79d2", None))
        self.parameter_2.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u79d2", None))
        self.parameter_2.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5206\u949f", None))

        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u968f\u673a\u6700\u5c0f\u79d2\u6570", None))
        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u968f\u673a\u6700\u5c0f\u503c\u5355\u4f4d", None))
        self.parameter_4.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6beb\u79d2", None))
        self.parameter_4.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u79d2", None))
        self.parameter_4.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5206\u949f", None))

        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u968f\u673a\u6700\u5927\u79d2\u6570", None))
        self.parameterLabel_6.setText(QCoreApplication.translate("InstructionEditor", u"\u968f\u673a\u6700\u5927\u503c\u5355\u4f4d", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u6beb\u79d2", None))
        self.parameter_6.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u79d2", None))
        self.parameter_6.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5206\u949f", None))

        self.parameterLabel_7.setText(QCoreApplication.translate("InstructionEditor", u"\u76ee\u6807\u65f6\u95f4 HH:MM:SS", None))
        self.parameter_7.setText("")
        self.parameterLabel_8.setText(QCoreApplication.translate("InstructionEditor", u"\u68c0\u6d4b\u9891\u7387", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

