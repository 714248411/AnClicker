# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '变量比较.ui'
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

        self.parameterContainer_0 = QWidget(self.parameterGroupBox)
        self.parameterContainer_0.setObjectName(u"parameterContainer_0")
        self.parameterLayout_0 = QHBoxLayout(self.parameterContainer_0)
        self.parameterLayout_0.setObjectName(u"parameterLayout_0")
        self.parameter_0 = QComboBox(self.parameterContainer_0)
        self.parameter_0.setObjectName(u"parameter_0")
        self.parameter_0.setEditable(True)

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
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.parameterLabel_2 = QLabel(self.parameterGroupBox)
        self.parameterLabel_2.setObjectName(u"parameterLabel_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.parameterLabel_2)

        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.addItem("")
        self.parameter_2.addItem("")
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

        self.parameter_4 = QComboBox(self.parameterGroupBox)
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.addItem("")
        self.parameter_4.setObjectName(u"parameter_4")

        self.parameterFormLayout.setWidget(4, QFormLayout.FieldRole, self.parameter_4)

        self.parameterLabel_5 = QLabel(self.parameterGroupBox)
        self.parameterLabel_5.setObjectName(u"parameterLabel_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.LabelRole, self.parameterLabel_5)

        self.parameter_5 = QComboBox(self.parameterGroupBox)
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.addItem("")
        self.parameter_5.setObjectName(u"parameter_5")

        self.parameterFormLayout.setWidget(5, QFormLayout.FieldRole, self.parameter_5)

        self.parameterLabel_6 = QLabel(self.parameterGroupBox)
        self.parameterLabel_6.setObjectName(u"parameterLabel_6")

        self.parameterFormLayout.setWidget(6, QFormLayout.LabelRole, self.parameterLabel_6)

        self.parameter_6 = QSpinBox(self.parameterGroupBox)
        self.parameter_6.setObjectName(u"parameter_6")
        self.parameter_6.setMinimum(1)
        self.parameter_6.setMaximum(1000000)

        self.parameterFormLayout.setWidget(6, QFormLayout.FieldRole, self.parameter_6)

        self.parameterLabel_7 = QLabel(self.parameterGroupBox)
        self.parameterLabel_7.setObjectName(u"parameterLabel_7")

        self.parameterFormLayout.setWidget(7, QFormLayout.LabelRole, self.parameterLabel_7)

        self.parameterContainer_7 = QWidget(self.parameterGroupBox)
        self.parameterContainer_7.setObjectName(u"parameterContainer_7")
        self.parameterLayout_7 = QHBoxLayout(self.parameterContainer_7)
        self.parameterLayout_7.setObjectName(u"parameterLayout_7")
        self.parameter_7 = QLineEdit(self.parameterContainer_7)
        self.parameter_7.setObjectName(u"parameter_7")

        self.parameterLayout_7.addWidget(self.parameter_7)

        self.auxiliary_7 = QPushButton(self.parameterContainer_7)
        self.auxiliary_7.setObjectName(u"auxiliary_7")

        self.parameterLayout_7.addWidget(self.auxiliary_7)


        self.parameterFormLayout.setWidget(7, QFormLayout.FieldRole, self.parameterContainer_7)

        self.parameterLabel_8 = QLabel(self.parameterGroupBox)
        self.parameterLabel_8.setObjectName(u"parameterLabel_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.LabelRole, self.parameterLabel_8)

        self.parameter_8 = QComboBox(self.parameterGroupBox)
        self.parameter_8.addItem("")
        self.parameter_8.addItem("")
        self.parameter_8.addItem("")
        self.parameter_8.addItem("")
        self.parameter_8.setObjectName(u"parameter_8")

        self.parameterFormLayout.setWidget(8, QFormLayout.FieldRole, self.parameter_8)

        self.parameterLabel_9 = QLabel(self.parameterGroupBox)
        self.parameterLabel_9.setObjectName(u"parameterLabel_9")

        self.parameterFormLayout.setWidget(9, QFormLayout.LabelRole, self.parameterLabel_9)

        self.parameter_9 = QSpinBox(self.parameterGroupBox)
        self.parameter_9.setObjectName(u"parameter_9")
        self.parameter_9.setMinimum(1)
        self.parameter_9.setMaximum(1000000)

        self.parameterFormLayout.setWidget(9, QFormLayout.FieldRole, self.parameter_9)

        self.parameterLabel_10 = QLabel(self.parameterGroupBox)
        self.parameterLabel_10.setObjectName(u"parameterLabel_10")

        self.parameterFormLayout.setWidget(10, QFormLayout.LabelRole, self.parameterLabel_10)

        self.parameterContainer_10 = QWidget(self.parameterGroupBox)
        self.parameterContainer_10.setObjectName(u"parameterContainer_10")
        self.parameterLayout_10 = QHBoxLayout(self.parameterContainer_10)
        self.parameterLayout_10.setObjectName(u"parameterLayout_10")
        self.parameter_10 = QLineEdit(self.parameterContainer_10)
        self.parameter_10.setObjectName(u"parameter_10")

        self.parameterLayout_10.addWidget(self.parameter_10)

        self.auxiliary_10 = QPushButton(self.parameterContainer_10)
        self.auxiliary_10.setObjectName(u"auxiliary_10")

        self.parameterLayout_10.addWidget(self.auxiliary_10)


        self.parameterFormLayout.setWidget(10, QFormLayout.FieldRole, self.parameterContainer_10)


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
        InstructionEditor.setWindowTitle(QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf\u6bd4\u8f83", None))
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf\u6bd4\u8f83", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf\u6bd4\u8f83\u53c2\u6570", None))
        self.parameterLabel_0.setText(QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf", None))
        self.auxiliary_0.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.parameterLabel_1.setText(QCoreApplication.translate("InstructionEditor", u"\u6bd4\u8f83\u6761\u4ef6", None))
        self.parameter_1.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u7b49\u4e8e", None))
        self.parameter_1.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u4e0d\u7b49\u4e8e", None))
        self.parameter_1.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5927\u4e8e", None))
        self.parameter_1.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u5927\u4e8e\u7b49\u4e8e", None))
        self.parameter_1.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u5c0f\u4e8e", None))
        self.parameter_1.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u5c0f\u4e8e\u7b49\u4e8e", None))
        self.parameter_1.setItemText(6, QCoreApplication.translate("InstructionEditor", u"\u5305\u542b", None))
        self.parameter_1.setItemText(7, QCoreApplication.translate("InstructionEditor", u"\u4e0d\u5305\u542b", None))

        self.parameterLabel_2.setText(QCoreApplication.translate("InstructionEditor", u"\u6bd4\u8f83\u5bf9\u8c61", None))
        self.parameter_2.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u56fa\u5b9a\u503c", None))
        self.parameter_2.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u53d8\u91cf", None))

        self.parameterLabel_3.setText(QCoreApplication.translate("InstructionEditor", u"\u6bd4\u8f83\u503c", None))
        self.parameterLabel_4.setText(QCoreApplication.translate("InstructionEditor", u"\u6bd4\u8f83\u7c7b\u578b", None))
        self.parameter_4.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8", None))
        self.parameter_4.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u6570\u5b57", None))
        self.parameter_4.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u6587\u672c", None))

        self.parameterLabel_5.setText(QCoreApplication.translate("InstructionEditor", u"\u662f\u8df3\u8f6c\u65b9\u5f0f", None))
        self.parameter_5.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8fde\u7ebf\u8282\u70b9", None))
        self.parameter_5.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5f53\u524d\u9879\u76ee\u884c", None))
        self.parameter_5.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5176\u4ed6\u9879\u76ee\u884c", None))
        self.parameter_5.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u7ee7\u7eed\u6267\u884c", None))

        self.parameterLabel_6.setText(QCoreApplication.translate("InstructionEditor", u"\u662f\u76ee\u6807\u884c\uff08\u8868\u683c\u5e8f\u53f7\uff0c\u4ece 1 \u5f00\u59cb\uff09", None))
        self.parameterLabel_7.setText(QCoreApplication.translate("InstructionEditor", u"\u662f\u9879\u76ee\u8def\u5f84", None))
        self.auxiliary_7.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u9879\u76ee", None))
        self.parameterLabel_8.setText(QCoreApplication.translate("InstructionEditor", u"\u5426\u8df3\u8f6c\u65b9\u5f0f", None))
        self.parameter_8.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8fde\u7ebf\u8282\u70b9", None))
        self.parameter_8.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u5f53\u524d\u9879\u76ee\u884c", None))
        self.parameter_8.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u5176\u4ed6\u9879\u76ee\u884c", None))
        self.parameter_8.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u7ee7\u7eed\u6267\u884c", None))

        self.parameterLabel_9.setText(QCoreApplication.translate("InstructionEditor", u"\u5426\u76ee\u6807\u884c\uff08\u8868\u683c\u5e8f\u53f7\uff0c\u4ece 1 \u5f00\u59cb\uff09", None))
        self.parameterLabel_10.setText(QCoreApplication.translate("InstructionEditor", u"\u5426\u9879\u76ee\u8def\u5f84", None))
        self.auxiliary_10.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4f\u89c8\u9879\u76ee", None))
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

