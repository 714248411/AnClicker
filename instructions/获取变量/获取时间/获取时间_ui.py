# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '获取时间.ui'
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
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

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

        self.parameter_1 = QComboBox(self.parameterGroupBox)
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.addItem("")
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)


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

        self.parameter_1.setCurrentIndex(0)
        self.errorPolicyComboBox.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u65f6\u95f4", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u65f6\u95f4", None))
        self.titleLabel.setStyleSheet(QCoreApplication.translate("InstructionEditor", u"font-size: 18px; font-weight: 600;", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u65f6\u95f4\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf\u540d\u79f0 *", None))
        self.parameter_0.setText(QCoreApplication.translate("InstructionEditor", u"\u5f53\u524d\u65f6\u95f4", None))
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u9009\u62e9\u53d8\u91cf", None))
        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u683c\u5f0f *", None))
        self.parameter_1.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u5e74-\u6708-\u65e5 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.parameter_1.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5e74/\u6708/\u65e5 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.parameter_1.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6708/\u65e5/\u5e74 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.parameter_1.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u65e5-\u6708-\u5e74 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.parameter_1.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u5e74-\u6708-\u65e5", None))
        self.parameter_1.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u6708/\u65e5/\u5e74", None))
        self.parameter_1.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u65e5-\u6708-\u5e74", None))
        self.parameter_1.setItemText(7, QCoreApplication.translate("InstructionEditor", u"\u6708/\u5e74", None))
        self.parameter_1.setItemText(8, QCoreApplication.translate("InstructionEditor", u"\u65f6\u95f4\u6233", None))

        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
    # retranslateUi

