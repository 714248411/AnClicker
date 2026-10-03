# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '参数窗口.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QApplication, QDialog, QPushButton, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)
import images_rc

class Ui_Param(object):
    def setupUi(self, Param):
        if not Param.objectName():
            Param.setObjectName(u"Param")
        Param.resize(246, 187)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Param.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Param)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.textEdit = QTextEdit(Param)
        self.textEdit.setObjectName(u"textEdit")
        font = QFont()
        font.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font.setPointSize(11)
        self.textEdit.setFont(font)
        self.textEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.textEdit)

        self.pushButton = QPushButton(Param)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)


        self.retranslateUi(Param)

        QMetaObject.connectSlotsByName(Param)
    # setupUi

    def retranslateUi(self, Param):
        Param.setWindowTitle(QCoreApplication.translate("Param", u"\u6307\u4ee4\u53c2\u6570", None))
        self.pushButton.setText(QCoreApplication.translate("Param", u"\u4fee\u6539\u6307\u4ee4", None))
    # retranslateUi

