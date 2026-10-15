# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '后台图色操作.ui'
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
        self.rootLayout = QVBoxLayout(InstructionEditor)
        self.rootLayout.setObjectName(u"rootLayout")
        self.titleLabel = QLabel(InstructionEditor)
        self.titleLabel.setObjectName(u"titleLabel")

        self.rootLayout.addWidget(self.titleLabel)

        self.parameterGroupBox = QGroupBox(InstructionEditor)
        self.parameterGroupBox.setObjectName(u"parameterGroupBox")
        self.parameterFormLayout = QFormLayout(self.parameterGroupBox)
        self.parameterFormLayout.setObjectName(u"parameterFormLayout")
        self.label_0 = QLabel(self.parameterGroupBox)
        self.label_0.setObjectName(u"label_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.LabelRole, self.label_0)

        self.parameter_0 = QComboBox(self.parameterGroupBox)
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.addItem("")
        self.parameter_0.setObjectName(u"parameter_0")

        self.parameterFormLayout.setWidget(0, QFormLayout.FieldRole, self.parameter_0)

        self.label_1 = QLabel(self.parameterGroupBox)
        self.label_1.setObjectName(u"label_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.LabelRole, self.label_1)

        self.parameter_1 = QPlainTextEdit(self.parameterGroupBox)
        self.parameter_1.setObjectName(u"parameter_1")

        self.parameterFormLayout.setWidget(1, QFormLayout.FieldRole, self.parameter_1)

        self.label_2 = QLabel(self.parameterGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.parameterFormLayout.setWidget(2, QFormLayout.LabelRole, self.label_2)

        self.fieldLayout_2 = QHBoxLayout()
        self.fieldLayout_2.setObjectName(u"fieldLayout_2")
        self.parameter_2 = QComboBox(self.parameterGroupBox)
        self.parameter_2.setObjectName(u"parameter_2")
        self.parameter_2.setEditable(True)

        self.fieldLayout_2.addWidget(self.parameter_2)

        self.auxiliary_2 = QPushButton(self.parameterGroupBox)
        self.auxiliary_2.setObjectName(u"auxiliary_2")

        self.fieldLayout_2.addWidget(self.auxiliary_2)


        self.parameterFormLayout.setLayout(2, QFormLayout.FieldRole, self.fieldLayout_2)


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
        self.titleLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u56fe\u8272\u64cd\u4f5c", None))
        self.parameterGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u540e\u53f0\u53c2\u6570", None))
        self.label_0.setText(QCoreApplication.translate("InstructionEditor", u"\u64cd\u4f5c", None))
        self.parameter_0.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6 RGB \u989c\u8272 \u00b7 GetColor", None))
        self.parameter_0.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u8bfb\u53d6 HSV \u989c\u8272 \u00b7 GetColorHSV", None))
        self.parameter_0.setItemText(2, QCoreApplication.translate("InstructionEditor", u"GetColorBGR", None))
        self.parameter_0.setItemText(3, QCoreApplication.translate("InstructionEditor", u"\u6bd4\u8f83\u989c\u8272 \u00b7 CmpColor", None))
        self.parameter_0.setItemText(4, QCoreApplication.translate("InstructionEditor", u"\u533a\u57df RGB \u5747\u503c \u00b7 GetAveRGB", None))
        self.parameter_0.setItemText(5, QCoreApplication.translate("InstructionEditor", u"\u533a\u57df HSV \u5747\u503c \u00b7 GetAveHSV", None))
        self.parameter_0.setItemText(6, QCoreApplication.translate("InstructionEditor", u"RGB2BGR", None))
        self.parameter_0.setItemText(7, QCoreApplication.translate("InstructionEditor", u"BGR2RGB", None))
        self.parameter_0.setItemText(8, QCoreApplication.translate("InstructionEditor", u"\u67e5\u627e\u989c\u8272 \u00b7 FindColor", None))
        self.parameter_0.setItemText(9, QCoreApplication.translate("InstructionEditor", u"\u67e5\u627e\u5168\u90e8\u989c\u8272\u4f4d\u7f6e \u00b7 FindColorEx", None))
        self.parameter_0.setItemText(10, QCoreApplication.translate("InstructionEditor", u"FindColorE", None))
        self.parameter_0.setItemText(11, QCoreApplication.translate("InstructionEditor", u"\u591a\u70b9\u627e\u8272 \u00b7 FindMultiColor", None))
        self.parameter_0.setItemText(12, QCoreApplication.translate("InstructionEditor", u"\u591a\u70b9\u627e\u8272\u5168\u90e8\u4f4d\u7f6e \u00b7 FindMultiColorEx", None))
        self.parameter_0.setItemText(13, QCoreApplication.translate("InstructionEditor", u"FindMultiColorE", None))
        self.parameter_0.setItemText(14, QCoreApplication.translate("InstructionEditor", u"\u67e5\u627e\u56fe\u7247 \u00b7 FindPic", None))
        self.parameter_0.setItemText(15, QCoreApplication.translate("InstructionEditor", u"\u67e5\u627e\u5168\u90e8\u56fe\u7247\u4f4d\u7f6e \u00b7 FindPicEx", None))
        self.parameter_0.setItemText(16, QCoreApplication.translate("InstructionEditor", u"FindPicE", None))
        self.parameter_0.setItemText(17, QCoreApplication.translate("InstructionEditor", u"\u622a\u56fe\u4fdd\u5b58 BMP \u00b7 Capture", None))
        self.parameter_0.setItemText(18, QCoreApplication.translate("InstructionEditor", u"\u622a\u56fe\u4fdd\u5b58 PNG \u00b7 CapturePng", None))
        self.parameter_0.setItemText(19, QCoreApplication.translate("InstructionEditor", u"\u622a\u56fe\u4fdd\u5b58 JPG \u00b7 CaptureJpg", None))
        self.parameter_0.setItemText(20, QCoreApplication.translate("InstructionEditor", u"\u5f55\u5236\u533a\u57df\u52a8\u56fe \u00b7 CaptureGif", None))
        self.parameter_0.setItemText(21, QCoreApplication.translate("InstructionEditor", u"LoadPic", None))
        self.parameter_0.setItemText(22, QCoreApplication.translate("InstructionEditor", u"FreePic", None))
        self.parameter_0.setItemText(23, QCoreApplication.translate("InstructionEditor", u"SetPicPwd", None))
        self.parameter_0.setItemText(24, QCoreApplication.translate("InstructionEditor", u"GetPicSize", None))
        self.parameter_0.setItemText(25, QCoreApplication.translate("InstructionEditor", u"MatchPicName", None))
        self.parameter_0.setItemText(26, QCoreApplication.translate("InstructionEditor", u"GetColorNum", None))
        self.parameter_0.setItemText(27, QCoreApplication.translate("InstructionEditor", u"FindShape", None))
        self.parameter_0.setItemText(28, QCoreApplication.translate("InstructionEditor", u"FindShapeE", None))
        self.parameter_0.setItemText(29, QCoreApplication.translate("InstructionEditor", u"FindShapeEx", None))
        self.parameter_0.setItemText(30, QCoreApplication.translate("InstructionEditor", u"ImageToBmp", None))
        self.parameter_0.setItemText(31, QCoreApplication.translate("InstructionEditor", u"FindColorBlock", None))
        self.parameter_0.setItemText(32, QCoreApplication.translate("InstructionEditor", u"FindColorBlockEx", None))
        self.parameter_0.setItemText(33, QCoreApplication.translate("InstructionEditor", u"FindPicSim", None))
        self.parameter_0.setItemText(34, QCoreApplication.translate("InstructionEditor", u"FindPicSimEx", None))
        self.parameter_0.setItemText(35, QCoreApplication.translate("InstructionEditor", u"\u83b7\u53d6\u56fe\u50cf\u6570\u7ec4 \u00b7 CaptureArray", None))

        self.label_1.setText(QCoreApplication.translate("InstructionEditor", u"\u63a5\u53e3\u53c2\u6570", None))
        self.parameter_1.setPlainText(QCoreApplication.translate("InstructionEditor", u"{}", None))
        self.label_2.setText(QCoreApplication.translate("InstructionEditor", u"\u7ed3\u679c\u53d8\u91cf\uff08\u53ef\u9009\uff09", None))
        self.auxiliary_2.setText(QCoreApplication.translate("InstructionEditor", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.commonGroupBox.setTitle(QCoreApplication.translate("InstructionEditor", u"\u901a\u7528\u53c2\u6570", None))
        self.repeatLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u91cd\u590d\u6b21\u6570", None))
        self.errorPolicyLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5f02\u5e38\u5904\u7406", None))
        self.errorPolicyComboBox.setItemText(0, QCoreApplication.translate("InstructionEditor", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.errorPolicyComboBox.setItemText(1, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.errorPolicyComboBox.setItemText(2, QCoreApplication.translate("InstructionEditor", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.noteLabel.setText(QCoreApplication.translate("InstructionEditor", u"\u5907\u6ce8", None))
        self.testButton.setText(QCoreApplication.translate("InstructionEditor", u"\u6d4b\u8bd5\u6307\u4ee4", None))
        pass
    # retranslateUi

