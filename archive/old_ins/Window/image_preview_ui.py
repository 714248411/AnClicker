# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'image_preview.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)
import images_rc

class Ui_Image(object):
    def setupUi(self, Image):
        if not Image.objectName():
            Image.setObjectName(u"Image")
        Image.resize(328, 299)
        font = QFont()
        font.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        Image.setFont(font)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Image.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Image)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Image)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_2 = QLabel(Image)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.comboBox = QComboBox(Image)
        self.comboBox.setObjectName(u"comboBox")
        palette = QPalette()
        brush = QBrush(QColor(0, 0, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        brush1 = QBrush(QColor(0, 0, 255, 128))
        brush1.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush1)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush1)
#endif
        brush2 = QBrush(QColor(120, 120, 120, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush2)
        brush3 = QBrush(QColor(0, 0, 0, 128))
        brush3.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush3)
#endif
        self.comboBox.setPalette(palette)

        self.gridLayout.addWidget(self.comboBox, 0, 1, 1, 1)

        self.label_3 = QLabel(Image)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.lineEdit = QLineEdit(Image)
        self.lineEdit.setObjectName(u"lineEdit")
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Text, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Active, QPalette.PlaceholderText, brush1)
#endif
        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Text, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush1)
#endif
        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.Text, brush2)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush3)
#endif
        self.lineEdit.setPalette(palette1)

        self.gridLayout.addWidget(self.lineEdit, 1, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton = QPushButton(Image)
        self.pushButton.setObjectName(u"pushButton")
        font1 = QFont()
        font1.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font1.setBold(True)
        self.pushButton.setFont(font1)

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(Image)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setFont(font1)

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(0, 6)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Image)
        self.pushButton_2.clicked.connect(Image.close)

        QMetaObject.connectSlotsByName(Image)
    # setupUi

    def retranslateUi(self, Image):
        Image.setWindowTitle(QCoreApplication.translate("Image", u"\u622a\u56fe\u9884\u89c8", None))
        self.label.setText(QCoreApplication.translate("Image", u"\u56fe\u50cf\u9884\u89c8", None))
        self.label_2.setText(QCoreApplication.translate("Image", u"\u6587\u4ef6\u5939\u8def\u5f84\uff1a", None))
        self.label_3.setText(QCoreApplication.translate("Image", u"\u56fe\u50cf\u540d\u79f0\uff1a", None))
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("Image", u"\u8bf7\u8f93\u5165\u56fe\u50cf\u540d\u79f0\uff0c\u652f\u6301\u4e2d\u6587...", None))
        self.pushButton.setText(QCoreApplication.translate("Image", u"\u4fdd\u5b58", None))
        self.pushButton_2.setText(QCoreApplication.translate("Image", u"\u53d6\u6d88", None))
    # retranslateUi

