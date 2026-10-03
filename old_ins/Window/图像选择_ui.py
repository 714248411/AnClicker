# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '图像选择.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QGridLayout,
    QLabel, QListView, QPushButton, QSizePolicy,
    QWidget)
import images_rc

class Ui_ImageSelect(object):
    def setupUi(self, ImageSelect):
        if not ImageSelect.objectName():
            ImageSelect.setObjectName(u"ImageSelect")
        ImageSelect.resize(310, 252)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        ImageSelect.setWindowIcon(icon)
        self.gridLayout = QGridLayout(ImageSelect)
        self.gridLayout.setObjectName(u"gridLayout")
        self.listView = QListView(ImageSelect)
        self.listView.setObjectName(u"listView")
        self.listView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.gridLayout.addWidget(self.listView, 0, 0, 1, 1)

        self.label = QLabel(ImageSelect)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(200, 200))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)

        self.pushButton = QPushButton(ImageSelect)
        self.pushButton.setObjectName(u"pushButton")

        self.gridLayout.addWidget(self.pushButton, 1, 0, 1, 1)

        self.pushButton_2 = QPushButton(ImageSelect)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.gridLayout.addWidget(self.pushButton_2, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(ImageSelect)

        QMetaObject.connectSlotsByName(ImageSelect)
    # setupUi

    def retranslateUi(self, ImageSelect):
        ImageSelect.setWindowTitle(QCoreApplication.translate("ImageSelect", u"\u56fe\u50cf\u9009\u62e9", None))
        self.label.setText(QCoreApplication.translate("ImageSelect", u"\u56fe\u50cf\u9884\u89c8\u533a", None))
        self.pushButton.setText(QCoreApplication.translate("ImageSelect", u"\u6dfb\u52a0", None))
        self.pushButton_2.setText(QCoreApplication.translate("ImageSelect", u"\u53d6\u6d88", None))
    # retranslateUi

