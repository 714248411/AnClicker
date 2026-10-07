# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '颜色判断.ui'
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
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_InstructionEditor(object):
    def setupUi(self, InstructionEditor):
        if not InstructionEditor.objectName():
            InstructionEditor.setObjectName(u"InstructionEditor")
        InstructionEditor.resize(700, 560)
        self.rootLayout = QVBoxLayout(InstructionEditor)
        self.rootLayout.setObjectName(u"rootLayout")
        self.titleLabel = QLabel(InstructionEditor)
        self.titleLabel.setObjectName(u"titleLabel")

        self.rootLayout.addWidget(self.titleLabel)

        self.parameterGroupBox = QGroupBox(InstructionEditor)
        self.parameterGroupBox.setObjectName(u"parameterGroupBox")
        self.parameterFormLayout = QFormLayout(self.parameterGroupBox)
        self.parameterFormLayout.setObjectName(u"parameterFormLayout")
        self.label0 = QLabel(self.parameterGroupBox)
        self.label0.setObjectName(u"label0")

        self.parameterFormLayout.setWidget(0, QFormLayout.LabelRole, self.label0)

        self.row0 = QHBoxLayout()
        self.row0.setObjectName(u"row0")
        self.parameter_0 = QLineEdit(self.parameterGroupBox)
        self.parameter_0.setObjectName(u"parameter_0")

        self.row0.addWidget(self.parameter_0)

        self.auxiliary_0 = QPushButton(self.parameterGroupBox)
        self.auxiliary_0.setObjectName(u"auxiliary_0")

        self.row0.addWidget(self.auxiliary_0)


        self.parameterFormLayout.setLayout(0, QFormLayout.FieldRole, self.row0)

        self.label1 = QLabel(self.parameterGroupBox)
        self.label1.setObjectName(u"label1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label1)

        self.row1 = QHBoxLayout()
        self.row1.setObjectName(u"row1")
        self.parameter_1 = QLineEdit(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")

        self.row1.addWidget(self.parameter_1)

        self.auxiliary_1 = QPushButton(self.parameterGroupBox)
        self.auxiliary_1.setObjectName(u"auxiliary_1")

        self.row1.addWidget(self.auxiliary_1)


        self.parameterFormLayout.setLayout(1, QFormLayout.FieldRole, self.row1)

        self.label2 = QLabel(self.parameterGroupBox)
        self.label2.setObjectName(u"label2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label2)

        self.parameter_2 = QSpinBox(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")
        self.parameter_2.setMaximum(255)

        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameter_2)

        self.label3 = QLabel(self.parameterGroupBox)
        self.label3.setObjectName(u"label3")

        self.parameterFormLayout.setWidget(3, QFormLayout.LabelRole, self.label3)

        self.parameter_3 = QComboBox(self.parameterGroupBox)
        self.parameter_3.addItem("")
        self.parameter_3.addItem("")
        self.parameter_3.setObjectName(u"parameter_3")

        self.parameterFormLayout.setWidget(3, QFormLayout.FieldRole, self.parameter_3)

        self.label4 = QLabel(self.parameterGroupBox)
        self.label4.setObjectName(u"label4")

        self.parameterFormLayout.setWidget(4, QFormLayout.LabelRole, self.label4)

        self.row4 = QHBoxLayout()
        self.row4.setObjectName(u"row4")
        self.parameter_4 = QComboBox(self.parameterGroupBox)
        self.parameter_4.setObjectName(u"parameter_4")
        self.parameter_4.setEditable(True)

        self.row4.addWidget(self.parameter_4)

        self.auxiliary_4 = QPushButton(self.parameterGroupBox)
        self.auxiliary_4.setObjectName(u"auxiliary_4")

        self.row4.addWidget(self.auxiliary_4)


        self.parameterFormLayout.setLayout(4, QFormLayout.FieldRole, self.row4)


        self.rootLayout.addWidget(self.parameterGroupBox)

        self.hint = QLabel(InstructionEditor)
        self.hint.setObjectName(u"hint")
        self.hint.setWordWrap(True)

        self.rootLayout.addWidget(self.hint)

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

        self.commonFormLayout.setWidget(0, QFormLayout.FieldRole, self.repeatSpinBox)

        self.errorLabel = QLabel(self.commonGroupBox)
        self.errorLabel.setObjectName(u"errorLabel")

        self.commonFormLayout.setWidget(1, QFormLayout.LabelRole, self.errorLabel)

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

        self.footer = QHBoxLayout()
        self.footer.setObjectName(u"footer")
        self.testButton = QPushButton(InstructionEditor)
        self.testButton.setObjectName(u"testButton")

        self.footer.addWidget(self.testButton)

        self.buttonBox = QDialogButtonBox(InstructionEditor)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.footer.addWidget(self.buttonBox)


        self.rootLayout.addLayout(self.footer)


        self.retranslateUi(InstructionEditor)

        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u989c\u8272\u5224\u65ad", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u989c\u8272\u5224\u65ad\uff08\u53f3\u4fa7\uff1a\u662f\uff0c\u4e0a\u65b9\uff1a\u5426\uff09", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u989c\u8272\u5224\u65ad\u53c2\u6570", None))
        self.label0.setText(QCoreApplication.translate("InstructionEditor", u"\u68c0\u6d4b\u5750\u6807 x,y", None))
        self.parameter_0.setText(QCoreApplication.translate("InstructionEditor", u"0,0", None))
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u5750\u6807", None))
        self.label1.setText(QCoreApplication.translate("InstructionEditor", u"\u989c\u8272 #RRGGBB \u6216 R,G,B", None))
        self.parameter_1.setText(QCoreApplication.translate("InstructionEditor", u"#FFFFFF", None))
        self.auxiliary_1.setText(QCoreApplication.translate("InstructionEditor", u"\u9009\u62e9\u989c\u8272", None))
        self.label2.setText(QCoreApplication.translate("InstructionEditor", u"RGB \u5355\u901a\u9053\u5bb9\u5dee\uff080\u2013255\uff09", None))
        self.label3.setText(QCoreApplication.translate("InstructionEditor", u"\u5224\u65ad\u65b9\u5f0f", None))
        self.parameter_3.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u76f8\u7b49", None))
        self.parameter_3.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4e0d\u76f8\u7b49", None))

        self.label4.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed3\u679c\u53d8\u91cf\uff08\u53ef\u9009\uff09", None))
        self.auxiliary_4.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.hint.setText(QCoreApplication.translate("InstructionEditor", u"\u5bb9\u5dee 0 \u4e3a\u5b8c\u5168\u4e00\u81f4\uff1b\u65e0\u8fde\u7ebf\u65f6\u8bb0\u5f55\u7ed3\u679c\u540e\u7ee7\u7eed\uff0c\u5206\u652f\u8fde\u7ebf\u4e0e\u6761\u4ef6\u5224\u65ad\u76f8\u540c\u3002", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

