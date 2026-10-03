# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'global_s.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QLabel,
    QListView, QPushButton, QSizePolicy, QWidget)
import images_rc

class Ui_Global(object):
    def setupUi(self, Global):
        if not Global.objectName():
            Global.setObjectName(u"Global")
        Global.resize(335, 253)
        font = QFont()
        font.setFamilies([u"\u9ed1\u4f53"])
        Global.setFont(font)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Global.setWindowIcon(icon)
        self.gridLayout = QGridLayout(Global)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(Global)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)

        self.listView = QListView(Global)
        self.listView.setObjectName(u"listView")
        self.listView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.gridLayout.addWidget(self.listView, 1, 0, 1, 4)

        self.pushButton_4 = QPushButton(Global)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setStyleSheet(u"")

        self.gridLayout.addWidget(self.pushButton_4, 2, 0, 1, 1)

        self.pushButton_5 = QPushButton(Global)
        self.pushButton_5.setObjectName(u"pushButton_5")

        self.gridLayout.addWidget(self.pushButton_5, 2, 1, 1, 1)

        self.pushButton = QPushButton(Global)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"    background-color: red;\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"	font-weight: bold; /* \u8bbe\u7f6e\u5b57\u4f53\u52a0\u7c97 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(170, 0, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(85, 85, 127); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}")

        self.gridLayout.addWidget(self.pushButton, 2, 2, 1, 1)

        self.pushButton_2 = QPushButton(Global)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout.addWidget(self.pushButton_2, 2, 3, 1, 1)


        self.retranslateUi(Global)

        QMetaObject.connectSlotsByName(Global)
    # setupUi

    def retranslateUi(self, Global):
        Global.setWindowTitle(QCoreApplication.translate("Global", u"\u5168\u5c40\u53c2\u6570", None))
        self.label.setText(QCoreApplication.translate("Global", u"\u8d44\u6e90\u6587\u4ef6\u5939\u8def\u5f84\uff1a\uff08\u53cc\u51fb\u6253\u5f00\u8def\u5f84\uff09", None))
        self.pushButton_4.setText(QCoreApplication.translate("Global", u"\u4e0a\u79fb", None))
        self.pushButton_5.setText(QCoreApplication.translate("Global", u"\u4e0b\u79fb", None))
        self.pushButton.setText(QCoreApplication.translate("Global", u"\u6dfb\u52a0\u6587\u4ef6\u5939", None))
        self.pushButton_2.setText(QCoreApplication.translate("Global", u"\u5220\u9664", None))
    # retranslateUi

