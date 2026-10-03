# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'clickposition.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_ClickPosition(object):
    def setupUi(self, ClickPosition):
        if not ClickPosition.objectName():
            ClickPosition.setObjectName(u"ClickPosition")
        ClickPosition.resize(336, 306)
        self.horizontalLayout = QHBoxLayout(ClickPosition)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(ClickPosition)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_4, 0, 1, 1, 1)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_5, 1, 1, 1, 1)

        self.checkBox = QCheckBox(self.groupBox)
        self.checkBox.setObjectName(u"checkBox")

        self.gridLayout.addWidget(self.checkBox, 2, 0, 1, 2)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(ClickPosition)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_2 = QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_6, 0, 0, 1, 1)

        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_8, 0, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_7, 1, 0, 1, 1)

        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_9, 1, 1, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.verticalSpacer = QSpacerItem(20, 96, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.pushButton = QPushButton(ClickPosition)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalLayout.setStretch(0, 1)

        self.retranslateUi(ClickPosition)

        QMetaObject.connectSlotsByName(ClickPosition)
    # setupUi

    def retranslateUi(self, ClickPosition):
        ClickPosition.setWindowTitle(QCoreApplication.translate("ClickPosition", u"\u56fe\u50cf\u70b9\u51fb\u4f4d\u7f6e", None))
        self.groupBox.setTitle(QCoreApplication.translate("ClickPosition", u"\u70b9\u51fb\u4f4d\u7f6e", None))
        self.label_3.setText(QCoreApplication.translate("ClickPosition", u"Y:", None))
        self.label_2.setText(QCoreApplication.translate("ClickPosition", u"X:", None))
        self.label_4.setText(QCoreApplication.translate("ClickPosition", u"0", None))
        self.label_5.setText(QCoreApplication.translate("ClickPosition", u"0", None))
        self.checkBox.setText(QCoreApplication.translate("ClickPosition", u"\u968f\u673a\u4f4d\u7f6e", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("ClickPosition", u"\u56fe\u50cf\u4fe1\u606f", None))
        self.label_6.setText(QCoreApplication.translate("ClickPosition", u"\u5bbd\u5ea6\uff1a", None))
        self.label_8.setText(QCoreApplication.translate("ClickPosition", u"0", None))
        self.label_7.setText(QCoreApplication.translate("ClickPosition", u"\u9ad8\u5ea6\uff1a", None))
        self.label_9.setText(QCoreApplication.translate("ClickPosition", u"0", None))
        self.pushButton.setText(QCoreApplication.translate("ClickPosition", u"\u786e\u5b9a", None))
    # retranslateUi

