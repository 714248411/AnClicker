# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'variablepool.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHeaderView, QSizePolicy,
    QTableView, QVBoxLayout, QWidget)
import images_rc

class Ui_VariablePool(object):
    def setupUi(self, VariablePool):
        if not VariablePool.objectName():
            VariablePool.setObjectName(u"VariablePool")
        VariablePool.resize(323, 255)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        VariablePool.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(VariablePool)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableView = QTableView(VariablePool)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setAlternatingRowColors(False)

        self.verticalLayout.addWidget(self.tableView)


        self.retranslateUi(VariablePool)

        QMetaObject.connectSlotsByName(VariablePool)
    # setupUi

    def retranslateUi(self, VariablePool):
        VariablePool.setWindowTitle(QCoreApplication.translate("VariablePool", u"\u53d8\u91cf\u6c60", None))
    # retranslateUi

