# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'OCR模糊找字返回坐标.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qt_compat.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from qt_compat.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from qt_compat.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

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
        self.parameter_2 = QLineEdit(self.parameterContainer_2)
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
        self.parameter_3 = QComboBox(self.parameterContainer_3)
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.setObjectName(u"parameter_3")

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
        self.parameter_4 = QDoubleSpinBox(self.parameterContainer_4)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setMinimum(0.010000000000000)
        self.parameter_4.setMaximum(1.000000000000000)
        self.parameter_4.setValue(0.800000000000000)
        self.parameter_4.setDecimals(2)

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
        self.parameter_5 = QSpinBox(self.parameterContainer_5)
        self.parameter_5.setObjectName(u"parameter_5")
        self.parameter_5.setMinimum(1)
        self.parameter_5.setMaximum(10000)
        self.parameter_5.setValue(1)

        self.parameterLayout_5.addWidget(self.parameter_5)


        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameterContainer_5)

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
        self.parameter_6.addItem("")
        self.parameter_6.setObjectName(u"parameter_6")

        self.parameterLayout_6.addWidget(self.parameter_6)


        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameterContainer_6)

        self.parameterLabel_7 = QLabel(self.parameterGroupBox)
        self.parameterLabel_7.setObjectName(u"parameterLabel_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.parameterLabel_7)

        self.parameterContainer_7 = QWidget(self.parameterGroupBox)
        self.parameterContainer_7.setObjectName(u"parameterContainer_7")
        self.parameterLayout_7 = QHBoxLayout(self.parameterContainer_7)
        self.parameterLayout_7.setObjectName(u"parameterLayout_7")
        self.parameterLayout_7.setContentsMargins(0, 0, 0, 0)
        self.parameter_7 = QLineEdit(self.parameterContainer_7)
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterLayout_7.addWidget(self.parameter_7)


        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameterContainer_7)

        self.parameterLabel_8 = QLabel(self.parameterGroupBox)
        self.parameterLabel_8.setObjectName(u"parameterLabel_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.LabelRole, self.parameterLabel_8)

        self.parameterContainer_8 = QWidget(self.parameterGroupBox)
        self.parameterContainer_8.setObjectName(u"parameterContainer_8")
        self.parameterLayout_8 = QHBoxLayout(self.parameterContainer_8)
        self.parameterLayout_8.setObjectName(u"parameterLayout_8")
        self.parameterLayout_8.setContentsMargins(0, 0, 0, 0)
        self.parameter_8 = QCheckBox(self.parameterContainer_8)
        self.parameter_8.setObjectName(u"parameter_8")
        self.parameter_8.setChecked(True)

        self.parameterLayout_8.addWidget(self.parameter_8)


        self.parameterFormLayout.setWidget(8, QFormLayout.FieldRole, self.parameterContainer_8)

        self.parameterLabel_9 = QLabel(self.parameterGroupBox)
        self.parameterLabel_9.setObjectName(u"parameterLabel_9")

        self.parameterFormLayout.setWidget(9, QFormLayout.LabelRole, self.parameterLabel_9)

        self.parameterContainer_9 = QWidget(self.parameterGroupBox)
        self.parameterContainer_9.setObjectName(u"parameterContainer_9")
        self.parameterLayout_9 = QHBoxLayout(self.parameterContainer_9)
        self.parameterLayout_9.setObjectName(u"parameterLayout_9")
        self.parameterLayout_9.setContentsMargins(0, 0, 0, 0)
        self.parameter_9 = QCheckBox(self.parameterContainer_9)
        self.parameter_9.setObjectName(u"parameter_9")
        self.parameter_9.setChecked(True)

        self.parameterLayout_9.addWidget(self.parameter_9)


        self.parameterFormLayout.setWidget(9, QFormLayout.FieldRole, self.parameterContainer_9)

        self.parameterLabel_10 = QLabel(self.parameterGroupBox)
        self.parameterLabel_10.setObjectName(u"parameterLabel_10")

        self.parameterFormLayout.setWidget(10, QFormLayout.LabelRole, self.parameterLabel_10)

        self.parameterContainer_10 = QWidget(self.parameterGroupBox)
        self.parameterContainer_10.setObjectName(u"parameterContainer_10")
        self.parameterLayout_10 = QHBoxLayout(self.parameterContainer_10)
        self.parameterLayout_10.setObjectName(u"parameterLayout_10")
        self.parameterLayout_10.setContentsMargins(0, 0, 0, 0)
        self.parameter_10 = QDoubleSpinBox(self.parameterContainer_10)
        self.parameter_10.setObjectName(u"parameter_10")
        self.parameter_10.setMinimum(0.000000000000000)
        self.parameter_10.setMaximum(1.000000000000000)
        self.parameter_10.setValue(0.500000000000000)
        self.parameter_10.setDecimals(2)

        self.parameterLayout_10.addWidget(self.parameter_10)


        self.parameterFormLayout.setWidget(10, QFormLayout.FieldRole, self.parameterContainer_10)

        self.parameterLabel_11 = QLabel(self.parameterGroupBox)
        self.parameterLabel_11.setObjectName(u"parameterLabel_11")

        self.parameterFormLayout.setWidget(11, QFormLayout.LabelRole, self.parameterLabel_11)

        self.parameterContainer_11 = QWidget(self.parameterGroupBox)
        self.parameterContainer_11.setObjectName(u"parameterContainer_11")
        self.parameterLayout_11 = QHBoxLayout(self.parameterContainer_11)
        self.parameterLayout_11.setObjectName(u"parameterLayout_11")
        self.parameterLayout_11.setContentsMargins(0, 0, 0, 0)
        self.parameter_11 = QComboBox(self.parameterContainer_11)
        self.parameter_11.addItem("")
        self.parameter_11.setObjectName(u"parameter_11")
        self.parameter_11.setEditable(True)

        self.parameterLayout_11.addWidget(self.parameter_11)

        self.auxiliary_11 = QPushButton(self.parameterContainer_11)
        self.auxiliary_11.setObjectName(u"auxiliary_11")

        self.parameterLayout_11.addWidget(self.auxiliary_11)


        self.parameterFormLayout.setWidget(11, QFormLayout.FieldRole, self.parameterContainer_11)

        self.parameterLabel_12 = QLabel(self.parameterGroupBox)
        self.parameterLabel_12.setObjectName(u"parameterLabel_12")

        self.parameterFormLayout.setWidget(12, QFormLayout.LabelRole, self.parameterLabel_12)

        self.parameterContainer_12 = QWidget(self.parameterGroupBox)
        self.parameterContainer_12.setObjectName(u"parameterContainer_12")
        self.parameterLayout_12 = QHBoxLayout(self.parameterContainer_12)
        self.parameterLayout_12.setObjectName(u"parameterLayout_12")
        self.parameterLayout_12.setContentsMargins(0, 0, 0, 0)
        self.parameter_12 = QComboBox(self.parameterContainer_12)
        self.parameter_12.addItem("")
        self.parameter_12.addItem("")
        self.parameter_12.setObjectName(u"parameter_12")

        self.parameterLayout_12.addWidget(self.parameter_12)


        self.parameterFormLayout.setWidget(12, QFormLayout.FieldRole, self.parameterContainer_12)

        self.parameterLabel_13 = QLabel(self.parameterGroupBox)
        self.parameterLabel_13.setObjectName(u"parameterLabel_13")

        self.parameterFormLayout.setWidget(13, QFormLayout.LabelRole, self.parameterLabel_13)

        self.parameterContainer_13 = QWidget(self.parameterGroupBox)
        self.parameterContainer_13.setObjectName(u"parameterContainer_13")
        self.parameterLayout_13 = QHBoxLayout(self.parameterContainer_13)
        self.parameterLayout_13.setObjectName(u"parameterLayout_13")
        self.parameterLayout_13.setContentsMargins(0, 0, 0, 0)
        self.parameter_13 = QDoubleSpinBox(self.parameterContainer_13)
        self.parameter_13.setObjectName(u"parameter_13")
        self.parameter_13.setMinimum(1.000000000000000)
        self.parameter_13.setMaximum(300.000000000000000)
        self.parameter_13.setValue(30.000000000000000)
        self.parameter_13.setDecimals(2)

        self.parameterLayout_13.addWidget(self.parameter_13)


        self.parameterFormLayout.setWidget(13, QFormLayout.FieldRole, self.parameterContainer_13)


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
        self.parameter_3.setCurrentIndex(2)
        self.parameter_6.setCurrentIndex(0)
        self.parameter_11.setCurrentIndex(0)
        self.parameter_12.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"OCR\u6a21\u7cca\u627e\u5b57\u8fd4\u56de\u5750\u6807", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"OCR\u6a21\u7cca\u627e\u5b57\u8fd4\u56de\u5750\u6807", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"OCR\u6a21\u7cca\u627e\u5b57\u8fd4\u56de\u5750\u6807\u53c2\u6570\uff08\u79bb\u7ebf\uff09", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u79bb\u7ebf\u5f15\u64ce", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"RapidOCR", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5fae\u4fe1OCR", None))

        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u8bc6\u522b\u533a\u57df x,y,w,h\uff08\u7a7a\u4e3a\u5168\u5c4f\uff09", None))
        self.parameter_1.setText("")
        self.auxiliary_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6846\u9009\u533a\u57df", None))
        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u76ee\u6807\u6587\u5b57\uff08\u533a\u57df\u6a21\u5757\u53ef\u7559\u7a7a\u5339\u914d\u5168\u90e8\u6587\u5b57\u6846\uff09 *", None))
        self.parameter_2.setText("")
        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u6587\u5b57\u5339\u914d\u65b9\u5f0f", None))
        self.parameter_3.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u7cbe\u51c6", None))
        self.parameter_3.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5305\u542b", None))
        self.parameter_3.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6a21\u7cca", None))

        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u6a21\u7cca\u76f8\u4f3c\u5ea6 0\u20131", None))
        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u6392\u5e8f\u540e\u7684\u7b2c\u51e0\u4e2a\u533a\u57df\uff08\u4ece1\u5f00\u59cb\uff09", None))
        self.parameterLabel_6.setText(QCoreApplication.translate("InstructionEditor", u"\u5339\u914d\u533a\u57df\u6392\u5e8f", None))
        self.parameter_6.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u4ece\u4e0a\u5230\u4e0b", None))
        self.parameter_6.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u79bb\u951a\u70b9\u6700\u8fd1", None))

        self.parameterLabel_7.setText(QCoreApplication.translate("InstructionEditor", u"\u5c4f\u5e55\u951a\u70b9 x,y\uff08\u7a7a\u4e3a\u8bc6\u522b\u8303\u56f4\u4e2d\u5fc3\uff09", None))
        self.parameter_7.setText("")
        self.parameterLabel_8.setText(QCoreApplication.translate("InstructionEditor", u"\u5ffd\u7565\u82f1\u6587\u5927\u5c0f\u5199", None))
        self.parameter_8.setText(QCoreApplication.translate("InstructionEditor", u"\u542f\u7528", None))
        self.parameterLabel_9.setText(QCoreApplication.translate("InstructionEditor", u"\u5ffd\u7565\u7a7a\u767d\u5b57\u7b26", None))
        self.parameter_9.setText(QCoreApplication.translate("InstructionEditor", u"\u542f\u7528", None))
        self.parameterLabel_10.setText(QCoreApplication.translate("InstructionEditor", u"\u6700\u4f4e\u8bc6\u522b\u7f6e\u4fe1\u5ea6 0\u20131", None))
        self.parameterLabel_11.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed3\u679c\u53d8\u91cf\uff08\u53ef\u81ea\u5b9a\u4e49\uff09 *", None))
        self.parameter_11.setItemText(0, QCoreApplication.translate("InstructionEditor", u"OCR\u5750\u6807", None))

        self.auxiliary_11.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.parameterLabel_12.setText(QCoreApplication.translate("InstructionEditor", u"\u672a\u627e\u5230\u6587\u5b57\u65f6", None))
        self.parameter_12.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519", None))
        self.parameter_12.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u8fd4\u56de\u7a7a\u503c", None))

        self.parameterLabel_13.setText(QCoreApplication.translate("InstructionEditor", u"\u5355\u6b21\u8bc6\u522b\u8d85\u65f6\uff08\u79d2\uff0c\u542b\u5f15\u64ce\u542f\u52a8\uff09", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

