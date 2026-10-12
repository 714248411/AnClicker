# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '报错跳转.ui'
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
    QSpinBox, QVBoxLayout, QWidget)

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
        self.parameterLabel_0 = QLabel(self.parameterGroupBox)
        self.parameterLabel_0.setObjectName(u"parameterLabel_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.LabelRole, self.parameterLabel_0)

        self.parameter_0 = QComboBox(self.parameterGroupBox)
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.parameterLabel_1 = QLabel(self.parameterGroupBox)
        self.parameterLabel_1.setObjectName(u"parameterLabel_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.parameterLabel_1)

        self.parameter_1 = QSpinBox(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")
        self.parameter_1.setMinimum(1)
        self.parameter_1.setMaximum(1000000)

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.parameterLabel_2 = QLabel(self.parameterGroupBox)
        self.parameterLabel_2.setObjectName(u"parameterLabel_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.parameterLabel_2)

        self.parameterContainer_2 = QWidget(self.parameterGroupBox)
        self.parameterContainer_2.setObjectName(u"parameterContainer_2")
        self.parameterLayout_2 = QHBoxLayout(self.parameterContainer_2)
        self.parameterLayout_2.setObjectName(u"parameterLayout_2")
        self.parameter_2 = QLineEdit(self.parameterContainer_2)
        self.parameter_2.setObjectName(u"parameter_2")

        self.parameterLayout_2.addWidget(self.parameter_2)

        self.auxiliary_2 = QPushButton(self.parameterContainer_2)
        self.auxiliary_2.setObjectName(u"auxiliary_2")

        self.parameterLayout_2.addWidget(self.auxiliary_2)


        self.parameterFormLayout.setWidget(2, QFormLayout.FieldRole, self.parameterContainer_2)


        self.rootLayout.addWidget(self.parameterGroupBox)

        self.helpLabel = QLabel(InstructionEditor)
        self.helpLabel.setObjectName(u"helpLabel")
        self.helpLabel.setWordWrap(True)

        self.rootLayout.addWidget(self.helpLabel)

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

        QMetaObject.connectSlotsByName(InstructionEditor)
    # setupUi

    def retranslateUi(self, InstructionEditor):
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519\u8df3\u8f6c", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519\u8df3\u8f6c", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u62a5\u9519\u8df3\u8f6c\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u8df3\u8f6c\u65b9\u5f0f", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8fde\u7ebf\u8282\u70b9", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5f53\u524d\u9879\u76ee\u884c", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5176\u4ed6\u9879\u76ee\u884c", None))
        self.parameter_0.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u7ee7\u7eed\u6267\u884c", None))

        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u76ee\u6807\u884c\uff08\u8868\u683c\u5e8f\u53f7\uff0c\u4ece 1 \u5f00\u59cb\uff09", None))
        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u9879\u76ee\u8def\u5f84", None))
        self.auxiliary_2.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u9879\u76ee", None))
        self.helpLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u884c\u53f7\u6309\u5f53\u524d\u8868\u683c\u5e8f\u53f7\uff0c\u4ece\u76ee\u6807\u884c\u5f00\u59cb\uff08\u5305\u62ec\u76ee\u6807\u884c\uff09\u3002\u8fde\u7ebf\u8282\u70b9\u6a21\u5f0f\u9700\u8fde\u63a5\u5bf9\u5e94\u8f93\u51fa\uff1b\u8de8\u9879\u76ee\u8fd0\u884c\u5b8c\u6210\u540e\u8fd4\u56de\u3002\u62a5\u9519\u6a21\u5757\u4ec5\u5728\u6e90\u6307\u4ee4\u53d1\u751f\u5f02\u5e38\u65f6\u542f\u7528\u3002\u505c\u6b62\u6309\u94ae / Esc \u53ef\u4e2d\u6b62\u6574\u4e2a\u8c03\u7528\u94fe\u3002", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u8bf7\u5728\u4e3b\u754c\u9762\u8fd0\u884c", None))
    # retranslateUi

