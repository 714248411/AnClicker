# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '运行项目.ui'
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
from qt_compat.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_InstructionEditor(object):
    def setupUi(self, InstructionEditor):
        if not InstructionEditor.objectName():
            InstructionEditor.setObjectName(u"InstructionEditor")
        InstructionEditor.resize(700, 480)
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


        self.rootLayout.addWidget(self.parameterGroupBox)

        self.helpLabel = QLabel(InstructionEditor)
        self.helpLabel.setObjectName(u"helpLabel")
        self.helpLabel.setWordWrap(True)

        self.rootLayout.addWidget(self.helpLabel)

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
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u8fd0\u884c\u9879\u76ee", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u8fd0\u884c\u9879\u76ee", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u76ee\u6807\u9879\u76ee\uff08\u8868\u683c\u53ea\u5360\u4e00\u884c\uff09", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u9879\u76ee\u6587\u4ef6 *", None))
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u9879\u76ee", None))
        self.helpLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5c06\u9879\u76ee\u6587\u4ef6\u62d6\u5165\u4e0a\u65b9\u8def\u5f84\u680f\u3002\u8fd0\u884c\u5230\u672c\u884c\u65f6\u6267\u884c\u76ee\u6807\u9879\u76ee\u4e00\u6b21\uff0c\u7ed3\u675f\u540e\u8fd4\u56de\u672c\u9879\u76ee\u7ee7\u7eed\u6267\u884c\u3002\n"
"\u4f8b\u5982\uff1aA \u6700\u540e\u4e00\u884c\u8fd0\u884c B\uff0cB \u6700\u540e\u4e00\u884c\u8fd0\u884c C\u3002\n"
"\u652f\u6301\u4e2d\u6587\u3001\u7a7a\u683c\u3001\u53d8\u91cf\u8def\u5f84\uff1b\u76f8\u5bf9\u8def\u5f84\u4ee5\u8c03\u7528\u9879\u76ee\u6240\u5728\u76ee\u5f55\u4e3a\u51c6\u3002\n"
"\u505c\u6b62\u6309\u94ae / Esc \u4e2d\u65ad\u6574\u4e2a\u8c03\u7528\u94fe\u3002\u4e0d\u4f1a\u8986\u76d6\u5f53\u524d\u8868\u683c\u4e0e\u6d41\u7a0b\u56fe\u3002", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u8bf7\u5728\u4e3b\u754c\u9762\u8fd0\u884c", None))
    # retranslateUi

