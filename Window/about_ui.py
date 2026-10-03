# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QToolButton, QVBoxLayout, QWidget)
import images_rc

class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(218, 396)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        About.setWindowIcon(icon)
        self.verticalLayout_2 = QVBoxLayout(About)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(About)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(90, 90))
        self.label.setPixmap(QPixmap(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png"))
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.label_5 = QLabel(About)
        self.label_5.setObjectName(u"label_5")
        palette = QPalette()
        brush = QBrush(QColor(255, 0, 0, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        brush1 = QBrush(QColor(255, 0, 0, 128))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush1)
#endif
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush1)
#endif
        brush2 = QBrush(QColor(120, 120, 120, 255))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush2)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush2)
        brush3 = QBrush(QColor(0, 0, 0, 128))
        brush3.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush3)
#endif
        self.label_5.setPalette(palette)
        font = QFont()
        font.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font.setPointSize(13)
        font.setBold(True)
        self.label_5.setFont(font)
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_5)


        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_7, 0, 0, 1, 1)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_8, 0, 2, 1, 1)

        self.label_2 = QLabel(About)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pushButton_2 = QPushButton(About)
        self.pushButton_2.setObjectName(u"pushButton_2")
        font2 = QFont()
        font2.setFamilies([u"Microsoft YaHei"])
        font2.setBold(True)
        self.pushButton_2.setFont(font2)
        self.pushButton_2.setStyleSheet(u"QPushButton {\n"
"    background-color: red;\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    font-size: 16px; /* \u8bbe\u7f6e\u5b57\u4f53\u5927\u5c0f\uff0c\u53ef\u4ee5\u6839\u636e\u9700\u8981\u8c03\u6574 */\n"
"    padding: 5px 10px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(170, 0, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(85, 85, 127); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.horizontalLayout_4.setStretch(0, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.label_3 = QLabel(About)
        self.label_3.setObjectName(u"label_3")
        font3 = QFont()
        font3.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        self.label_3.setFont(font3)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_3.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_3)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(7)
        self.gridLayout_2.setVerticalSpacing(4)
        self.pushButton_3 = QPushButton(About)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setFont(font2)
        self.pushButton_3.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(219, 58, 150); /* \u8bbe\u7f6e\u80cc\u666f\u989c\u8272\u4e3a\u7c89\u7ea2\u8272 */\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    font-size: 18px; /* \u8bbe\u7f6e\u5b57\u4f53\u5927\u5c0f\uff0c\u53ef\u4ee5\u6839\u636e\u9700\u8981\u8c03\u6574 */\n"
"    padding: 5px 10px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(180, 40, 120); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272\u4e3a\u52a0\u6df1\u7684\u7c89\u7ea2\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(85, 85, 127); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")
        icon1 = QIcon()
        icon1.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u6350\u8d60.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_3.setIcon(icon1)

        self.gridLayout_2.addWidget(self.pushButton_3, 0, 0, 1, 3)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_5, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_6 = QLabel(About)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout.addWidget(self.label_6)

        self.label_7 = QLabel(About)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setStyleSheet(u"color: red; text-decoration: underline")
        self.label_7.setOpenExternalLinks(True)

        self.horizontalLayout.addWidget(self.label_7)


        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 1, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_6, 1, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.gitee = QToolButton(About)
        self.gitee.setObjectName(u"gitee")
        icon2 = QIcon()
        icon2.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/gitee.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.gitee.setIcon(icon2)
        self.gitee.setIconSize(QSize(50, 50))
        self.gitee.setAutoRaise(True)

        self.horizontalLayout_3.addWidget(self.gitee)

        self.gitee_2 = QToolButton(About)
        self.gitee_2.setObjectName(u"gitee_2")
        icon3 = QIcon()
        icon3.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/github.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.gitee_2.setIcon(icon3)
        self.gitee_2.setIconSize(QSize(50, 50))
        self.gitee_2.setAutoRaise(True)

        self.horizontalLayout_3.addWidget(self.gitee_2)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.label_4 = QLabel(About)
        self.label_4.setObjectName(u"label_4")
        font4 = QFont()
        font4.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font4.setPointSize(7)
        self.label_4.setFont(font4)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_4.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_4)


        self.retranslateUi(About)

        QMetaObject.connectSlotsByName(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", u"\u5173\u4e8e", None))
        self.label.setText("")
        self.label_5.setText(QCoreApplication.translate("About", u"Clicker", None))
        self.label_2.setText(QCoreApplication.translate("About", u"\u7248\u672c\uff1av0.25 Bate", None))
        self.pushButton_2.setText(QCoreApplication.translate("About", u"\u53cd\u9988\u53ca\u5efa\u8bae", None))
        self.label_3.setText(QCoreApplication.translate("About", u"PyAutoGUI\u53ef\u89c6\u5316\uff0c\u81ea\u52a8\u5904\u7406\u9700\u8981\u5927\u91cf\u91cd\u590d\u64cd\u4f5c\u9f20\u6807\u952e\u76d8\u7684\u4e8b\u4ef6\u3002", None))
        self.pushButton_3.setText(QCoreApplication.translate("About", u"\u6350\u8d60\u652f\u6301\u5f00\u53d1\u8005", None))
        self.label_6.setText(QCoreApplication.translate("About", u"QQ\u4ea4\u6d41\u7fa4\uff1a", None))
        self.label_7.setText(QCoreApplication.translate("About", u"308994839", None))
        self.gitee.setText(QCoreApplication.translate("About", u"gitee\u5730\u5740", None))
        self.gitee_2.setText(QCoreApplication.translate("About", u"gitee\u5730\u5740", None))
        self.label_4.setText(QCoreApplication.translate("About", u"federalsadler@sohu.com Copyright (c) [2022] ", None))
    # retranslateUi

