# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '导航窗口.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QKeySequenceEdit, QLabel,
    QLineEdit, QListView, QPushButton, QRadioButton,
    QSizePolicy, QSlider, QSpacerItem, QSpinBox,
    QTabWidget, QTextBrowser, QTextEdit, QTimeEdit,
    QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget)
import images_rc

class Ui_navigation(object):
    def setupUi(self, navigation):
        if not navigation.objectName():
            navigation.setObjectName(u"navigation")
        navigation.resize(638, 667)
        font = QFont()
        font.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font.setBold(False)
        navigation.setFont(font)
        icon = QIcon()
        icon.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u56fe\u6807.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        navigation.setWindowIcon(icon)
        navigation.setStyleSheet(u"")
        self.horizontalLayout_16 = QHBoxLayout(navigation)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.verticalLayout_43 = QVBoxLayout()
        self.verticalLayout_43.setObjectName(u"verticalLayout_43")
        self.lineEdit_22 = QLineEdit(navigation)
        self.lineEdit_22.setObjectName(u"lineEdit_22")
        self.lineEdit_22.setMaximumSize(QSize(220, 16777215))

        self.verticalLayout_43.addWidget(self.lineEdit_22)

        self.treeWidget = QTreeWidget(navigation)
        __qtreewidgetitem = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem)
        __qtreewidgetitem1 = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem1)
        QTreeWidgetItem(__qtreewidgetitem1)
        QTreeWidgetItem(__qtreewidgetitem1)
        QTreeWidgetItem(__qtreewidgetitem1)
        QTreeWidgetItem(__qtreewidgetitem1)
        __qtreewidgetitem2 = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        QTreeWidgetItem(__qtreewidgetitem2)
        __qtreewidgetitem3 = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem3)
        __qtreewidgetitem4 = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        QTreeWidgetItem(__qtreewidgetitem4)
        __qtreewidgetitem5 = QTreeWidgetItem(self.treeWidget)
        QTreeWidgetItem(__qtreewidgetitem5)
        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setEnabled(True)
        self.treeWidget.setMaximumSize(QSize(220, 16777215))
        font1 = QFont()
        font1.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font1.setBold(True)
        font1.setItalic(False)
        font1.setUnderline(False)
        self.treeWidget.setFont(font1)
        self.treeWidget.setStyleSheet(u"")

        self.verticalLayout_43.addWidget(self.treeWidget)


        self.horizontalLayout_16.addLayout(self.verticalLayout_43)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.tabWidget = QTabWidget(navigation)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setMinimumSize(QSize(500, 0))
        self.tabWidget.setFont(font)
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tabWidget.setUsesScrollButtons(True)
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(False)
        self.tabWidget.setTabBarAutoHide(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_12 = QVBoxLayout(self.tab)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.label = QLabel(self.tab)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(False)

        self.verticalLayout_12.addWidget(self.label)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.label_3 = QLabel(self.tab)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_3.setWordWrap(False)

        self.verticalLayout.addWidget(self.label_3)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.verticalLayout_12.addLayout(self.verticalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pushButton = QPushButton(self.tab)
        self.pushButton.setObjectName(u"pushButton")
        font2 = QFont()
        font2.setFamilies([u"Microsoft YaHei"])
        font2.setBold(True)
        self.pushButton.setFont(font2)
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #0066CC; /* \u84dd\u8272 */\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0056B3; /* \u9f20\u6807\u60ac\u505c\u65f6\u7684\u8f83\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004C99; /* \u6309\u94ae\u6309\u4e0b\u65f6\u7684\u66f4\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"")

        self.horizontalLayout_4.addWidget(self.pushButton)

        self.pushButton_7 = QPushButton(self.tab)
        self.pushButton_7.setObjectName(u"pushButton_7")
        font3 = QFont()
        font3.setFamilies([u"SimSun"])
        font3.setBold(False)
        self.pushButton_7.setFont(font3)

        self.horizontalLayout_4.addWidget(self.pushButton_7)


        self.verticalLayout_12.addLayout(self.horizontalLayout_4)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(self.tab)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)

        self.checkBox = QCheckBox(self.tab)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setEnabled(True)
        self.checkBox.setChecked(False)

        self.gridLayout.addWidget(self.checkBox, 1, 4, 1, 1)

        self.label_36 = QLabel(self.tab)
        self.label_36.setObjectName(u"label_36")
        self.label_36.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_36, 0, 0, 1, 1)

        self.label_5 = QLabel(self.tab)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)

        self.comboBox_8 = QComboBox(self.tab)
        self.comboBox_8.setObjectName(u"comboBox_8")
        self.comboBox_8.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.comboBox_8.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.comboBox_8.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.comboBox_8, 0, 1, 1, 4)

        self.comboBox = QComboBox(self.tab)
        self.comboBox.setObjectName(u"comboBox")

        self.gridLayout.addWidget(self.comboBox, 1, 1, 1, 3)

        self.pushButton_11 = QPushButton(self.tab)
        self.pushButton_11.setObjectName(u"pushButton_11")
        self.pushButton_11.setStyleSheet(u"")

        self.gridLayout.addWidget(self.pushButton_11, 2, 4, 1, 1)

        self.comboBox_2 = QComboBox(self.tab)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")

        self.gridLayout.addWidget(self.comboBox_2, 2, 1, 1, 3)


        self.verticalLayout_12.addLayout(self.gridLayout)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.groupBox_77 = QGroupBox(self.tab)
        self.groupBox_77.setObjectName(u"groupBox_77")
        self.gridLayout_73 = QGridLayout(self.groupBox_77)
        self.gridLayout_73.setObjectName(u"gridLayout_73")
        self.label_176 = QLabel(self.groupBox_77)
        self.label_176.setObjectName(u"label_176")
        self.label_176.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_73.addWidget(self.label_176, 0, 0, 1, 1)

        self.pushButton_76 = QPushButton(self.groupBox_77)
        self.pushButton_76.setObjectName(u"pushButton_76")

        self.gridLayout_73.addWidget(self.pushButton_76, 0, 1, 1, 1)

        self.label_177 = QLabel(self.groupBox_77)
        self.label_177.setObjectName(u"label_177")

        self.gridLayout_73.addWidget(self.label_177, 1, 0, 1, 1)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.horizontalSlider_4 = QSlider(self.groupBox_77)
        self.horizontalSlider_4.setObjectName(u"horizontalSlider_4")
        self.horizontalSlider_4.setMaximum(100)
        self.horizontalSlider_4.setValue(80)
        self.horizontalSlider_4.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_32.addWidget(self.horizontalSlider_4)

        self.label_178 = QLabel(self.groupBox_77)
        self.label_178.setObjectName(u"label_178")

        self.horizontalLayout_32.addWidget(self.label_178)


        self.gridLayout_73.addLayout(self.horizontalLayout_32, 1, 1, 1, 1)


        self.horizontalLayout_34.addWidget(self.groupBox_77)

        self.groupBox_57 = QGroupBox(self.tab)
        self.groupBox_57.setObjectName(u"groupBox_57")
        self.groupBox_57.setEnabled(True)
        self.groupBox_57.setCheckable(True)
        self.groupBox_57.setChecked(False)
        self.verticalLayout_79 = QVBoxLayout(self.groupBox_57)
        self.verticalLayout_79.setObjectName(u"verticalLayout_79")
        self.label_155 = QLabel(self.groupBox_57)
        self.label_155.setObjectName(u"label_155")
        self.label_155.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_79.addWidget(self.label_155)

        self.pushButton_50 = QPushButton(self.groupBox_57)
        self.pushButton_50.setObjectName(u"pushButton_50")

        self.verticalLayout_79.addWidget(self.pushButton_50)


        self.horizontalLayout_34.addWidget(self.groupBox_57)

        self.horizontalLayout_34.setStretch(0, 1)
        self.horizontalLayout_34.setStretch(1, 1)

        self.verticalLayout_12.addLayout(self.horizontalLayout_34)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_12.addItem(self.verticalSpacer_2)

        self.groupBox_3 = QGroupBox(self.tab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_13 = QGridLayout(self.groupBox_3)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.radioButton_2 = QRadioButton(self.groupBox_3)
        self.radioButton_2.setObjectName(u"radioButton_2")
        self.radioButton_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.gridLayout_13.addWidget(self.radioButton_2, 0, 0, 1, 2)

        self.radioButton_4 = QRadioButton(self.groupBox_3)
        self.radioButton_4.setObjectName(u"radioButton_4")
        self.radioButton_4.setChecked(True)

        self.gridLayout_13.addWidget(self.radioButton_4, 1, 0, 1, 1)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_42 = QLabel(self.groupBox_3)
        self.label_42.setObjectName(u"label_42")
        self.label_42.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_15.addWidget(self.label_42)

        self.spinBox_4 = QSpinBox(self.groupBox_3)
        self.spinBox_4.setObjectName(u"spinBox_4")
        self.spinBox_4.setMaximum(9999)
        self.spinBox_4.setValue(5)

        self.horizontalLayout_15.addWidget(self.spinBox_4)


        self.gridLayout_13.addLayout(self.horizontalLayout_15, 1, 1, 1, 1)


        self.verticalLayout_12.addWidget(self.groupBox_3)

        self.pushButton_6 = QPushButton(self.tab)
        self.pushButton_6.setObjectName(u"pushButton_6")
        palette = QPalette()
        brush = QBrush(QColor(255, 255, 255, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(0, 170, 0, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush2 = QBrush(QColor(255, 255, 255, 128))
        brush2.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush2)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush3 = QBrush(QColor(255, 255, 255, 128))
        brush3.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush3)
#endif
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush)
        brush4 = QBrush(QColor(0, 0, 0, 92))
        brush4.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush5 = QBrush(QColor(255, 255, 255, 128))
        brush5.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush5)
#endif
        self.pushButton_6.setPalette(palette)
        self.pushButton_6.setFont(font2)
        self.pushButton_6.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_12.addWidget(self.pushButton_6)

        self.tabWidget.addTab(self.tab, "")
        self.tab_43 = QWidget()
        self.tab_43.setObjectName(u"tab_43")
        self.verticalLayout_57 = QVBoxLayout(self.tab_43)
        self.verticalLayout_57.setObjectName(u"verticalLayout_57")
        self.label_172 = QLabel(self.tab_43)
        self.label_172.setObjectName(u"label_172")
        self.label_172.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_172.setWordWrap(False)

        self.verticalLayout_57.addWidget(self.label_172)

        self.groupBox_71 = QGroupBox(self.tab_43)
        self.groupBox_71.setObjectName(u"groupBox_71")
        self.verticalLayout_56 = QVBoxLayout(self.groupBox_71)
        self.verticalLayout_56.setSpacing(0)
        self.verticalLayout_56.setObjectName(u"verticalLayout_56")
        self.verticalLayout_56.setContentsMargins(-1, -1, -1, 0)
        self.listView = QListView(self.groupBox_71)
        self.listView.setObjectName(u"listView")
        self.listView.setStyleSheet(u"QListView {\n"
"                border: none; /* \u65e0\u8fb9\u6846 */\n"
"            }")
        self.listView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.verticalLayout_56.addWidget(self.listView)

        self.gridLayout_71 = QGridLayout()
        self.gridLayout_71.setSpacing(5)
        self.gridLayout_71.setObjectName(u"gridLayout_71")
        self.gridLayout_71.setContentsMargins(-1, 5, -1, -1)
        self.pushButton_67 = QPushButton(self.groupBox_71)
        self.pushButton_67.setObjectName(u"pushButton_67")
        self.pushButton_67.setFont(font2)
        self.pushButton_67.setStyleSheet(u"QPushButton {\n"
"    background-color: red;\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
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

        self.gridLayout_71.addWidget(self.pushButton_67, 0, 0, 1, 1)

        self.toolButton_2 = QToolButton(self.groupBox_71)
        self.toolButton_2.setObjectName(u"toolButton_2")
        icon1 = QIcon()
        icon1.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/qss_icons/add_top.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolButton_2.setIcon(icon1)

        self.gridLayout_71.addWidget(self.toolButton_2, 0, 1, 1, 1)

        self.pushButton_63 = QPushButton(self.groupBox_71)
        self.pushButton_63.setObjectName(u"pushButton_63")
        self.pushButton_63.setFont(font2)
        self.pushButton_63.setStyleSheet(u"QPushButton {\n"
"    background-color: #0066CC; /* \u84dd\u8272 */\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0056B3; /* \u9f20\u6807\u60ac\u505c\u65f6\u7684\u8f83\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004C99; /* \u6309\u94ae\u6309\u4e0b\u65f6\u7684\u66f4\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"")

        self.gridLayout_71.addWidget(self.pushButton_63, 0, 2, 1, 1)

        self.pushButton_64 = QPushButton(self.groupBox_71)
        self.pushButton_64.setObjectName(u"pushButton_64")

        self.gridLayout_71.addWidget(self.pushButton_64, 1, 0, 1, 1)

        self.toolButton = QToolButton(self.groupBox_71)
        self.toolButton.setObjectName(u"toolButton")
        icon2 = QIcon()
        icon2.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/qss_icons/add_bottom.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolButton.setIcon(icon2)

        self.gridLayout_71.addWidget(self.toolButton, 1, 1, 1, 1)

        self.pushButton_68 = QPushButton(self.groupBox_71)
        self.pushButton_68.setObjectName(u"pushButton_68")

        self.gridLayout_71.addWidget(self.pushButton_68, 1, 2, 1, 1)


        self.verticalLayout_56.addLayout(self.gridLayout_71)


        self.verticalLayout_57.addWidget(self.groupBox_71)

        self.groupBox_74 = QGroupBox(self.tab_43)
        self.groupBox_74.setObjectName(u"groupBox_74")
        self.gridLayout_70 = QGridLayout(self.groupBox_74)
        self.gridLayout_70.setObjectName(u"gridLayout_70")
        self.comboBox_70 = QComboBox(self.groupBox_74)
        self.comboBox_70.addItem("")
        self.comboBox_70.addItem("")
        self.comboBox_70.addItem("")
        self.comboBox_70.addItem("")
        self.comboBox_70.addItem("")
        self.comboBox_70.setObjectName(u"comboBox_70")

        self.gridLayout_70.addWidget(self.comboBox_70, 0, 0, 1, 1)

        self.pushButton_66 = QPushButton(self.groupBox_74)
        self.pushButton_66.setObjectName(u"pushButton_66")
        self.pushButton_66.setStyleSheet(u"")

        self.gridLayout_70.addWidget(self.pushButton_66, 0, 1, 1, 1)

        self.comboBox_71 = QComboBox(self.groupBox_74)
        self.comboBox_71.addItem("")
        self.comboBox_71.addItem("")
        self.comboBox_71.setObjectName(u"comboBox_71")

        self.gridLayout_70.addWidget(self.comboBox_71, 1, 0, 1, 1)

        self.checkBox_11 = QCheckBox(self.groupBox_74)
        self.checkBox_11.setObjectName(u"checkBox_11")
        self.checkBox_11.setEnabled(True)
        self.checkBox_11.setChecked(False)

        self.gridLayout_70.addWidget(self.checkBox_11, 1, 1, 1, 1)

        self.gridLayout_70.setColumnStretch(0, 2)
        self.gridLayout_70.setColumnStretch(1, 1)

        self.verticalLayout_57.addWidget(self.groupBox_74)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.groupBox_78 = QGroupBox(self.tab_43)
        self.groupBox_78.setObjectName(u"groupBox_78")
        self.gridLayout_74 = QGridLayout(self.groupBox_78)
        self.gridLayout_74.setObjectName(u"gridLayout_74")
        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.horizontalSlider_5 = QSlider(self.groupBox_78)
        self.horizontalSlider_5.setObjectName(u"horizontalSlider_5")
        self.horizontalSlider_5.setMaximum(100)
        self.horizontalSlider_5.setValue(80)
        self.horizontalSlider_5.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_35.addWidget(self.horizontalSlider_5)

        self.label_181 = QLabel(self.groupBox_78)
        self.label_181.setObjectName(u"label_181")

        self.horizontalLayout_35.addWidget(self.label_181)


        self.gridLayout_74.addLayout(self.horizontalLayout_35, 0, 1, 1, 1)

        self.label_180 = QLabel(self.groupBox_78)
        self.label_180.setObjectName(u"label_180")

        self.gridLayout_74.addWidget(self.label_180, 0, 0, 1, 1)


        self.horizontalLayout_9.addWidget(self.groupBox_78)

        self.groupBox_73 = QGroupBox(self.tab_43)
        self.groupBox_73.setObjectName(u"groupBox_73")
        self.groupBox_73.setEnabled(True)
        self.groupBox_73.setCheckable(True)
        self.groupBox_73.setChecked(False)
        self.verticalLayout_86 = QVBoxLayout(self.groupBox_73)
        self.verticalLayout_86.setObjectName(u"verticalLayout_86")
        self.label_174 = QLabel(self.groupBox_73)
        self.label_174.setObjectName(u"label_174")
        self.label_174.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_86.addWidget(self.label_174)

        self.pushButton_65 = QPushButton(self.groupBox_73)
        self.pushButton_65.setObjectName(u"pushButton_65")

        self.verticalLayout_86.addWidget(self.pushButton_65)


        self.horizontalLayout_9.addWidget(self.groupBox_73)

        self.horizontalLayout_9.setStretch(0, 1)
        self.horizontalLayout_9.setStretch(1, 1)

        self.verticalLayout_57.addLayout(self.horizontalLayout_9)

        self.verticalSpacer_38 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_57.addItem(self.verticalSpacer_38)

        self.pushButton_69 = QPushButton(self.tab_43)
        self.pushButton_69.setObjectName(u"pushButton_69")
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Text, brush)
        palette1.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush6 = QBrush(QColor(255, 255, 255, 128))
        brush6.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Active, QPalette.PlaceholderText, brush6)
#endif
        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush7 = QBrush(QColor(255, 255, 255, 128))
        brush7.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush7)
#endif
        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette1.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush8 = QBrush(QColor(255, 255, 255, 128))
        brush8.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush8)
#endif
        self.pushButton_69.setPalette(palette1)
        self.pushButton_69.setFont(font2)
        self.pushButton_69.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_57.addWidget(self.pushButton_69)

        self.tabWidget.addTab(self.tab_43, "")
        self.tab_27 = QWidget()
        self.tab_27.setObjectName(u"tab_27")
        self.verticalLayout_3 = QVBoxLayout(self.tab_27)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_6 = QLabel(self.tab_27)
        self.label_6.setObjectName(u"label_6")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_6.setWordWrap(False)
        self.label_6.setMargin(0)
        self.label_6.setIndent(-1)
        self.label_6.setOpenExternalLinks(False)

        self.verticalLayout_3.addWidget(self.label_6)

        self.verticalLayout_60 = QVBoxLayout()
        self.verticalLayout_60.setObjectName(u"verticalLayout_60")
        self.gridLayout_33 = QGridLayout()
        self.gridLayout_33.setObjectName(u"gridLayout_33")
        self.pushButton_4 = QPushButton(self.tab_27)
        self.pushButton_4.setObjectName(u"pushButton_4")

        self.gridLayout_33.addWidget(self.pushButton_4, 0, 0, 1, 2)

        self.label_7 = QLabel(self.tab_27)
        self.label_7.setObjectName(u"label_7")
        font4 = QFont()
        font4.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font4.setBold(True)
        self.label_7.setFont(font4)
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_33.addWidget(self.label_7, 1, 0, 1, 1)

        self.label_9 = QLabel(self.tab_27)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font4)
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_33.addWidget(self.label_9, 1, 1, 1, 1)

        self.label_8 = QLabel(self.tab_27)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font4)
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_33.addWidget(self.label_8, 2, 0, 1, 1)

        self.label_10 = QLabel(self.tab_27)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font4)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_33.addWidget(self.label_10, 2, 1, 1, 1)


        self.verticalLayout_60.addLayout(self.gridLayout_33)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_11 = QLabel(self.tab_27)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_11, 0, 0, 1, 1)

        self.comboBox_3 = QComboBox(self.tab_27)
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.setObjectName(u"comboBox_3")

        self.gridLayout_2.addWidget(self.comboBox_3, 0, 1, 1, 1)

        self.label_22 = QLabel(self.tab_27)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setEnabled(True)
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.label_22, 1, 0, 1, 1)

        self.spinBox_2 = QSpinBox(self.tab_27)
        self.spinBox_2.setObjectName(u"spinBox_2")
        self.spinBox_2.setEnabled(True)
        self.spinBox_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.spinBox_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_2.setMaximum(999)

        self.gridLayout_2.addWidget(self.spinBox_2, 1, 1, 1, 1)


        self.verticalLayout_60.addLayout(self.gridLayout_2)


        self.verticalLayout_3.addLayout(self.verticalLayout_60)

        self.verticalSpacer_5 = QSpacerItem(20, 227, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_5)

        self.pushButton_23 = QPushButton(self.tab_27)
        self.pushButton_23.setObjectName(u"pushButton_23")
        palette2 = QPalette()
        palette2.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette2.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette2.setBrush(QPalette.Active, QPalette.Text, brush)
        palette2.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette2.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush9 = QBrush(QColor(255, 255, 255, 128))
        brush9.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Active, QPalette.PlaceholderText, brush9)
#endif
        palette2.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette2.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette2.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush10 = QBrush(QColor(255, 255, 255, 128))
        brush10.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush10)
#endif
        palette2.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette2.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette2.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette2.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette2.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette2.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush11 = QBrush(QColor(255, 255, 255, 128))
        brush11.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush11)
#endif
        self.pushButton_23.setPalette(palette2)
        self.pushButton_23.setFont(font2)
        self.pushButton_23.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_3.addWidget(self.pushButton_23)

        self.tabWidget.addTab(self.tab_27, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayout_15 = QVBoxLayout(self.tab_5)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.groupBox_28 = QGroupBox(self.tab_5)
        self.groupBox_28.setObjectName(u"groupBox_28")
        self.groupBox_28.setStyleSheet(u"")
        self.groupBox_28.setFlat(False)
        self.groupBox_28.setCheckable(True)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_28)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lineEdit = QLineEdit(self.groupBox_28)
        self.lineEdit.setObjectName(u"lineEdit")

        self.gridLayout_3.addWidget(self.lineEdit, 1, 1, 1, 1)

        self.label_13 = QLabel(self.groupBox_28)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_13, 1, 0, 1, 1)

        self.comboBox_4 = QComboBox(self.groupBox_28)
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.setObjectName(u"comboBox_4")

        self.gridLayout_3.addWidget(self.comboBox_4, 0, 1, 1, 1)

        self.label_12 = QLabel(self.groupBox_28)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.label_12, 0, 0, 1, 1)

        self.gridLayout_3.setColumnStretch(0, 1)
        self.gridLayout_3.setColumnStretch(1, 1)

        self.verticalLayout_4.addLayout(self.gridLayout_3)


        self.verticalLayout_15.addWidget(self.groupBox_28)

        self.groupBox_30 = QGroupBox(self.tab_5)
        self.groupBox_30.setObjectName(u"groupBox_30")
        self.groupBox_30.setFlat(False)
        self.groupBox_30.setCheckable(True)
        self.groupBox_30.setChecked(False)
        self.verticalLayout_59 = QVBoxLayout(self.groupBox_30)
        self.verticalLayout_59.setObjectName(u"verticalLayout_59")
        self.gridLayout_35 = QGridLayout()
        self.gridLayout_35.setObjectName(u"gridLayout_35")
        self.comboBox_16 = QComboBox(self.groupBox_30)
        self.comboBox_16.addItem("")
        self.comboBox_16.addItem("")
        self.comboBox_16.setObjectName(u"comboBox_16")

        self.gridLayout_35.addWidget(self.comboBox_16, 0, 1, 1, 1)

        self.label_102 = QLabel(self.groupBox_30)
        self.label_102.setObjectName(u"label_102")
        self.label_102.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_35.addWidget(self.label_102, 0, 0, 1, 1)

        self.gridLayout_35.setColumnStretch(0, 1)
        self.gridLayout_35.setColumnStretch(1, 1)

        self.verticalLayout_59.addLayout(self.gridLayout_35)


        self.verticalLayout_15.addWidget(self.groupBox_30)

        self.groupBox_59 = QGroupBox(self.tab_5)
        self.groupBox_59.setObjectName(u"groupBox_59")
        self.groupBox_59.setCheckable(True)
        self.groupBox_59.setChecked(False)
        self.gridLayout_29 = QGridLayout(self.groupBox_59)
        self.gridLayout_29.setObjectName(u"gridLayout_29")
        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.label_157 = QLabel(self.groupBox_59)
        self.label_157.setObjectName(u"label_157")
        self.label_157.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_23.addWidget(self.label_157)

        self.lineEdit_29 = QLineEdit(self.groupBox_59)
        self.lineEdit_29.setObjectName(u"lineEdit_29")
        self.lineEdit_29.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_23.addWidget(self.lineEdit_29)

        self.label_158 = QLabel(self.groupBox_59)
        self.label_158.setObjectName(u"label_158")
        self.label_158.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_23.addWidget(self.label_158)

        self.lineEdit_30 = QLineEdit(self.groupBox_59)
        self.lineEdit_30.setObjectName(u"lineEdit_30")
        self.lineEdit_30.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_23.addWidget(self.lineEdit_30)

        self.horizontalLayout_23.setStretch(0, 1)
        self.horizontalLayout_23.setStretch(1, 1)
        self.horizontalLayout_23.setStretch(2, 1)
        self.horizontalLayout_23.setStretch(3, 1)

        self.gridLayout_29.addLayout(self.horizontalLayout_23, 0, 0, 1, 2)

        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.label_31 = QLabel(self.groupBox_59)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_26.addWidget(self.label_31)

        self.doubleSpinBox = QDoubleSpinBox(self.groupBox_59)
        self.doubleSpinBox.setObjectName(u"doubleSpinBox")
        self.doubleSpinBox.setMaximum(99.000000000000000)
        self.doubleSpinBox.setSingleStep(0.100000000000000)
        self.doubleSpinBox.setValue(0.000000000000000)

        self.horizontalLayout_26.addWidget(self.doubleSpinBox)


        self.gridLayout_29.addLayout(self.horizontalLayout_26, 1, 0, 1, 1)

        self.pushButton_56 = QPushButton(self.groupBox_59)
        self.pushButton_56.setObjectName(u"pushButton_56")

        self.gridLayout_29.addWidget(self.pushButton_56, 1, 1, 1, 1)


        self.verticalLayout_15.addWidget(self.groupBox_59)

        self.groupBox_20 = QGroupBox(self.tab_5)
        self.groupBox_20.setObjectName(u"groupBox_20")
        self.groupBox_20.setCheckable(True)
        self.groupBox_20.setChecked(False)
        self.gridLayout_31 = QGridLayout(self.groupBox_20)
        self.gridLayout_31.setObjectName(u"gridLayout_31")
        self.label_25 = QLabel(self.groupBox_20)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_31.addWidget(self.label_25, 0, 0, 1, 1)

        self.comboBox_61 = QComboBox(self.groupBox_20)
        self.comboBox_61.setObjectName(u"comboBox_61")

        self.gridLayout_31.addWidget(self.comboBox_61, 0, 1, 1, 1)

        self.pushButton_57 = QPushButton(self.groupBox_20)
        self.pushButton_57.setObjectName(u"pushButton_57")

        self.gridLayout_31.addWidget(self.pushButton_57, 1, 1, 1, 1)

        self.label_173 = QLabel(self.groupBox_20)
        self.label_173.setObjectName(u"label_173")
        self.label_173.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_31.addWidget(self.label_173, 1, 0, 1, 1)


        self.verticalLayout_15.addWidget(self.groupBox_20)

        self.verticalSpacer = QSpacerItem(20, 302, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_15.addItem(self.verticalSpacer)

        self.pushButton_52 = QPushButton(self.tab_5)
        self.pushButton_52.setObjectName(u"pushButton_52")
        palette3 = QPalette()
        palette3.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette3.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Text, brush)
        palette3.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush12 = QBrush(QColor(255, 255, 255, 128))
        brush12.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Active, QPalette.PlaceholderText, brush12)
#endif
        palette3.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush13 = QBrush(QColor(255, 255, 255, 128))
        brush13.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush13)
#endif
        palette3.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette3.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette3.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette3.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush14 = QBrush(QColor(255, 255, 255, 128))
        brush14.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush14)
#endif
        self.pushButton_52.setPalette(palette3)
        self.pushButton_52.setFont(font2)
        self.pushButton_52.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_15.addWidget(self.pushButton_52)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_9 = QWidget()
        self.tab_9.setObjectName(u"tab_9")
        self.verticalLayout_19 = QVBoxLayout(self.tab_9)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.label_87 = QLabel(self.tab_9)
        self.label_87.setObjectName(u"label_87")
        sizePolicy.setHeightForWidth(self.label_87.sizePolicy().hasHeightForWidth())
        self.label_87.setSizePolicy(sizePolicy)
        self.label_87.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_87.setWordWrap(False)
        self.label_87.setMargin(0)
        self.label_87.setIndent(-1)
        self.label_87.setOpenExternalLinks(False)

        self.verticalLayout_19.addWidget(self.label_87)

        self.groupBox_31 = QGroupBox(self.tab_9)
        self.groupBox_31.setObjectName(u"groupBox_31")
        self.verticalLayout_17 = QVBoxLayout(self.groupBox_31)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.gridLayout_37 = QGridLayout()
        self.gridLayout_37.setObjectName(u"gridLayout_37")
        self.label_111 = QLabel(self.groupBox_31)
        self.label_111.setObjectName(u"label_111")

        self.gridLayout_37.addWidget(self.label_111, 3, 3, 1, 1)

        self.horizontalSlider_2 = QSlider(self.groupBox_31)
        self.horizontalSlider_2.setObjectName(u"horizontalSlider_2")
        self.horizontalSlider_2.setMinimum(1)
        self.horizontalSlider_2.setMaximum(10000)
        self.horizontalSlider_2.setValue(100)
        self.horizontalSlider_2.setOrientation(Qt.Orientation.Horizontal)

        self.gridLayout_37.addWidget(self.horizontalSlider_2, 2, 1, 1, 1)

        self.label_109 = QLabel(self.groupBox_31)
        self.label_109.setObjectName(u"label_109")

        self.gridLayout_37.addWidget(self.label_109, 2, 3, 1, 1)

        self.label_107 = QLabel(self.groupBox_31)
        self.label_107.setObjectName(u"label_107")
        self.label_107.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_37.addWidget(self.label_107, 0, 0, 1, 1)

        self.comboBox_35 = QComboBox(self.groupBox_31)
        self.comboBox_35.addItem("")
        self.comboBox_35.addItem("")
        self.comboBox_35.setObjectName(u"comboBox_35")

        self.gridLayout_37.addWidget(self.comboBox_35, 0, 1, 1, 3)

        self.label_32 = QLabel(self.groupBox_31)
        self.label_32.setObjectName(u"label_32")
        self.label_32.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_37.addWidget(self.label_32, 2, 0, 1, 1)

        self.spinBox_18 = QSpinBox(self.groupBox_31)
        self.spinBox_18.setObjectName(u"spinBox_18")
        self.spinBox_18.setEnabled(True)
        self.spinBox_18.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.spinBox_18.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spinBox_18.setMinimum(1)
        self.spinBox_18.setMaximum(999)
        self.spinBox_18.setValue(1)

        self.gridLayout_37.addWidget(self.spinBox_18, 1, 1, 1, 3)

        self.label_108 = QLabel(self.groupBox_31)
        self.label_108.setObjectName(u"label_108")
        self.label_108.setEnabled(True)
        self.label_108.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_37.addWidget(self.label_108, 1, 0, 1, 1)

        self.label_110 = QLabel(self.groupBox_31)
        self.label_110.setObjectName(u"label_110")
        self.label_110.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_37.addWidget(self.label_110, 3, 0, 1, 1)

        self.spinBox_19 = QSpinBox(self.groupBox_31)
        self.spinBox_19.setObjectName(u"spinBox_19")
        self.spinBox_19.setMinimum(1)
        self.spinBox_19.setMaximum(10000)
        self.spinBox_19.setValue(100)

        self.gridLayout_37.addWidget(self.spinBox_19, 2, 2, 1, 1)

        self.spinBox_20 = QSpinBox(self.groupBox_31)
        self.spinBox_20.setObjectName(u"spinBox_20")
        self.spinBox_20.setMinimum(1)
        self.spinBox_20.setMaximum(10000)
        self.spinBox_20.setValue(100)

        self.gridLayout_37.addWidget(self.spinBox_20, 3, 2, 1, 1)

        self.horizontalSlider_3 = QSlider(self.groupBox_31)
        self.horizontalSlider_3.setObjectName(u"horizontalSlider_3")
        self.horizontalSlider_3.setMinimum(1)
        self.horizontalSlider_3.setMaximum(10000)
        self.horizontalSlider_3.setValue(100)
        self.horizontalSlider_3.setOrientation(Qt.Orientation.Horizontal)

        self.gridLayout_37.addWidget(self.horizontalSlider_3, 3, 1, 1, 1)

        self.gridLayout_37.setColumnStretch(0, 4)
        self.gridLayout_37.setColumnStretch(1, 4)
        self.gridLayout_37.setColumnStretch(2, 1)

        self.verticalLayout_17.addLayout(self.gridLayout_37)


        self.verticalLayout_19.addWidget(self.groupBox_31)

        self.groupBox_63 = QGroupBox(self.tab_9)
        self.groupBox_63.setObjectName(u"groupBox_63")
        self.groupBox_63.setCheckable(True)
        self.groupBox_63.setChecked(False)
        self.horizontalLayout_8 = QHBoxLayout(self.groupBox_63)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_162 = QLabel(self.groupBox_63)
        self.label_162.setObjectName(u"label_162")
        self.label_162.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.label_162)

        self.comboBox_66 = QComboBox(self.groupBox_63)
        self.comboBox_66.addItem("")
        self.comboBox_66.addItem("")
        self.comboBox_66.addItem("")
        self.comboBox_66.setObjectName(u"comboBox_66")

        self.horizontalLayout_8.addWidget(self.comboBox_66)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 1)

        self.verticalLayout_19.addWidget(self.groupBox_63)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_19.addItem(self.verticalSpacer_4)

        self.tabWidget.addTab(self.tab_9, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_5 = QVBoxLayout(self.tab_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_88 = QLabel(self.tab_3)
        self.label_88.setObjectName(u"label_88")
        sizePolicy.setHeightForWidth(self.label_88.sizePolicy().hasHeightForWidth())
        self.label_88.setSizePolicy(sizePolicy)
        self.label_88.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_88.setWordWrap(False)
        self.label_88.setMargin(0)
        self.label_88.setIndent(-1)
        self.label_88.setOpenExternalLinks(False)

        self.verticalLayout_5.addWidget(self.label_88)

        self.groupBox = QGroupBox(self.tab_3)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setCheckable(True)
        self.horizontalLayout_25 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.label_14 = QLabel(self.groupBox)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_14.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_25.addWidget(self.label_14)

        self.spinBox_13 = QSpinBox(self.groupBox)
        self.spinBox_13.setObjectName(u"spinBox_13")
        font5 = QFont()
        font5.setFamilies([u"\u5fae\u8f6f\u96c5\u9ed1"])
        font5.setPointSize(9)
        font5.setBold(False)
        self.spinBox_13.setFont(font5)
        self.spinBox_13.setMinimum(1)
        self.spinBox_13.setMaximum(999999)
        self.spinBox_13.setValue(5)

        self.horizontalLayout_25.addWidget(self.spinBox_13)

        self.comboBox_25 = QComboBox(self.groupBox)
        self.comboBox_25.addItem("")
        self.comboBox_25.addItem("")
        self.comboBox_25.addItem("")
        self.comboBox_25.setObjectName(u"comboBox_25")

        self.horizontalLayout_25.addWidget(self.comboBox_25)

        self.horizontalLayout_25.setStretch(0, 2)
        self.horizontalLayout_25.setStretch(1, 2)
        self.horizontalLayout_25.setStretch(2, 1)

        self.verticalLayout_5.addWidget(self.groupBox)

        self.groupBox_16 = QGroupBox(self.tab_3)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.groupBox_16.setCheckable(True)
        self.groupBox_16.setChecked(False)
        self.gridLayout_6 = QGridLayout(self.groupBox_16)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label_78 = QLabel(self.groupBox_16)
        self.label_78.setObjectName(u"label_78")
        self.label_78.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_78, 0, 0, 1, 1)

        self.spinBox_14 = QSpinBox(self.groupBox_16)
        self.spinBox_14.setObjectName(u"spinBox_14")
        self.spinBox_14.setMaximum(999999)
        self.spinBox_14.setValue(1)

        self.gridLayout_6.addWidget(self.spinBox_14, 0, 1, 1, 1)

        self.comboBox_64 = QComboBox(self.groupBox_16)
        self.comboBox_64.addItem("")
        self.comboBox_64.addItem("")
        self.comboBox_64.addItem("")
        self.comboBox_64.setObjectName(u"comboBox_64")

        self.gridLayout_6.addWidget(self.comboBox_64, 0, 2, 1, 1)

        self.label_79 = QLabel(self.groupBox_16)
        self.label_79.setObjectName(u"label_79")
        self.label_79.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_79, 1, 0, 1, 1)

        self.spinBox_15 = QSpinBox(self.groupBox_16)
        self.spinBox_15.setObjectName(u"spinBox_15")
        self.spinBox_15.setMaximum(999999)
        self.spinBox_15.setValue(10)

        self.gridLayout_6.addWidget(self.spinBox_15, 1, 1, 1, 1)

        self.comboBox_65 = QComboBox(self.groupBox_16)
        self.comboBox_65.addItem("")
        self.comboBox_65.addItem("")
        self.comboBox_65.addItem("")
        self.comboBox_65.setObjectName(u"comboBox_65")

        self.gridLayout_6.addWidget(self.comboBox_65, 1, 2, 1, 1)

        self.gridLayout_6.setColumnStretch(0, 2)
        self.gridLayout_6.setColumnStretch(1, 2)
        self.gridLayout_6.setColumnStretch(2, 1)
        self.gridLayout_6.setColumnMinimumWidth(0, 2)
        self.gridLayout_6.setColumnMinimumWidth(1, 2)
        self.gridLayout_6.setColumnMinimumWidth(2, 1)

        self.verticalLayout_5.addWidget(self.groupBox_16)

        self.groupBox_15 = QGroupBox(self.tab_3)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.groupBox_15.setEnabled(True)
        self.groupBox_15.setCheckable(True)
        self.groupBox_15.setChecked(False)
        self.gridLayout_28 = QGridLayout(self.groupBox_15)
        self.gridLayout_28.setObjectName(u"gridLayout_28")
        self.label_15 = QLabel(self.groupBox_15)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_28.addWidget(self.label_15, 0, 0, 1, 1)

        self.timeEdit = QTimeEdit(self.groupBox_15)
        self.timeEdit.setObjectName(u"timeEdit")

        self.gridLayout_28.addWidget(self.timeEdit, 0, 1, 1, 1)

        self.label_26 = QLabel(self.groupBox_15)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_28.addWidget(self.label_26, 1, 0, 1, 1)

        self.comboBox_6 = QComboBox(self.groupBox_15)
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.setObjectName(u"comboBox_6")
        self.comboBox_6.setEnabled(False)

        self.gridLayout_28.addWidget(self.comboBox_6, 1, 1, 1, 1)

        self.gridLayout_28.setColumnStretch(0, 2)
        self.gridLayout_28.setColumnStretch(1, 1)

        self.verticalLayout_5.addWidget(self.groupBox_15)

        self.verticalSpacer_16 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_16)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab_19 = QWidget()
        self.tab_19.setObjectName(u"tab_19")
        self.verticalLayout_40 = QVBoxLayout(self.tab_19)
        self.verticalLayout_40.setObjectName(u"verticalLayout_40")
        self.label_89 = QLabel(self.tab_19)
        self.label_89.setObjectName(u"label_89")
        sizePolicy.setHeightForWidth(self.label_89.sizePolicy().hasHeightForWidth())
        self.label_89.setSizePolicy(sizePolicy)
        self.label_89.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_89.setWordWrap(False)
        self.label_89.setMargin(0)
        self.label_89.setIndent(-1)
        self.label_89.setOpenExternalLinks(False)

        self.verticalLayout_40.addWidget(self.label_89)

        self.groupBox_2 = QGroupBox(self.tab_19)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_20 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.pushButton_21 = QPushButton(self.groupBox_2)
        self.pushButton_21.setObjectName(u"pushButton_21")
        palette4 = QPalette()
        palette4.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush15 = QBrush(QColor(0, 102, 204, 255))
        brush15.setStyle(Qt.SolidPattern)
        palette4.setBrush(QPalette.Active, QPalette.Button, brush15)
        palette4.setBrush(QPalette.Active, QPalette.Text, brush)
        palette4.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette4.setBrush(QPalette.Active, QPalette.Base, brush15)
        palette4.setBrush(QPalette.Active, QPalette.Window, brush15)
        brush16 = QBrush(QColor(255, 255, 255, 128))
        brush16.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette4.setBrush(QPalette.Active, QPalette.PlaceholderText, brush16)
#endif
        palette4.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette4.setBrush(QPalette.Inactive, QPalette.Button, brush15)
        palette4.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette4.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette4.setBrush(QPalette.Inactive, QPalette.Base, brush15)
        palette4.setBrush(QPalette.Inactive, QPalette.Window, brush15)
        brush17 = QBrush(QColor(255, 255, 255, 128))
        brush17.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette4.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush17)
#endif
        palette4.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette4.setBrush(QPalette.Disabled, QPalette.Button, brush15)
        palette4.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette4.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette4.setBrush(QPalette.Disabled, QPalette.Base, brush15)
        palette4.setBrush(QPalette.Disabled, QPalette.Window, brush15)
        brush18 = QBrush(QColor(255, 255, 255, 128))
        brush18.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette4.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush18)
#endif
        self.pushButton_21.setPalette(palette4)
        self.pushButton_21.setFont(font2)
        self.pushButton_21.setStyleSheet(u"QPushButton {\n"
"    background-color: #0066CC; /* \u84dd\u8272 */\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0056B3; /* \u9f20\u6807\u60ac\u505c\u65f6\u7684\u8f83\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004C99; /* \u6309\u94ae\u6309\u4e0b\u65f6\u7684\u66f4\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"")

        self.horizontalLayout_5.addWidget(self.pushButton_21)

        self.pushButton_22 = QPushButton(self.groupBox_2)
        self.pushButton_22.setObjectName(u"pushButton_22")

        self.horizontalLayout_5.addWidget(self.pushButton_22)


        self.verticalLayout_20.addLayout(self.horizontalLayout_5)

        self.gridLayout_9 = QGridLayout()
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.label_46 = QLabel(self.groupBox_2)
        self.label_46.setObjectName(u"label_46")

        self.gridLayout_9.addWidget(self.label_46, 1, 0, 1, 1)

        self.comboBox_19 = QComboBox(self.groupBox_2)
        self.comboBox_19.addItem("")
        self.comboBox_19.addItem("")
        self.comboBox_19.setObjectName(u"comboBox_19")

        self.gridLayout_9.addWidget(self.comboBox_19, 2, 1, 1, 2)

        self.spinBox_6 = QSpinBox(self.groupBox_2)
        self.spinBox_6.setObjectName(u"spinBox_6")
        self.spinBox_6.setMinimum(1)
        self.spinBox_6.setMaximum(86400)
        self.spinBox_6.setValue(10)

        self.gridLayout_9.addWidget(self.spinBox_6, 3, 2, 1, 1)

        self.comboBox_18 = QComboBox(self.groupBox_2)
        self.comboBox_18.setObjectName(u"comboBox_18")

        self.gridLayout_9.addWidget(self.comboBox_18, 1, 1, 1, 2)

        self.label_48 = QLabel(self.groupBox_2)
        self.label_48.setObjectName(u"label_48")
        self.label_48.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_9.addWidget(self.label_48, 3, 0, 1, 2)

        self.label_45 = QLabel(self.groupBox_2)
        self.label_45.setObjectName(u"label_45")

        self.gridLayout_9.addWidget(self.label_45, 0, 0, 1, 1)

        self.comboBox_17 = QComboBox(self.groupBox_2)
        self.comboBox_17.setObjectName(u"comboBox_17")

        self.gridLayout_9.addWidget(self.comboBox_17, 0, 1, 1, 2)

        self.label_47 = QLabel(self.groupBox_2)
        self.label_47.setObjectName(u"label_47")

        self.gridLayout_9.addWidget(self.label_47, 2, 0, 1, 1)


        self.verticalLayout_20.addLayout(self.gridLayout_9)


        self.verticalLayout_40.addWidget(self.groupBox_2)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.groupBox_79 = QGroupBox(self.tab_19)
        self.groupBox_79.setObjectName(u"groupBox_79")
        self.gridLayout_75 = QGridLayout(self.groupBox_79)
        self.gridLayout_75.setObjectName(u"gridLayout_75")
        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName(u"horizontalLayout_36")
        self.horizontalSlider_6 = QSlider(self.groupBox_79)
        self.horizontalSlider_6.setObjectName(u"horizontalSlider_6")
        self.horizontalSlider_6.setMaximum(100)
        self.horizontalSlider_6.setValue(80)
        self.horizontalSlider_6.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_36.addWidget(self.horizontalSlider_6)

        self.label_182 = QLabel(self.groupBox_79)
        self.label_182.setObjectName(u"label_182")

        self.horizontalLayout_36.addWidget(self.label_182)


        self.gridLayout_75.addLayout(self.horizontalLayout_36, 0, 1, 1, 1)

        self.label_183 = QLabel(self.groupBox_79)
        self.label_183.setObjectName(u"label_183")

        self.gridLayout_75.addWidget(self.label_183, 0, 0, 1, 1)


        self.horizontalLayout_33.addWidget(self.groupBox_79)

        self.groupBox_61 = QGroupBox(self.tab_19)
        self.groupBox_61.setObjectName(u"groupBox_61")
        self.groupBox_61.setEnabled(True)
        self.groupBox_61.setCheckable(True)
        self.groupBox_61.setChecked(False)
        self.horizontalLayout_24 = QHBoxLayout(self.groupBox_61)
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.label_160 = QLabel(self.groupBox_61)
        self.label_160.setObjectName(u"label_160")
        self.label_160.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_24.addWidget(self.label_160)

        self.pushButton_54 = QPushButton(self.groupBox_61)
        self.pushButton_54.setObjectName(u"pushButton_54")

        self.horizontalLayout_24.addWidget(self.pushButton_54)


        self.horizontalLayout_33.addWidget(self.groupBox_61)

        self.horizontalLayout_33.setStretch(0, 1)
        self.horizontalLayout_33.setStretch(1, 1)

        self.verticalLayout_40.addLayout(self.horizontalLayout_33)

        self.verticalSpacer_8 = QSpacerItem(20, 211, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_40.addItem(self.verticalSpacer_8)

        self.tabWidget.addTab(self.tab_19, "")
        self.tab_42 = QWidget()
        self.tab_42.setObjectName(u"tab_42")
        self.verticalLayout_38 = QVBoxLayout(self.tab_42)
        self.verticalLayout_38.setObjectName(u"verticalLayout_38")
        self.label_165 = QLabel(self.tab_42)
        self.label_165.setObjectName(u"label_165")
        sizePolicy.setHeightForWidth(self.label_165.sizePolicy().hasHeightForWidth())
        self.label_165.setSizePolicy(sizePolicy)
        self.label_165.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_165.setWordWrap(False)
        self.label_165.setMargin(0)
        self.label_165.setIndent(-1)
        self.label_165.setOpenExternalLinks(False)

        self.verticalLayout_38.addWidget(self.label_165)

        self.groupBox_70 = QGroupBox(self.tab_42)
        self.groupBox_70.setObjectName(u"groupBox_70")
        self.gridLayout_68 = QGridLayout(self.groupBox_70)
        self.gridLayout_68.setObjectName(u"gridLayout_68")
        self.label_20 = QLabel(self.groupBox_70)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_20, 0, 0, 1, 1)

        self.lineEdit_18 = QLineEdit(self.groupBox_70)
        self.lineEdit_18.setObjectName(u"lineEdit_18")

        self.gridLayout_68.addWidget(self.lineEdit_18, 0, 1, 1, 1)

        self.label_169 = QLabel(self.groupBox_70)
        self.label_169.setObjectName(u"label_169")
        self.label_169.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_169, 1, 2, 1, 1)

        self.label_170 = QLabel(self.groupBox_70)
        self.label_170.setObjectName(u"label_170")
        self.label_170.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_170, 4, 0, 1, 1)

        self.label_168 = QLabel(self.groupBox_70)
        self.label_168.setObjectName(u"label_168")
        self.label_168.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_168, 1, 0, 1, 1)

        self.label_171 = QLabel(self.groupBox_70)
        self.label_171.setObjectName(u"label_171")
        self.label_171.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_171, 4, 2, 1, 1)

        self.spinBox_28 = QSpinBox(self.groupBox_70)
        self.spinBox_28.setObjectName(u"spinBox_28")
        self.spinBox_28.setMaximum(100000)
        self.spinBox_28.setValue(60)

        self.gridLayout_68.addWidget(self.spinBox_28, 4, 1, 1, 1)

        self.comboBox_68 = QComboBox(self.groupBox_70)
        self.comboBox_68.addItem("")
        self.comboBox_68.addItem("")
        self.comboBox_68.addItem("")
        self.comboBox_68.addItem("")
        self.comboBox_68.addItem("")
        self.comboBox_68.setObjectName(u"comboBox_68")

        self.gridLayout_68.addWidget(self.comboBox_68, 1, 1, 1, 1)

        self.label_166 = QLabel(self.groupBox_70)
        self.label_166.setObjectName(u"label_166")
        self.label_166.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_68.addWidget(self.label_166, 2, 0, 1, 1)

        self.comboBox_69 = QComboBox(self.groupBox_70)
        self.comboBox_69.addItem("")
        self.comboBox_69.addItem("")
        self.comboBox_69.setObjectName(u"comboBox_69")

        self.gridLayout_68.addWidget(self.comboBox_69, 2, 1, 1, 1)

        self.gridLayout_68.setColumnStretch(0, 3)
        self.gridLayout_68.setColumnStretch(1, 3)

        self.verticalLayout_38.addWidget(self.groupBox_70)

        self.verticalSpacer_37 = QSpacerItem(20, 357, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_38.addItem(self.verticalSpacer_37)

        self.tabWidget.addTab(self.tab_42, "")
        self.tab_23 = QWidget()
        self.tab_23.setObjectName(u"tab_23")
        self.verticalLayout_76 = QVBoxLayout(self.tab_23)
        self.verticalLayout_76.setObjectName(u"verticalLayout_76")
        self.groupBox_44 = QGroupBox(self.tab_23)
        self.groupBox_44.setObjectName(u"groupBox_44")
        self.gridLayout_47 = QGridLayout(self.groupBox_44)
        self.gridLayout_47.setObjectName(u"gridLayout_47")
        self.label_136 = QLabel(self.groupBox_44)
        self.label_136.setObjectName(u"label_136")

        self.gridLayout_47.addWidget(self.label_136, 0, 0, 1, 2)

        self.comboBox_45 = QComboBox(self.groupBox_44)
        self.comboBox_45.setObjectName(u"comboBox_45")

        self.gridLayout_47.addWidget(self.comboBox_45, 0, 2, 1, 1)

        self.label_137 = QLabel(self.groupBox_44)
        self.label_137.setObjectName(u"label_137")

        self.gridLayout_47.addWidget(self.label_137, 1, 0, 1, 1)

        self.comboBox_46 = QComboBox(self.groupBox_44)
        self.comboBox_46.setObjectName(u"comboBox_46")

        self.gridLayout_47.addWidget(self.comboBox_46, 1, 2, 1, 1)

        self.label_138 = QLabel(self.groupBox_44)
        self.label_138.setObjectName(u"label_138")

        self.gridLayout_47.addWidget(self.label_138, 2, 0, 1, 1)

        self.lineEdit_23 = QLineEdit(self.groupBox_44)
        self.lineEdit_23.setObjectName(u"lineEdit_23")

        self.gridLayout_47.addWidget(self.lineEdit_23, 2, 2, 1, 1)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.checkBox_9 = QCheckBox(self.groupBox_44)
        self.checkBox_9.setObjectName(u"checkBox_9")

        self.horizontalLayout_17.addWidget(self.checkBox_9)

        self.pushButton_29 = QPushButton(self.groupBox_44)
        self.pushButton_29.setObjectName(u"pushButton_29")

        self.horizontalLayout_17.addWidget(self.pushButton_29)


        self.gridLayout_47.addLayout(self.horizontalLayout_17, 3, 0, 1, 3)


        self.verticalLayout_76.addWidget(self.groupBox_44)

        self.groupBox_45 = QGroupBox(self.tab_23)
        self.groupBox_45.setObjectName(u"groupBox_45")
        self.gridLayout_50 = QGridLayout(self.groupBox_45)
        self.gridLayout_50.setObjectName(u"gridLayout_50")
        self.comboBox_47 = QComboBox(self.groupBox_45)
        self.comboBox_47.setObjectName(u"comboBox_47")

        self.gridLayout_50.addWidget(self.comboBox_47, 0, 1, 1, 1)

        self.label_139 = QLabel(self.groupBox_45)
        self.label_139.setObjectName(u"label_139")
        self.label_139.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_50.addWidget(self.label_139, 0, 0, 1, 1)

        self.horizontalSpacer_7 = QSpacerItem(84, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_50.addItem(self.horizontalSpacer_7, 2, 0, 1, 1)

        self.pushButton_35 = QPushButton(self.groupBox_45)
        self.pushButton_35.setObjectName(u"pushButton_35")
        self.pushButton_35.setFont(font4)

        self.gridLayout_50.addWidget(self.pushButton_35, 2, 1, 1, 1)

        self.gridLayout_50.setColumnStretch(0, 1)
        self.gridLayout_50.setColumnStretch(1, 1)

        self.verticalLayout_76.addWidget(self.groupBox_45)

        self.verticalSpacer_29 = QSpacerItem(20, 160, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_76.addItem(self.verticalSpacer_29)

        self.pushButton_36 = QPushButton(self.tab_23)
        self.pushButton_36.setObjectName(u"pushButton_36")
        palette5 = QPalette()
        palette5.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette5.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette5.setBrush(QPalette.Active, QPalette.Text, brush)
        palette5.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette5.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette5.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush19 = QBrush(QColor(255, 255, 255, 128))
        brush19.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette5.setBrush(QPalette.Active, QPalette.PlaceholderText, brush19)
#endif
        palette5.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette5.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette5.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette5.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette5.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette5.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush20 = QBrush(QColor(255, 255, 255, 128))
        brush20.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette5.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush20)
#endif
        palette5.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette5.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette5.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette5.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette5.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette5.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush21 = QBrush(QColor(255, 255, 255, 128))
        brush21.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette5.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush21)
#endif
        self.pushButton_36.setPalette(palette5)
        self.pushButton_36.setFont(font2)
        self.pushButton_36.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_76.addWidget(self.pushButton_36)

        self.tabWidget.addTab(self.tab_23, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_63 = QVBoxLayout(self.tab_4)
        self.verticalLayout_63.setObjectName(u"verticalLayout_63")
        self.label_90 = QLabel(self.tab_4)
        self.label_90.setObjectName(u"label_90")
        sizePolicy.setHeightForWidth(self.label_90.sizePolicy().hasHeightForWidth())
        self.label_90.setSizePolicy(sizePolicy)
        self.label_90.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_90.setWordWrap(False)
        self.label_90.setMargin(0)
        self.label_90.setIndent(-1)
        self.label_90.setOpenExternalLinks(False)

        self.verticalLayout_63.addWidget(self.label_90)

        self.groupBox_22 = QGroupBox(self.tab_4)
        self.groupBox_22.setObjectName(u"groupBox_22")
        self.groupBox_22.setCheckable(True)
        self.verticalLayout_7 = QVBoxLayout(self.groupBox_22)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_17 = QLabel(self.groupBox_22)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.label_17, 1, 0, 1, 1)

        self.label_16 = QLabel(self.groupBox_22)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.label_16, 0, 0, 1, 1)

        self.lineEdit_3 = QLineEdit(self.groupBox_22)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.gridLayout_4.addWidget(self.lineEdit_3, 1, 1, 1, 1)

        self.label_105 = QLabel(self.groupBox_22)
        self.label_105.setObjectName(u"label_105")

        self.gridLayout_4.addWidget(self.label_105, 1, 2, 1, 1)

        self.comboBox_5 = QComboBox(self.groupBox_22)
        self.comboBox_5.addItem("")
        self.comboBox_5.addItem("")
        self.comboBox_5.setObjectName(u"comboBox_5")

        self.gridLayout_4.addWidget(self.comboBox_5, 0, 1, 1, 2)

        self.gridLayout_4.setColumnStretch(0, 4)
        self.gridLayout_4.setColumnStretch(1, 4)
        self.gridLayout_4.setColumnStretch(2, 1)

        self.verticalLayout_7.addLayout(self.gridLayout_4)


        self.verticalLayout_63.addWidget(self.groupBox_22)

        self.groupBox_29 = QGroupBox(self.tab_4)
        self.groupBox_29.setObjectName(u"groupBox_29")
        self.groupBox_29.setCheckable(True)
        self.groupBox_29.setChecked(False)
        self.verticalLayout_55 = QVBoxLayout(self.groupBox_29)
        self.verticalLayout_55.setObjectName(u"verticalLayout_55")
        self.gridLayout_36 = QGridLayout()
        self.gridLayout_36.setObjectName(u"gridLayout_36")
        self.spinBox_16 = QSpinBox(self.groupBox_29)
        self.spinBox_16.setObjectName(u"spinBox_16")
        self.spinBox_16.setMaximum(999999)
        self.spinBox_16.setValue(1)

        self.gridLayout_36.addWidget(self.spinBox_16, 0, 1, 1, 1)

        self.spinBox_17 = QSpinBox(self.groupBox_29)
        self.spinBox_17.setObjectName(u"spinBox_17")
        self.spinBox_17.setMaximum(999999)
        self.spinBox_17.setValue(500)

        self.gridLayout_36.addWidget(self.spinBox_17, 1, 1, 1, 1)

        self.label_103 = QLabel(self.groupBox_29)
        self.label_103.setObjectName(u"label_103")
        self.label_103.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_36.addWidget(self.label_103, 1, 0, 1, 1)

        self.label_101 = QLabel(self.groupBox_29)
        self.label_101.setObjectName(u"label_101")
        self.label_101.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_36.addWidget(self.label_101, 0, 0, 1, 1)

        self.label_104 = QLabel(self.groupBox_29)
        self.label_104.setObjectName(u"label_104")

        self.gridLayout_36.addWidget(self.label_104, 0, 2, 1, 1)

        self.label_106 = QLabel(self.groupBox_29)
        self.label_106.setObjectName(u"label_106")

        self.gridLayout_36.addWidget(self.label_106, 1, 2, 1, 1)

        self.gridLayout_36.setColumnStretch(0, 4)
        self.gridLayout_36.setColumnStretch(1, 4)
        self.gridLayout_36.setColumnStretch(2, 1)

        self.verticalLayout_55.addLayout(self.gridLayout_36)


        self.verticalLayout_63.addWidget(self.groupBox_29)

        self.verticalSpacer_3 = QSpacerItem(20, 302, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_63.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.gridLayout_48 = QGridLayout(self.tab_6)
        self.gridLayout_48.setObjectName(u"gridLayout_48")
        self.checkBox_2 = QCheckBox(self.tab_6)
        self.checkBox_2.setObjectName(u"checkBox_2")

        self.gridLayout_48.addWidget(self.checkBox_2, 2, 0, 1, 1)

        self.label_91 = QLabel(self.tab_6)
        self.label_91.setObjectName(u"label_91")
        sizePolicy.setHeightForWidth(self.label_91.sizePolicy().hasHeightForWidth())
        self.label_91.setSizePolicy(sizePolicy)
        self.label_91.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_91.setWordWrap(False)
        self.label_91.setMargin(0)
        self.label_91.setIndent(-1)
        self.label_91.setOpenExternalLinks(False)

        self.gridLayout_48.addWidget(self.label_91, 0, 0, 1, 2)

        self.pushButton_28 = QPushButton(self.tab_6)
        self.pushButton_28.setObjectName(u"pushButton_28")
        self.pushButton_28.setFont(font4)

        self.gridLayout_48.addWidget(self.pushButton_28, 2, 1, 1, 1)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.label_18 = QLabel(self.tab_6)
        self.label_18.setObjectName(u"label_18")

        self.verticalLayout_8.addWidget(self.label_18)

        self.textEdit = QTextEdit(self.tab_6)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout_8.addWidget(self.textEdit)


        self.gridLayout_48.addLayout(self.verticalLayout_8, 1, 0, 1, 2)

        self.tabWidget.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.verticalLayout_87 = QVBoxLayout(self.tab_7)
        self.verticalLayout_87.setObjectName(u"verticalLayout_87")
        self.label_24 = QLabel(self.tab_7)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_24.setWordWrap(False)

        self.verticalLayout_87.addWidget(self.label_24)

        self.groupBox_65 = QGroupBox(self.tab_7)
        self.groupBox_65.setObjectName(u"groupBox_65")
        self.gridLayout_62 = QGridLayout(self.groupBox_65)
        self.gridLayout_62.setObjectName(u"gridLayout_62")
        self.label_163 = QLabel(self.groupBox_65)
        self.label_163.setObjectName(u"label_163")
        self.label_163.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_62.addWidget(self.label_163, 0, 0, 1, 1)

        self.keySequenceEdit = QKeySequenceEdit(self.groupBox_65)
        self.keySequenceEdit.setObjectName(u"keySequenceEdit")
        self.keySequenceEdit.setFont(font4)
        self.keySequenceEdit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.gridLayout_62.addWidget(self.keySequenceEdit, 0, 1, 1, 1)

        self.label_167 = QLabel(self.groupBox_65)
        self.label_167.setObjectName(u"label_167")
        self.label_167.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_62.addWidget(self.label_167, 1, 0, 1, 1)

        self.spinBox_27 = QSpinBox(self.groupBox_65)
        self.spinBox_27.setObjectName(u"spinBox_27")
        self.spinBox_27.setMinimum(1)
        self.spinBox_27.setMaximum(1000000)
        self.spinBox_27.setValue(100)

        self.gridLayout_62.addWidget(self.spinBox_27, 1, 1, 1, 1)

        self.gridLayout_62.setColumnStretch(0, 1)
        self.gridLayout_62.setColumnStretch(1, 1)
        self.gridLayout_62.setRowMinimumHeight(0, 1)
        self.gridLayout_62.setRowMinimumHeight(1, 1)

        self.verticalLayout_87.addWidget(self.groupBox_65)

        self.verticalSpacer_36 = QSpacerItem(20, 448, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_87.addItem(self.verticalSpacer_36)

        self.groupBox_80 = QGroupBox(self.tab_7)
        self.groupBox_80.setObjectName(u"groupBox_80")
        self.horizontalLayout_38 = QHBoxLayout(self.groupBox_80)
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.label_179 = QLabel(self.groupBox_80)
        self.label_179.setObjectName(u"label_179")

        self.verticalLayout_10.addWidget(self.label_179)

        self.horizontalLayout_37 = QHBoxLayout()
        self.horizontalLayout_37.setObjectName(u"horizontalLayout_37")
        self.label_186 = QLabel(self.groupBox_80)
        self.label_186.setObjectName(u"label_186")

        self.horizontalLayout_37.addWidget(self.label_186)

        self.pushButton_77 = QPushButton(self.groupBox_80)
        self.pushButton_77.setObjectName(u"pushButton_77")
        self.pushButton_77.setStyleSheet(u"font-size: 14px; /* \u8bbe\u7f6e\u5b57\u4f53\u5927\u5c0f\uff0c\u53ef\u4ee5\u6839\u636e\u9700\u8981\u8c03\u6574 */")

        self.horizontalLayout_37.addWidget(self.pushButton_77)

        self.pushButton_78 = QPushButton(self.groupBox_80)
        self.pushButton_78.setObjectName(u"pushButton_78")
        self.pushButton_78.setStyleSheet(u"font-size: 14px; /* \u8bbe\u7f6e\u5b57\u4f53\u5927\u5c0f\uff0c\u53ef\u4ee5\u6839\u636e\u9700\u8981\u8c03\u6574 */")

        self.horizontalLayout_37.addWidget(self.pushButton_78)

        self.horizontalSpacer_26 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_37.addItem(self.horizontalSpacer_26)


        self.verticalLayout_10.addLayout(self.horizontalLayout_37)

        self.label_185 = QLabel(self.groupBox_80)
        self.label_185.setObjectName(u"label_185")

        self.verticalLayout_10.addWidget(self.label_185)

        self.label_184 = QLabel(self.groupBox_80)
        self.label_184.setObjectName(u"label_184")

        self.verticalLayout_10.addWidget(self.label_184)


        self.horizontalLayout_38.addLayout(self.verticalLayout_10)

        self.horizontalSpacer_28 = QSpacerItem(240, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_38.addItem(self.horizontalSpacer_28)


        self.verticalLayout_87.addWidget(self.groupBox_80)

        self.tabWidget.addTab(self.tab_7, "")
        self.tab_8 = QWidget()
        self.tab_8.setObjectName(u"tab_8")
        self.verticalLayout_11 = QVBoxLayout(self.tab_8)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.label_30 = QLabel(self.tab_8)
        self.label_30.setObjectName(u"label_30")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_30.sizePolicy().hasHeightForWidth())
        self.label_30.setSizePolicy(sizePolicy1)
        self.label_30.setFrameShadow(QFrame.Shadow.Plain)
        self.label_30.setLineWidth(1)
        self.label_30.setTextFormat(Qt.TextFormat.PlainText)
        self.label_30.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_30.setWordWrap(False)

        self.verticalLayout_11.addWidget(self.label_30)

        self.groupBox_23 = QGroupBox(self.tab_8)
        self.groupBox_23.setObjectName(u"groupBox_23")
        self.gridLayout_60 = QGridLayout(self.groupBox_23)
        self.gridLayout_60.setObjectName(u"gridLayout_60")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_27 = QLabel(self.groupBox_23)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.label_27.setWordWrap(False)

        self.horizontalLayout_7.addWidget(self.label_27)

        self.spinBox_3 = QSpinBox(self.groupBox_23)
        self.spinBox_3.setObjectName(u"spinBox_3")
        self.spinBox_3.setMinimum(1)
        self.spinBox_3.setMaximum(999)
        self.spinBox_3.setValue(10)

        self.horizontalLayout_7.addWidget(self.spinBox_3)

        self.label_28 = QLabel(self.groupBox_23)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.label_28)

        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(2, 1)

        self.gridLayout_60.addLayout(self.horizontalLayout_7, 0, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_60.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.radioButton_zi = QRadioButton(self.groupBox_23)
        self.radioButton_zi.setObjectName(u"radioButton_zi")
        self.radioButton_zi.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.gridLayout_60.addWidget(self.radioButton_zi, 1, 1, 1, 1)

        self.label_29 = QLabel(self.groupBox_23)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.label_29.setWordWrap(False)

        self.gridLayout_60.addWidget(self.label_29, 1, 2, 1, 1)

        self.radioButton = QRadioButton(self.groupBox_23)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.radioButton.setChecked(True)

        self.gridLayout_60.addWidget(self.radioButton, 0, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_60.addItem(self.horizontalSpacer_2, 1, 0, 1, 1)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_60.addItem(self.horizontalSpacer_11, 0, 3, 1, 1)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_60.addItem(self.horizontalSpacer_12, 1, 3, 1, 1)


        self.verticalLayout_11.addWidget(self.groupBox_23)

        self.verticalSpacer_9 = QSpacerItem(20, 157, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_9)

        self.tabWidget.addTab(self.tab_8, "")
        self.tab_14 = QWidget()
        self.tab_14.setObjectName(u"tab_14")
        self.verticalLayout_29 = QVBoxLayout(self.tab_14)
        self.verticalLayout_29.setObjectName(u"verticalLayout_29")
        self.label_67 = QLabel(self.tab_14)
        self.label_67.setObjectName(u"label_67")
        self.label_67.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_67.setWordWrap(False)

        self.verticalLayout_29.addWidget(self.label_67)

        self.groupBox_64 = QGroupBox(self.tab_14)
        self.groupBox_64.setObjectName(u"groupBox_64")
        self.verticalLayout_14 = QVBoxLayout(self.groupBox_64)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.gridLayout_17 = QGridLayout()
        self.gridLayout_17.setObjectName(u"gridLayout_17")
        self.label_57 = QLabel(self.groupBox_64)
        self.label_57.setObjectName(u"label_57")
        self.label_57.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_17.addWidget(self.label_57, 0, 0, 1, 1)

        self.pushButton_12 = QPushButton(self.groupBox_64)
        self.pushButton_12.setObjectName(u"pushButton_12")

        self.gridLayout_17.addWidget(self.pushButton_12, 0, 1, 1, 1)

        self.label_58 = QLabel(self.groupBox_64)
        self.label_58.setObjectName(u"label_58")
        self.label_58.setFont(font4)
        self.label_58.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_17.addWidget(self.label_58, 1, 0, 1, 1)

        self.label_59 = QLabel(self.groupBox_64)
        self.label_59.setObjectName(u"label_59")
        self.label_59.setFont(font4)
        self.label_59.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_17.addWidget(self.label_59, 1, 1, 1, 1)

        self.label_61 = QLabel(self.groupBox_64)
        self.label_61.setObjectName(u"label_61")
        self.label_61.setFont(font4)
        self.label_61.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_17.addWidget(self.label_61, 2, 1, 1, 1)

        self.label_60 = QLabel(self.groupBox_64)
        self.label_60.setObjectName(u"label_60")
        self.label_60.setFont(font4)
        self.label_60.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_17.addWidget(self.label_60, 2, 0, 1, 1)


        self.verticalLayout_14.addLayout(self.gridLayout_17)

        self.gridLayout_18 = QGridLayout()
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.pushButton_13 = QPushButton(self.groupBox_64)
        self.pushButton_13.setObjectName(u"pushButton_13")

        self.gridLayout_18.addWidget(self.pushButton_13, 0, 1, 1, 1)

        self.label_64 = QLabel(self.groupBox_64)
        self.label_64.setObjectName(u"label_64")
        self.label_64.setFont(font4)
        self.label_64.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_18.addWidget(self.label_64, 2, 0, 1, 1)

        self.label_63 = QLabel(self.groupBox_64)
        self.label_63.setObjectName(u"label_63")
        self.label_63.setFont(font4)
        self.label_63.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_18.addWidget(self.label_63, 1, 0, 1, 1)

        self.label_62 = QLabel(self.groupBox_64)
        self.label_62.setObjectName(u"label_62")
        self.label_62.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_18.addWidget(self.label_62, 0, 0, 1, 1)

        self.label_66 = QLabel(self.groupBox_64)
        self.label_66.setObjectName(u"label_66")
        self.label_66.setFont(font4)
        self.label_66.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_18.addWidget(self.label_66, 2, 1, 1, 1)

        self.label_65 = QLabel(self.groupBox_64)
        self.label_65.setObjectName(u"label_65")
        self.label_65.setFont(font4)
        self.label_65.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_18.addWidget(self.label_65, 1, 1, 1, 1)


        self.verticalLayout_14.addLayout(self.gridLayout_18)

        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_13)

        self.checkBox_8 = QCheckBox(self.groupBox_64)
        self.checkBox_8.setObjectName(u"checkBox_8")
        self.checkBox_8.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.checkBox_8.setAutoFillBackground(False)

        self.horizontalLayout_27.addWidget(self.checkBox_8)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_14)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_15)

        self.checkBox_7 = QCheckBox(self.groupBox_64)
        self.checkBox_7.setObjectName(u"checkBox_7")
        self.checkBox_7.setAcceptDrops(False)
        self.checkBox_7.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.checkBox_7.setAutoFillBackground(False)
        self.checkBox_7.setAutoRepeat(False)
        self.checkBox_7.setAutoExclusive(False)
        self.checkBox_7.setTristate(False)

        self.horizontalLayout_27.addWidget(self.checkBox_7)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_16)


        self.verticalLayout_14.addLayout(self.horizontalLayout_27)

        self.verticalSpacer_42 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_14.addItem(self.verticalSpacer_42)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName(u"horizontalLayout_41")
        self.label_199 = QLabel(self.groupBox_64)
        self.label_199.setObjectName(u"label_199")
        self.label_199.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_41.addWidget(self.label_199)

        self.spinBox_32 = QSpinBox(self.groupBox_64)
        self.spinBox_32.setObjectName(u"spinBox_32")
        self.spinBox_32.setMaximum(999999)
        self.spinBox_32.setValue(300)

        self.horizontalLayout_41.addWidget(self.spinBox_32)

        self.label_200 = QLabel(self.groupBox_64)
        self.label_200.setObjectName(u"label_200")

        self.horizontalLayout_41.addWidget(self.label_200)


        self.verticalLayout_14.addLayout(self.horizontalLayout_41)


        self.verticalLayout_29.addWidget(self.groupBox_64)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_29.addItem(self.verticalSpacer_10)

        self.groupBox_84 = QGroupBox(self.tab_14)
        self.groupBox_84.setObjectName(u"groupBox_84")
        self.horizontalLayout_42 = QHBoxLayout(self.groupBox_84)
        self.horizontalLayout_42.setObjectName(u"horizontalLayout_42")
        self.horizontalSpacer_30 = QSpacerItem(206, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_42.addItem(self.horizontalSpacer_30)

        self.pushButton_83 = QPushButton(self.groupBox_84)
        self.pushButton_83.setObjectName(u"pushButton_83")

        self.horizontalLayout_42.addWidget(self.pushButton_83)

        self.horizontalSpacer_31 = QSpacerItem(206, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_42.addItem(self.horizontalSpacer_31)


        self.verticalLayout_29.addWidget(self.groupBox_84)

        self.pushButton_14 = QPushButton(self.tab_14)
        self.pushButton_14.setObjectName(u"pushButton_14")
        palette6 = QPalette()
        palette6.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette6.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette6.setBrush(QPalette.Active, QPalette.Text, brush)
        palette6.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette6.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette6.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush22 = QBrush(QColor(255, 255, 255, 128))
        brush22.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette6.setBrush(QPalette.Active, QPalette.PlaceholderText, brush22)
#endif
        palette6.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette6.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette6.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette6.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette6.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette6.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush23 = QBrush(QColor(255, 255, 255, 128))
        brush23.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette6.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush23)
#endif
        palette6.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette6.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette6.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette6.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette6.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette6.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush24 = QBrush(QColor(255, 255, 255, 128))
        brush24.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette6.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush24)
#endif
        self.pushButton_14.setPalette(palette6)
        self.pushButton_14.setFont(font2)
        self.pushButton_14.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_29.addWidget(self.pushButton_14)

        self.tabWidget.addTab(self.tab_14, "")
        self.tab_10 = QWidget()
        self.tab_10.setObjectName(u"tab_10")
        self.verticalLayout_42 = QVBoxLayout(self.tab_10)
        self.verticalLayout_42.setObjectName(u"verticalLayout_42")
        self.label_92 = QLabel(self.tab_10)
        self.label_92.setObjectName(u"label_92")
        sizePolicy.setHeightForWidth(self.label_92.sizePolicy().hasHeightForWidth())
        self.label_92.setSizePolicy(sizePolicy)
        self.label_92.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_92.setWordWrap(False)
        self.label_92.setMargin(0)
        self.label_92.setIndent(-1)
        self.label_92.setOpenExternalLinks(False)

        self.verticalLayout_42.addWidget(self.label_92)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_5 = QPushButton(self.tab_10)
        self.pushButton_5.setObjectName(u"pushButton_5")
        palette7 = QPalette()
        palette7.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette7.setBrush(QPalette.Active, QPalette.Button, brush15)
        palette7.setBrush(QPalette.Active, QPalette.Text, brush)
        palette7.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette7.setBrush(QPalette.Active, QPalette.Base, brush15)
        palette7.setBrush(QPalette.Active, QPalette.Window, brush15)
        brush25 = QBrush(QColor(255, 255, 255, 128))
        brush25.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette7.setBrush(QPalette.Active, QPalette.PlaceholderText, brush25)
#endif
        palette7.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette7.setBrush(QPalette.Inactive, QPalette.Button, brush15)
        palette7.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette7.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette7.setBrush(QPalette.Inactive, QPalette.Base, brush15)
        palette7.setBrush(QPalette.Inactive, QPalette.Window, brush15)
        brush26 = QBrush(QColor(255, 255, 255, 128))
        brush26.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette7.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush26)
#endif
        palette7.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette7.setBrush(QPalette.Disabled, QPalette.Button, brush15)
        palette7.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette7.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette7.setBrush(QPalette.Disabled, QPalette.Base, brush15)
        palette7.setBrush(QPalette.Disabled, QPalette.Window, brush15)
        brush27 = QBrush(QColor(255, 255, 255, 128))
        brush27.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette7.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush27)
#endif
        self.pushButton_5.setPalette(palette7)
        self.pushButton_5.setFont(font2)
        self.pushButton_5.setStyleSheet(u"QPushButton {\n"
"    background-color: #0066CC; /* \u84dd\u8272 */\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0056B3; /* \u9f20\u6807\u60ac\u505c\u65f6\u7684\u8f83\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004C99; /* \u6309\u94ae\u6309\u4e0b\u65f6\u7684\u66f4\u6df1\u84dd\u8272\uff0c\u901a\u8fc7\u8c03\u6574#0066CC\u7684\u660e\u5ea6\u5f97\u5230 */\n"
"}\n"
"")

        self.horizontalLayout_2.addWidget(self.pushButton_5)

        self.pushButton_8 = QPushButton(self.tab_10)
        self.pushButton_8.setObjectName(u"pushButton_8")

        self.horizontalLayout_2.addWidget(self.pushButton_8)


        self.verticalLayout_42.addLayout(self.horizontalLayout_2)

        self.groupBox_67 = QGroupBox(self.tab_10)
        self.groupBox_67.setObjectName(u"groupBox_67")
        self.gridLayout_7 = QGridLayout(self.groupBox_67)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.label_37 = QLabel(self.groupBox_67)
        self.label_37.setObjectName(u"label_37")

        self.gridLayout_7.addWidget(self.label_37, 0, 0, 1, 1)

        self.comboBox_12 = QComboBox(self.groupBox_67)
        self.comboBox_12.setObjectName(u"comboBox_12")
        self.comboBox_12.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout_7.addWidget(self.comboBox_12, 0, 1, 1, 1)

        self.label_38 = QLabel(self.groupBox_67)
        self.label_38.setObjectName(u"label_38")

        self.gridLayout_7.addWidget(self.label_38, 1, 0, 1, 1)

        self.comboBox_13 = QComboBox(self.groupBox_67)
        self.comboBox_13.setObjectName(u"comboBox_13")

        self.gridLayout_7.addWidget(self.comboBox_13, 1, 1, 1, 1)

        self.label_39 = QLabel(self.groupBox_67)
        self.label_39.setObjectName(u"label_39")

        self.gridLayout_7.addWidget(self.label_39, 2, 0, 1, 1)

        self.lineEdit_4 = QLineEdit(self.groupBox_67)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.gridLayout_7.addWidget(self.lineEdit_4, 2, 1, 1, 1)

        self.gridLayout_7.setColumnStretch(0, 1)
        self.gridLayout_7.setColumnStretch(1, 5)

        self.verticalLayout_42.addWidget(self.groupBox_67)

        self.groupBox_66 = QGroupBox(self.tab_10)
        self.groupBox_66.setObjectName(u"groupBox_66")
        self.gridLayout_66 = QGridLayout(self.groupBox_66)
        self.gridLayout_66.setObjectName(u"gridLayout_66")
        self.comboBox_15 = QComboBox(self.groupBox_66)
        self.comboBox_15.setObjectName(u"comboBox_15")

        self.gridLayout_66.addWidget(self.comboBox_15, 1, 1, 1, 1)

        self.comboBox_14 = QComboBox(self.groupBox_66)
        self.comboBox_14.setObjectName(u"comboBox_14")
        self.comboBox_14.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout_66.addWidget(self.comboBox_14, 0, 1, 1, 1)

        self.label_40 = QLabel(self.groupBox_66)
        self.label_40.setObjectName(u"label_40")

        self.gridLayout_66.addWidget(self.label_40, 0, 0, 1, 1)

        self.label_41 = QLabel(self.groupBox_66)
        self.label_41.setObjectName(u"label_41")

        self.gridLayout_66.addWidget(self.label_41, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_17)

        self.checkBox_3 = QCheckBox(self.groupBox_66)
        self.checkBox_3.setObjectName(u"checkBox_3")

        self.horizontalLayout.addWidget(self.checkBox_3)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_18)

        self.horizontalSpacer_19 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_19)

        self.checkBox_4 = QCheckBox(self.groupBox_66)
        self.checkBox_4.setObjectName(u"checkBox_4")

        self.horizontalLayout.addWidget(self.checkBox_4)

        self.horizontalSpacer_20 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_20)


        self.gridLayout_66.addLayout(self.horizontalLayout, 2, 0, 1, 2)

        self.gridLayout_66.setColumnStretch(0, 1)
        self.gridLayout_66.setColumnStretch(1, 5)

        self.verticalLayout_42.addWidget(self.groupBox_66)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_42.addItem(self.verticalSpacer_7)

        self.groupBox_24 = QGroupBox(self.tab_10)
        self.groupBox_24.setObjectName(u"groupBox_24")
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_24)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.gridLayout_8 = QGridLayout()
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.radioButton_5 = QRadioButton(self.groupBox_24)
        self.radioButton_5.setObjectName(u"radioButton_5")
        self.radioButton_5.setChecked(True)

        self.gridLayout_8.addWidget(self.radioButton_5, 1, 0, 1, 1)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_44 = QLabel(self.groupBox_24)
        self.label_44.setObjectName(u"label_44")
        self.label_44.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_19.addWidget(self.label_44)

        self.spinBox_5 = QSpinBox(self.groupBox_24)
        self.spinBox_5.setObjectName(u"spinBox_5")
        self.spinBox_5.setMinimum(1)
        self.spinBox_5.setMaximum(9999)
        self.spinBox_5.setValue(5)

        self.horizontalLayout_19.addWidget(self.spinBox_5)


        self.gridLayout_8.addLayout(self.horizontalLayout_19, 1, 1, 1, 1)

        self.radioButton_3 = QRadioButton(self.groupBox_24)
        self.radioButton_3.setObjectName(u"radioButton_3")

        self.gridLayout_8.addWidget(self.radioButton_3, 0, 0, 1, 2)


        self.verticalLayout_18.addLayout(self.gridLayout_8)


        self.verticalLayout_42.addWidget(self.groupBox_24)

        self.pushButton_58 = QPushButton(self.tab_10)
        self.pushButton_58.setObjectName(u"pushButton_58")
        palette8 = QPalette()
        palette8.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette8.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette8.setBrush(QPalette.Active, QPalette.Text, brush)
        palette8.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette8.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette8.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush28 = QBrush(QColor(255, 255, 255, 128))
        brush28.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette8.setBrush(QPalette.Active, QPalette.PlaceholderText, brush28)
#endif
        palette8.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette8.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette8.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette8.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette8.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette8.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush29 = QBrush(QColor(255, 255, 255, 128))
        brush29.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette8.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush29)
#endif
        palette8.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette8.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette8.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette8.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette8.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette8.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush30 = QBrush(QColor(255, 255, 255, 128))
        brush30.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette8.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush30)
#endif
        self.pushButton_58.setPalette(palette8)
        self.pushButton_58.setFont(font2)
        self.pushButton_58.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_42.addWidget(self.pushButton_58)

        self.tabWidget.addTab(self.tab_10, "")
        self.tab_25 = QWidget()
        self.tab_25.setObjectName(u"tab_25")
        self.verticalLayout_16 = QVBoxLayout(self.tab_25)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.label_97 = QLabel(self.tab_25)
        self.label_97.setObjectName(u"label_97")
        sizePolicy.setHeightForWidth(self.label_97.sizePolicy().hasHeightForWidth())
        self.label_97.setSizePolicy(sizePolicy)
        self.label_97.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_97.setWordWrap(False)
        self.label_97.setMargin(0)
        self.label_97.setIndent(-1)
        self.label_97.setOpenExternalLinks(False)

        self.verticalLayout_16.addWidget(self.label_97)

        self.groupBox_19 = QGroupBox(self.tab_25)
        self.groupBox_19.setObjectName(u"groupBox_19")
        self.groupBox_19.setEnabled(True)
        self.gridLayout_64 = QGridLayout(self.groupBox_19)
        self.gridLayout_64.setObjectName(u"gridLayout_64")
        self.label_85 = QLabel(self.groupBox_19)
        self.label_85.setObjectName(u"label_85")
        self.label_85.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_64.addWidget(self.label_85, 0, 0, 1, 2)

        self.pushButton_16 = QPushButton(self.groupBox_19)
        self.pushButton_16.setObjectName(u"pushButton_16")

        self.gridLayout_64.addWidget(self.pushButton_16, 1, 0, 1, 2)


        self.verticalLayout_16.addWidget(self.groupBox_19)

        self.groupBox_60 = QGroupBox(self.tab_25)
        self.groupBox_60.setObjectName(u"groupBox_60")
        self.groupBox_60.setEnabled(True)
        self.verticalLayout_53 = QVBoxLayout(self.groupBox_60)
        self.verticalLayout_53.setObjectName(u"verticalLayout_53")
        self.gridLayout_63 = QGridLayout()
        self.gridLayout_63.setObjectName(u"gridLayout_63")
        self.comboBox_62 = QComboBox(self.groupBox_60)
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.addItem("")
        self.comboBox_62.setObjectName(u"comboBox_62")

        self.gridLayout_63.addWidget(self.comboBox_62, 0, 0, 1, 1)


        self.verticalLayout_53.addLayout(self.gridLayout_63)


        self.verticalLayout_16.addWidget(self.groupBox_60)

        self.groupBox_62 = QGroupBox(self.tab_25)
        self.groupBox_62.setObjectName(u"groupBox_62")
        self.gridLayout_65 = QGridLayout(self.groupBox_62)
        self.gridLayout_65.setObjectName(u"gridLayout_65")
        self.comboBox_63 = QComboBox(self.groupBox_62)
        self.comboBox_63.setObjectName(u"comboBox_63")

        self.gridLayout_65.addWidget(self.comboBox_63, 0, 1, 1, 1)

        self.label_161 = QLabel(self.groupBox_62)
        self.label_161.setObjectName(u"label_161")
        self.label_161.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_65.addWidget(self.label_161, 0, 0, 1, 1)

        self.pushButton_55 = QPushButton(self.groupBox_62)
        self.pushButton_55.setObjectName(u"pushButton_55")
        self.pushButton_55.setFont(font4)

        self.gridLayout_65.addWidget(self.pushButton_55, 2, 1, 1, 1)

        self.pushButton_53 = QPushButton(self.groupBox_62)
        self.pushButton_53.setObjectName(u"pushButton_53")

        self.gridLayout_65.addWidget(self.pushButton_53, 2, 0, 1, 1)

        self.gridLayout_65.setColumnStretch(0, 1)
        self.gridLayout_65.setColumnStretch(1, 1)

        self.verticalLayout_16.addWidget(self.groupBox_62)

        self.verticalSpacer_19 = QSpacerItem(20, 173, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_16.addItem(self.verticalSpacer_19)

        self.pushButton_17 = QPushButton(self.tab_25)
        self.pushButton_17.setObjectName(u"pushButton_17")
        self.pushButton_17.setEnabled(True)
        palette9 = QPalette()
        palette9.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette9.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette9.setBrush(QPalette.Active, QPalette.Text, brush)
        palette9.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette9.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette9.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush31 = QBrush(QColor(255, 255, 255, 128))
        brush31.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette9.setBrush(QPalette.Active, QPalette.PlaceholderText, brush31)
#endif
        palette9.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette9.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette9.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette9.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette9.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette9.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush32 = QBrush(QColor(255, 255, 255, 128))
        brush32.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette9.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush32)
#endif
        palette9.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette9.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette9.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette9.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette9.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette9.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush33 = QBrush(QColor(255, 255, 255, 128))
        brush33.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette9.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush33)
#endif
        self.pushButton_17.setPalette(palette9)
        self.pushButton_17.setFont(font2)
        self.pushButton_17.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_16.addWidget(self.pushButton_17)

        self.tabWidget.addTab(self.tab_25, "")
        self.tab_17 = QWidget()
        self.tab_17.setObjectName(u"tab_17")
        self.verticalLayout_52 = QVBoxLayout(self.tab_17)
        self.verticalLayout_52.setObjectName(u"verticalLayout_52")
        self.label_99 = QLabel(self.tab_17)
        self.label_99.setObjectName(u"label_99")
        sizePolicy.setHeightForWidth(self.label_99.sizePolicy().hasHeightForWidth())
        self.label_99.setSizePolicy(sizePolicy)
        self.label_99.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_99.setWordWrap(False)
        self.label_99.setMargin(0)
        self.label_99.setIndent(-1)
        self.label_99.setOpenExternalLinks(False)

        self.verticalLayout_52.addWidget(self.label_99)

        self.groupBox_68 = QGroupBox(self.tab_17)
        self.groupBox_68.setObjectName(u"groupBox_68")
        self.gridLayout_67 = QGridLayout(self.groupBox_68)
        self.gridLayout_67.setObjectName(u"gridLayout_67")
        self.label_19 = QLabel(self.groupBox_68)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_67.addWidget(self.label_19, 0, 0, 1, 1)

        self.comboBox_67 = QComboBox(self.groupBox_68)
        self.comboBox_67.addItem("")
        self.comboBox_67.addItem("")
        self.comboBox_67.setObjectName(u"comboBox_67")

        self.gridLayout_67.addWidget(self.comboBox_67, 0, 1, 1, 1)

        self.label_164 = QLabel(self.groupBox_68)
        self.label_164.setObjectName(u"label_164")
        self.label_164.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_67.addWidget(self.label_164, 1, 0, 1, 1)

        self.pushButton_60 = QPushButton(self.groupBox_68)
        self.pushButton_60.setObjectName(u"pushButton_60")

        self.gridLayout_67.addWidget(self.pushButton_60, 1, 1, 1, 1)


        self.verticalLayout_52.addWidget(self.groupBox_68)

        self.groupBox_69 = QGroupBox(self.tab_17)
        self.groupBox_69.setObjectName(u"groupBox_69")
        self.horizontalLayout_29 = QHBoxLayout(self.groupBox_69)
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_22)

        self.radioButton_9 = QRadioButton(self.groupBox_69)
        self.radioButton_9.setObjectName(u"radioButton_9")
        self.radioButton_9.setChecked(True)

        self.horizontalLayout_29.addWidget(self.radioButton_9)

        self.radioButton_8 = QRadioButton(self.groupBox_69)
        self.radioButton_8.setObjectName(u"radioButton_8")

        self.horizontalLayout_29.addWidget(self.radioButton_8)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_23)


        self.verticalLayout_52.addWidget(self.groupBox_69)

        self.groupBox_14 = QGroupBox(self.tab_17)
        self.groupBox_14.setObjectName(u"groupBox_14")
        self.verticalLayout_37 = QVBoxLayout(self.groupBox_14)
        self.verticalLayout_37.setObjectName(u"verticalLayout_37")
        self.gridLayout_27 = QGridLayout()
        self.gridLayout_27.setObjectName(u"gridLayout_27")
        self.label_76 = QLabel(self.groupBox_14)
        self.label_76.setObjectName(u"label_76")
        self.label_76.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_27.addWidget(self.label_76, 0, 0, 1, 1)

        self.comboBox_31 = QComboBox(self.groupBox_14)
        self.comboBox_31.setObjectName(u"comboBox_31")

        self.gridLayout_27.addWidget(self.comboBox_31, 0, 1, 1, 1)

        self.label_77 = QLabel(self.groupBox_14)
        self.label_77.setObjectName(u"label_77")
        self.label_77.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_27.addWidget(self.label_77, 1, 0, 1, 1)

        self.lineEdit_16 = QLineEdit(self.groupBox_14)
        self.lineEdit_16.setObjectName(u"lineEdit_16")

        self.gridLayout_27.addWidget(self.lineEdit_16, 1, 1, 1, 1)

        self.gridLayout_27.setColumnStretch(0, 1)
        self.gridLayout_27.setColumnStretch(1, 2)

        self.verticalLayout_37.addLayout(self.gridLayout_27)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.horizontalSpacer_24 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_24)

        self.pushButton_62 = QPushButton(self.groupBox_14)
        self.pushButton_62.setObjectName(u"pushButton_62")

        self.horizontalLayout_30.addWidget(self.pushButton_62)

        self.horizontalLayout_30.setStretch(0, 1)
        self.horizontalLayout_30.setStretch(1, 1)

        self.verticalLayout_37.addLayout(self.horizontalLayout_30)


        self.verticalLayout_52.addWidget(self.groupBox_14)

        self.verticalSpacer_14 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_52.addItem(self.verticalSpacer_14)

        self.pushButton_61 = QPushButton(self.tab_17)
        self.pushButton_61.setObjectName(u"pushButton_61")
        palette10 = QPalette()
        palette10.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette10.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette10.setBrush(QPalette.Active, QPalette.Text, brush)
        palette10.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette10.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette10.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush34 = QBrush(QColor(255, 255, 255, 128))
        brush34.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette10.setBrush(QPalette.Active, QPalette.PlaceholderText, brush34)
#endif
        palette10.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette10.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette10.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette10.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette10.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette10.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush35 = QBrush(QColor(255, 255, 255, 128))
        brush35.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette10.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush35)
#endif
        palette10.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette10.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette10.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette10.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette10.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette10.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush36 = QBrush(QColor(255, 255, 255, 128))
        brush36.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette10.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush36)
#endif
        self.pushButton_61.setPalette(palette10)
        self.pushButton_61.setFont(font2)
        self.pushButton_61.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_52.addWidget(self.pushButton_61)

        self.tabWidget.addTab(self.tab_17, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_66 = QVBoxLayout(self.tab_2)
        self.verticalLayout_66.setObjectName(u"verticalLayout_66")
        self.groupBox_32 = QGroupBox(self.tab_2)
        self.groupBox_32.setObjectName(u"groupBox_32")
        self.groupBox_32.setCheckable(True)
        self.verticalLayout_65 = QVBoxLayout(self.groupBox_32)
        self.verticalLayout_65.setObjectName(u"verticalLayout_65")
        self.gridLayout_38 = QGridLayout()
        self.gridLayout_38.setObjectName(u"gridLayout_38")
        self.label_116 = QLabel(self.groupBox_32)
        self.label_116.setObjectName(u"label_116")

        self.gridLayout_38.addWidget(self.label_116, 1, 2, 1, 1)

        self.spinBox_24 = QSpinBox(self.groupBox_32)
        self.spinBox_24.setObjectName(u"spinBox_24")
        self.spinBox_24.setMaximum(9999)

        self.gridLayout_38.addWidget(self.spinBox_24, 1, 3, 1, 1)

        self.label_112 = QLabel(self.groupBox_32)
        self.label_112.setObjectName(u"label_112")

        self.gridLayout_38.addWidget(self.label_112, 0, 0, 1, 1)

        self.spinBox_21 = QSpinBox(self.groupBox_32)
        self.spinBox_21.setObjectName(u"spinBox_21")
        self.spinBox_21.setMinimum(37)
        self.spinBox_21.setMaximum(32767)
        self.spinBox_21.setValue(1000)

        self.gridLayout_38.addWidget(self.spinBox_21, 0, 1, 1, 1)

        self.label_114 = QLabel(self.groupBox_32)
        self.label_114.setObjectName(u"label_114")

        self.gridLayout_38.addWidget(self.label_114, 0, 2, 1, 1)

        self.spinBox_23 = QSpinBox(self.groupBox_32)
        self.spinBox_23.setObjectName(u"spinBox_23")
        self.spinBox_23.setMinimum(1)
        self.spinBox_23.setMaximum(99999)
        self.spinBox_23.setValue(500)

        self.gridLayout_38.addWidget(self.spinBox_23, 0, 3, 1, 1)

        self.label_113 = QLabel(self.groupBox_32)
        self.label_113.setObjectName(u"label_113")

        self.gridLayout_38.addWidget(self.label_113, 1, 0, 1, 1)

        self.spinBox_22 = QSpinBox(self.groupBox_32)
        self.spinBox_22.setObjectName(u"spinBox_22")
        self.spinBox_22.setMinimum(1)
        self.spinBox_22.setMaximum(9999)

        self.gridLayout_38.addWidget(self.spinBox_22, 1, 1, 1, 1)


        self.verticalLayout_65.addLayout(self.gridLayout_38)


        self.verticalLayout_66.addWidget(self.groupBox_32)

        self.groupBox_33 = QGroupBox(self.tab_2)
        self.groupBox_33.setObjectName(u"groupBox_33")
        self.groupBox_33.setEnabled(True)
        self.groupBox_33.setCheckable(True)
        self.groupBox_33.setChecked(False)
        self.gridLayout_39 = QGridLayout(self.groupBox_33)
        self.gridLayout_39.setObjectName(u"gridLayout_39")
        self.label_115 = QLabel(self.groupBox_33)
        self.label_115.setObjectName(u"label_115")

        self.gridLayout_39.addWidget(self.label_115, 0, 0, 1, 1)

        self.comboBox_7 = QComboBox(self.groupBox_33)
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.setObjectName(u"comboBox_7")

        self.gridLayout_39.addWidget(self.comboBox_7, 0, 1, 1, 1)


        self.verticalLayout_66.addWidget(self.groupBox_33)

        self.groupBox_34 = QGroupBox(self.tab_2)
        self.groupBox_34.setObjectName(u"groupBox_34")
        self.groupBox_34.setEnabled(True)
        self.groupBox_34.setCheckable(True)
        self.groupBox_34.setChecked(False)
        self.gridLayout_40 = QGridLayout(self.groupBox_34)
        self.gridLayout_40.setObjectName(u"gridLayout_40")
        self.textEdit_4 = QTextEdit(self.groupBox_34)
        self.textEdit_4.setObjectName(u"textEdit_4")

        self.gridLayout_40.addWidget(self.textEdit_4, 0, 0, 1, 2)

        self.horizontalLayout_28 = QHBoxLayout()
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.label_117 = QLabel(self.groupBox_34)
        self.label_117.setObjectName(u"label_117")

        self.horizontalLayout_28.addWidget(self.label_117)

        self.horizontalSlider = QSlider(self.groupBox_34)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setMinimum(100)
        self.horizontalSlider.setMaximum(999)
        self.horizontalSlider.setValue(200)
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_28.addWidget(self.horizontalSlider)

        self.label_118 = QLabel(self.groupBox_34)
        self.label_118.setObjectName(u"label_118")

        self.horizontalLayout_28.addWidget(self.label_118)


        self.gridLayout_40.addLayout(self.horizontalLayout_28, 1, 0, 1, 1)

        self.pushButton_32 = QPushButton(self.groupBox_34)
        self.pushButton_32.setObjectName(u"pushButton_32")
        self.pushButton_32.setFont(font4)

        self.gridLayout_40.addWidget(self.pushButton_32, 1, 1, 1, 1)

        self.gridLayout_40.setColumnStretch(0, 1)
        self.gridLayout_40.setColumnStretch(1, 1)

        self.verticalLayout_66.addWidget(self.groupBox_34)

        self.verticalSpacer_17 = QSpacerItem(20, 13, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_66.addItem(self.verticalSpacer_17)

        self.pushButton_24 = QPushButton(self.tab_2)
        self.pushButton_24.setObjectName(u"pushButton_24")
        palette11 = QPalette()
        palette11.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette11.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette11.setBrush(QPalette.Active, QPalette.Text, brush)
        palette11.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette11.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette11.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush37 = QBrush(QColor(255, 255, 255, 128))
        brush37.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette11.setBrush(QPalette.Active, QPalette.PlaceholderText, brush37)
#endif
        palette11.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette11.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette11.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette11.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette11.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette11.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush38 = QBrush(QColor(255, 255, 255, 128))
        brush38.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette11.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush38)
#endif
        palette11.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette11.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette11.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette11.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette11.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette11.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush39 = QBrush(QColor(255, 255, 255, 128))
        brush39.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette11.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush39)
#endif
        self.pushButton_24.setPalette(palette11)
        self.pushButton_24.setFont(font2)
        self.pushButton_24.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_66.addWidget(self.pushButton_24)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_28 = QWidget()
        self.tab_28.setObjectName(u"tab_28")
        self.verticalLayout_68 = QVBoxLayout(self.tab_28)
        self.verticalLayout_68.setObjectName(u"verticalLayout_68")
        self.groupBox_35 = QGroupBox(self.tab_28)
        self.groupBox_35.setObjectName(u"groupBox_35")
        self.verticalLayout_67 = QVBoxLayout(self.groupBox_35)
        self.verticalLayout_67.setObjectName(u"verticalLayout_67")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_119 = QLabel(self.groupBox_35)
        self.label_119.setObjectName(u"label_119")
        self.label_119.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_119)

        self.lineEdit_2 = QLineEdit(self.groupBox_35)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_6.addWidget(self.lineEdit_2)


        self.verticalLayout_67.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_120 = QLabel(self.groupBox_35)
        self.label_120.setObjectName(u"label_120")
        self.label_120.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_10.addWidget(self.label_120)

        self.lineEdit_6 = QLineEdit(self.groupBox_35)
        self.lineEdit_6.setObjectName(u"lineEdit_6")
        self.lineEdit_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_10.addWidget(self.lineEdit_6)


        self.verticalLayout_67.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_121 = QLabel(self.groupBox_35)
        self.label_121.setObjectName(u"label_121")
        self.label_121.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_121)

        self.spinBox_25 = QSpinBox(self.groupBox_35)
        self.spinBox_25.setObjectName(u"spinBox_25")
        self.spinBox_25.setMinimum(1)
        self.spinBox_25.setMaximum(9999)
        self.spinBox_25.setValue(10)

        self.horizontalLayout_3.addWidget(self.spinBox_25)

        self.label_122 = QLabel(self.groupBox_35)
        self.label_122.setObjectName(u"label_122")
        self.label_122.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_3.addWidget(self.label_122)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)


        self.verticalLayout_67.addLayout(self.horizontalLayout_3)


        self.verticalLayout_68.addWidget(self.groupBox_35)

        self.verticalSpacer_18 = QSpacerItem(20, 306, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_68.addItem(self.verticalSpacer_18)

        self.pushButton_25 = QPushButton(self.tab_28)
        self.pushButton_25.setObjectName(u"pushButton_25")
        palette12 = QPalette()
        palette12.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette12.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette12.setBrush(QPalette.Active, QPalette.Text, brush)
        palette12.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette12.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette12.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush40 = QBrush(QColor(255, 255, 255, 128))
        brush40.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette12.setBrush(QPalette.Active, QPalette.PlaceholderText, brush40)
#endif
        palette12.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette12.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette12.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette12.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette12.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette12.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush41 = QBrush(QColor(255, 255, 255, 128))
        brush41.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette12.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush41)
#endif
        palette12.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette12.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette12.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette12.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette12.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette12.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush42 = QBrush(QColor(255, 255, 255, 128))
        brush42.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette12.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush42)
#endif
        self.pushButton_25.setPalette(palette12)
        self.pushButton_25.setFont(font2)
        self.pushButton_25.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_68.addWidget(self.pushButton_25)

        self.tabWidget.addTab(self.tab_28, "")
        self.tab_32 = QWidget()
        self.tab_32.setObjectName(u"tab_32")
        self.verticalLayout_74 = QVBoxLayout(self.tab_32)
        self.verticalLayout_74.setObjectName(u"verticalLayout_74")
        self.groupBox_39 = QGroupBox(self.tab_32)
        self.groupBox_39.setObjectName(u"groupBox_39")
        self.gridLayout_44 = QGridLayout(self.groupBox_39)
        self.gridLayout_44.setObjectName(u"gridLayout_44")
        self.label_130 = QLabel(self.groupBox_39)
        self.label_130.setObjectName(u"label_130")
        self.label_130.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_44.addWidget(self.label_130, 1, 0, 1, 1)

        self.comboBox_40 = QComboBox(self.groupBox_39)
        self.comboBox_40.addItem("")
        self.comboBox_40.addItem("")
        self.comboBox_40.addItem("")
        self.comboBox_40.addItem("")
        self.comboBox_40.setObjectName(u"comboBox_40")

        self.gridLayout_44.addWidget(self.comboBox_40, 1, 1, 1, 1)

        self.lineEdit_21 = QLineEdit(self.groupBox_39)
        self.lineEdit_21.setObjectName(u"lineEdit_21")

        self.gridLayout_44.addWidget(self.lineEdit_21, 0, 1, 1, 1)

        self.label_129 = QLabel(self.groupBox_39)
        self.label_129.setObjectName(u"label_129")
        self.label_129.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_44.addWidget(self.label_129, 0, 0, 1, 1)

        self.checkBox_5 = QCheckBox(self.groupBox_39)
        self.checkBox_5.setObjectName(u"checkBox_5")
        self.checkBox_5.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.checkBox_5.setChecked(False)

        self.gridLayout_44.addWidget(self.checkBox_5, 2, 1, 1, 1)

        self.gridLayout_44.setColumnStretch(0, 1)
        self.gridLayout_44.setColumnStretch(1, 2)

        self.verticalLayout_74.addWidget(self.groupBox_39)

        self.verticalSpacer_25 = QSpacerItem(20, 314, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_74.addItem(self.verticalSpacer_25)

        self.pushButton_27 = QPushButton(self.tab_32)
        self.pushButton_27.setObjectName(u"pushButton_27")
        palette13 = QPalette()
        palette13.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette13.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette13.setBrush(QPalette.Active, QPalette.Text, brush)
        palette13.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette13.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette13.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush43 = QBrush(QColor(255, 255, 255, 128))
        brush43.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette13.setBrush(QPalette.Active, QPalette.PlaceholderText, brush43)
#endif
        palette13.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette13.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette13.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette13.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette13.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette13.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush44 = QBrush(QColor(255, 255, 255, 128))
        brush44.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette13.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush44)
#endif
        palette13.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette13.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette13.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette13.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette13.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette13.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush45 = QBrush(QColor(255, 255, 255, 128))
        brush45.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette13.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush45)
#endif
        self.pushButton_27.setPalette(palette13)
        self.pushButton_27.setFont(font2)
        self.pushButton_27.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_74.addWidget(self.pushButton_27)

        self.tabWidget.addTab(self.tab_32, "")
        self.tab_29 = QWidget()
        self.tab_29.setObjectName(u"tab_29")
        self.verticalLayout_70 = QVBoxLayout(self.tab_29)
        self.verticalLayout_70.setObjectName(u"verticalLayout_70")
        self.groupBox_36 = QGroupBox(self.tab_29)
        self.groupBox_36.setObjectName(u"groupBox_36")
        self.verticalLayout_69 = QVBoxLayout(self.groupBox_36)
        self.verticalLayout_69.setObjectName(u"verticalLayout_69")
        self.gridLayout_41 = QGridLayout()
        self.gridLayout_41.setObjectName(u"gridLayout_41")
        self.label_123 = QLabel(self.groupBox_36)
        self.label_123.setObjectName(u"label_123")
        self.label_123.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_41.addWidget(self.label_123, 0, 0, 1, 1)

        self.lineEdit_8 = QLineEdit(self.groupBox_36)
        self.lineEdit_8.setObjectName(u"lineEdit_8")
        self.lineEdit_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_41.addWidget(self.lineEdit_8, 0, 1, 1, 1)

        self.label_125 = QLabel(self.groupBox_36)
        self.label_125.setObjectName(u"label_125")
        self.label_125.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_41.addWidget(self.label_125, 0, 2, 1, 1)

        self.comboBox_36 = QComboBox(self.groupBox_36)
        self.comboBox_36.addItem("")
        self.comboBox_36.addItem("")
        self.comboBox_36.addItem("")
        self.comboBox_36.addItem("")
        self.comboBox_36.setObjectName(u"comboBox_36")

        self.gridLayout_41.addWidget(self.comboBox_36, 0, 3, 1, 1)

        self.label_124 = QLabel(self.groupBox_36)
        self.label_124.setObjectName(u"label_124")
        self.label_124.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_41.addWidget(self.label_124, 1, 0, 1, 1)

        self.lineEdit_20 = QLineEdit(self.groupBox_36)
        self.lineEdit_20.setObjectName(u"lineEdit_20")
        self.lineEdit_20.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_41.addWidget(self.lineEdit_20, 1, 1, 1, 3)

        self.gridLayout_41.setColumnStretch(0, 1)
        self.gridLayout_41.setColumnStretch(1, 1)
        self.gridLayout_41.setColumnStretch(2, 1)
        self.gridLayout_41.setColumnStretch(3, 1)

        self.verticalLayout_69.addLayout(self.gridLayout_41)


        self.verticalLayout_70.addWidget(self.groupBox_36)

        self.verticalSpacer_22 = QSpacerItem(20, 343, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_70.addItem(self.verticalSpacer_22)

        self.pushButton_26 = QPushButton(self.tab_29)
        self.pushButton_26.setObjectName(u"pushButton_26")
        palette14 = QPalette()
        palette14.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette14.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette14.setBrush(QPalette.Active, QPalette.Text, brush)
        palette14.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette14.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette14.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush46 = QBrush(QColor(255, 255, 255, 128))
        brush46.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette14.setBrush(QPalette.Active, QPalette.PlaceholderText, brush46)
#endif
        palette14.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette14.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette14.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette14.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette14.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette14.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush47 = QBrush(QColor(255, 255, 255, 128))
        brush47.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette14.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush47)
#endif
        palette14.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette14.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette14.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette14.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette14.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette14.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush48 = QBrush(QColor(255, 255, 255, 128))
        brush48.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette14.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush48)
#endif
        self.pushButton_26.setPalette(palette14)
        self.pushButton_26.setFont(font2)
        self.pushButton_26.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    font-size: 14px; /* \u8bbe\u7f6e\u5b57\u4f53\u5927\u5c0f\uff0c\u53ef\u4ee5\u6839\u636e\u9700\u8981\u8c03\u6574 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_70.addWidget(self.pushButton_26)

        self.tabWidget.addTab(self.tab_29, "")
        self.tab_31 = QWidget()
        self.tab_31.setObjectName(u"tab_31")
        self.verticalLayout_72 = QVBoxLayout(self.tab_31)
        self.verticalLayout_72.setObjectName(u"verticalLayout_72")
        self.groupBox_38 = QGroupBox(self.tab_31)
        self.groupBox_38.setObjectName(u"groupBox_38")
        self.gridLayout_43 = QGridLayout(self.groupBox_38)
        self.gridLayout_43.setObjectName(u"gridLayout_43")
        self.label_128 = QLabel(self.groupBox_38)
        self.label_128.setObjectName(u"label_128")
        self.label_128.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_43.addWidget(self.label_128, 0, 0, 1, 1)

        self.comboBox_39 = QComboBox(self.groupBox_38)
        self.comboBox_39.addItem("")
        self.comboBox_39.setObjectName(u"comboBox_39")

        self.gridLayout_43.addWidget(self.comboBox_39, 0, 1, 1, 1)

        self.gridLayout_43.setColumnStretch(0, 1)
        self.gridLayout_43.setColumnStretch(1, 1)

        self.verticalLayout_72.addWidget(self.groupBox_38)

        self.verticalSpacer_24 = QSpacerItem(20, 413, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_72.addItem(self.verticalSpacer_24)

        self.tabWidget.addTab(self.tab_31, "")
        self.tab_34 = QWidget()
        self.tab_34.setObjectName(u"tab_34")
        self.verticalLayout_48 = QVBoxLayout(self.tab_34)
        self.verticalLayout_48.setObjectName(u"verticalLayout_48")
        self.groupBox_42 = QGroupBox(self.tab_34)
        self.groupBox_42.setObjectName(u"groupBox_42")
        self.horizontalLayout_13 = QHBoxLayout(self.groupBox_42)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_134 = QLabel(self.groupBox_42)
        self.label_134.setObjectName(u"label_134")
        self.label_134.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.label_134)

        self.comboBox_43 = QComboBox(self.groupBox_42)
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.addItem("")
        self.comboBox_43.setObjectName(u"comboBox_43")

        self.horizontalLayout_13.addWidget(self.comboBox_43)


        self.verticalLayout_48.addWidget(self.groupBox_42)

        self.groupBox_43 = QGroupBox(self.tab_34)
        self.groupBox_43.setObjectName(u"groupBox_43")
        self.gridLayout_49 = QGridLayout(self.groupBox_43)
        self.gridLayout_49.setObjectName(u"gridLayout_49")
        self.comboBox_44 = QComboBox(self.groupBox_43)
        self.comboBox_44.setObjectName(u"comboBox_44")

        self.gridLayout_49.addWidget(self.comboBox_44, 0, 1, 1, 1)

        self.label_135 = QLabel(self.groupBox_43)
        self.label_135.setObjectName(u"label_135")
        self.label_135.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_49.addWidget(self.label_135, 0, 0, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(84, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_49.addItem(self.horizontalSpacer_6, 2, 0, 1, 1)

        self.pushButton_33 = QPushButton(self.groupBox_43)
        self.pushButton_33.setObjectName(u"pushButton_33")
        self.pushButton_33.setFont(font4)

        self.gridLayout_49.addWidget(self.pushButton_33, 2, 1, 1, 1)

        self.gridLayout_49.setColumnStretch(0, 1)
        self.gridLayout_49.setColumnStretch(1, 1)

        self.verticalLayout_48.addWidget(self.groupBox_43)

        self.verticalSpacer_28 = QSpacerItem(20, 264, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_48.addItem(self.verticalSpacer_28)

        self.pushButton_34 = QPushButton(self.tab_34)
        self.pushButton_34.setObjectName(u"pushButton_34")
        palette15 = QPalette()
        palette15.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette15.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette15.setBrush(QPalette.Active, QPalette.Text, brush)
        palette15.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette15.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette15.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush49 = QBrush(QColor(255, 255, 255, 128))
        brush49.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette15.setBrush(QPalette.Active, QPalette.PlaceholderText, brush49)
#endif
        palette15.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette15.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette15.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette15.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette15.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette15.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush50 = QBrush(QColor(255, 255, 255, 128))
        brush50.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette15.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush50)
#endif
        palette15.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette15.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette15.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette15.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette15.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette15.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush51 = QBrush(QColor(255, 255, 255, 128))
        brush51.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette15.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush51)
#endif
        self.pushButton_34.setPalette(palette15)
        self.pushButton_34.setFont(font2)
        self.pushButton_34.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_48.addWidget(self.pushButton_34)

        self.tabWidget.addTab(self.tab_34, "")
        self.tab_41 = QWidget()
        self.tab_41.setObjectName(u"tab_41")
        self.verticalLayout_13 = QVBoxLayout(self.tab_41)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.label_159 = QLabel(self.tab_41)
        self.label_159.setObjectName(u"label_159")
        sizePolicy.setHeightForWidth(self.label_159.sizePolicy().hasHeightForWidth())
        self.label_159.setSizePolicy(sizePolicy)
        self.label_159.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_159.setWordWrap(False)
        self.label_159.setMargin(0)
        self.label_159.setIndent(-1)
        self.label_159.setOpenExternalLinks(False)

        self.verticalLayout_13.addWidget(self.label_159)

        self.groupBox_58 = QGroupBox(self.tab_41)
        self.groupBox_58.setObjectName(u"groupBox_58")
        self.gridLayout_61 = QGridLayout(self.groupBox_58)
        self.gridLayout_61.setObjectName(u"gridLayout_61")
        self.comboBox_60 = QComboBox(self.groupBox_58)
        self.comboBox_60.setObjectName(u"comboBox_60")

        self.gridLayout_61.addWidget(self.comboBox_60, 0, 1, 1, 1)

        self.label_156 = QLabel(self.groupBox_58)
        self.label_156.setObjectName(u"label_156")
        self.label_156.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_61.addWidget(self.label_156, 0, 0, 1, 1)

        self.horizontalSpacer_10 = QSpacerItem(84, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_61.addItem(self.horizontalSpacer_10, 2, 0, 1, 1)

        self.pushButton_51 = QPushButton(self.groupBox_58)
        self.pushButton_51.setObjectName(u"pushButton_51")
        self.pushButton_51.setFont(font4)

        self.gridLayout_61.addWidget(self.pushButton_51, 2, 1, 1, 1)

        self.gridLayout_61.setColumnStretch(0, 1)
        self.gridLayout_61.setColumnStretch(1, 1)

        self.verticalLayout_13.addWidget(self.groupBox_58)

        self.verticalSpacer_35 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_13.addItem(self.verticalSpacer_35)

        self.tabWidget.addTab(self.tab_41, "")
        self.tab_33 = QWidget()
        self.tab_33.setObjectName(u"tab_33")
        self.verticalLayout_75 = QVBoxLayout(self.tab_33)
        self.verticalLayout_75.setObjectName(u"verticalLayout_75")
        self.groupBox_40 = QGroupBox(self.tab_33)
        self.groupBox_40.setObjectName(u"groupBox_40")
        self.gridLayout_45 = QGridLayout(self.groupBox_40)
        self.gridLayout_45.setObjectName(u"gridLayout_45")
        self.label_131 = QLabel(self.groupBox_40)
        self.label_131.setObjectName(u"label_131")
        self.label_131.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_45.addWidget(self.label_131, 0, 0, 1, 1)

        self.keySequenceEdit_2 = QKeySequenceEdit(self.groupBox_40)
        self.keySequenceEdit_2.setObjectName(u"keySequenceEdit_2")

        self.gridLayout_45.addWidget(self.keySequenceEdit_2, 0, 1, 1, 1)

        self.gridLayout_45.setColumnStretch(0, 1)
        self.gridLayout_45.setColumnStretch(1, 1)

        self.verticalLayout_75.addWidget(self.groupBox_40)

        self.verticalSpacer_26 = QSpacerItem(20, 272, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_75.addItem(self.verticalSpacer_26)

        self.tabWidget.addTab(self.tab_33, "")
        self.tab_35 = QWidget()
        self.tab_35.setObjectName(u"tab_35")
        self.verticalLayout_77 = QVBoxLayout(self.tab_35)
        self.verticalLayout_77.setObjectName(u"verticalLayout_77")
        self.groupBox_47 = QGroupBox(self.tab_35)
        self.groupBox_47.setObjectName(u"groupBox_47")
        self.gridLayout_52 = QGridLayout(self.groupBox_47)
        self.gridLayout_52.setObjectName(u"gridLayout_52")
        self.label_141 = QLabel(self.groupBox_47)
        self.label_141.setObjectName(u"label_141")
        self.label_141.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_52.addWidget(self.label_141, 0, 0, 1, 1)

        self.lineEdit_24 = QLineEdit(self.groupBox_47)
        self.lineEdit_24.setObjectName(u"lineEdit_24")

        self.gridLayout_52.addWidget(self.lineEdit_24, 0, 1, 1, 1)

        self.label_142 = QLabel(self.groupBox_47)
        self.label_142.setObjectName(u"label_142")
        self.label_142.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_52.addWidget(self.label_142, 1, 0, 1, 1)

        self.lineEdit_25 = QLineEdit(self.groupBox_47)
        self.lineEdit_25.setObjectName(u"lineEdit_25")

        self.gridLayout_52.addWidget(self.lineEdit_25, 1, 1, 1, 1)

        self.gridLayout_52.setColumnStretch(0, 1)
        self.gridLayout_52.setColumnStretch(1, 1)

        self.verticalLayout_77.addWidget(self.groupBox_47)

        self.groupBox_46 = QGroupBox(self.tab_35)
        self.groupBox_46.setObjectName(u"groupBox_46")
        self.gridLayout_51 = QGridLayout(self.groupBox_46)
        self.gridLayout_51.setObjectName(u"gridLayout_51")
        self.comboBox_48 = QComboBox(self.groupBox_46)
        self.comboBox_48.setObjectName(u"comboBox_48")

        self.gridLayout_51.addWidget(self.comboBox_48, 0, 1, 1, 1)

        self.label_140 = QLabel(self.groupBox_46)
        self.label_140.setObjectName(u"label_140")
        self.label_140.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_51.addWidget(self.label_140, 0, 0, 1, 1)

        self.horizontalSpacer_8 = QSpacerItem(84, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_51.addItem(self.horizontalSpacer_8, 2, 0, 1, 1)

        self.pushButton_37 = QPushButton(self.groupBox_46)
        self.pushButton_37.setObjectName(u"pushButton_37")
        self.pushButton_37.setFont(font4)

        self.gridLayout_51.addWidget(self.pushButton_37, 2, 1, 1, 1)

        self.gridLayout_51.setColumnStretch(0, 1)
        self.gridLayout_51.setColumnStretch(1, 1)

        self.verticalLayout_77.addWidget(self.groupBox_46)

        self.verticalSpacer_30 = QSpacerItem(20, 266, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_77.addItem(self.verticalSpacer_30)

        self.tabWidget.addTab(self.tab_35, "")
        self.tab_45 = QWidget()
        self.tab_45.setObjectName(u"tab_45")
        self.verticalLayout_64 = QVBoxLayout(self.tab_45)
        self.verticalLayout_64.setObjectName(u"verticalLayout_64")
        self.groupBox_76 = QGroupBox(self.tab_45)
        self.groupBox_76.setObjectName(u"groupBox_76")
        self.gridLayout_72 = QGridLayout(self.groupBox_76)
        self.gridLayout_72.setObjectName(u"gridLayout_72")
        self.comboBox_73 = QComboBox(self.groupBox_76)
        self.comboBox_73.setObjectName(u"comboBox_73")

        self.gridLayout_72.addWidget(self.comboBox_73, 0, 1, 1, 1)

        self.label_175 = QLabel(self.groupBox_76)
        self.label_175.setObjectName(u"label_175")
        self.label_175.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_72.addWidget(self.label_175, 0, 0, 1, 1)

        self.horizontalSpacer_25 = QSpacerItem(84, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_72.addItem(self.horizontalSpacer_25, 2, 0, 1, 1)

        self.pushButton_74 = QPushButton(self.groupBox_76)
        self.pushButton_74.setObjectName(u"pushButton_74")
        self.pushButton_74.setFont(font4)

        self.gridLayout_72.addWidget(self.pushButton_74, 2, 1, 1, 1)

        self.gridLayout_72.setColumnStretch(0, 1)
        self.gridLayout_72.setColumnStretch(1, 1)

        self.verticalLayout_64.addWidget(self.groupBox_76)

        self.verticalSpacer_40 = QSpacerItem(20, 396, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_64.addItem(self.verticalSpacer_40)

        self.pushButton_75 = QPushButton(self.tab_45)
        self.pushButton_75.setObjectName(u"pushButton_75")
        palette16 = QPalette()
        palette16.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette16.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette16.setBrush(QPalette.Active, QPalette.Text, brush)
        palette16.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette16.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette16.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush52 = QBrush(QColor(255, 255, 255, 128))
        brush52.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette16.setBrush(QPalette.Active, QPalette.PlaceholderText, brush52)
#endif
        palette16.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette16.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette16.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette16.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette16.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette16.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush53 = QBrush(QColor(255, 255, 255, 128))
        brush53.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette16.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush53)
#endif
        palette16.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette16.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette16.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette16.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette16.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette16.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush54 = QBrush(QColor(255, 255, 255, 128))
        brush54.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette16.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush54)
#endif
        self.pushButton_75.setPalette(palette16)
        self.pushButton_75.setFont(font2)
        self.pushButton_75.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_64.addWidget(self.pushButton_75)

        self.tabWidget.addTab(self.tab_45, "")
        self.tab_37 = QWidget()
        self.tab_37.setObjectName(u"tab_37")
        self.verticalLayout_81 = QVBoxLayout(self.tab_37)
        self.verticalLayout_81.setObjectName(u"verticalLayout_81")
        self.groupBox_51 = QGroupBox(self.tab_37)
        self.groupBox_51.setObjectName(u"groupBox_51")
        self.verticalLayout_80 = QVBoxLayout(self.groupBox_51)
        self.verticalLayout_80.setObjectName(u"verticalLayout_80")
        self.gridLayout_55 = QGridLayout()
        self.gridLayout_55.setObjectName(u"gridLayout_55")
        self.textEdit_5 = QTextEdit(self.groupBox_51)
        self.textEdit_5.setObjectName(u"textEdit_5")
        font6 = QFont()
        font6.setFamilies([u"Cascadia Code"])
        font6.setPointSize(10)
        font6.setBold(False)
        self.textEdit_5.setFont(font6)

        self.gridLayout_55.addWidget(self.textEdit_5, 0, 0, 1, 3)

        self.pushButton_41 = QPushButton(self.groupBox_51)
        self.pushButton_41.setObjectName(u"pushButton_41")
        self.pushButton_41.setFont(font4)

        self.gridLayout_55.addWidget(self.pushButton_41, 1, 0, 1, 1)

        self.pushButton_39 = QPushButton(self.groupBox_51)
        self.pushButton_39.setObjectName(u"pushButton_39")
        self.pushButton_39.setFont(font4)

        self.gridLayout_55.addWidget(self.pushButton_39, 1, 1, 1, 1)

        self.toolButton_4 = QToolButton(self.groupBox_51)
        self.toolButton_4.setObjectName(u"toolButton_4")
        icon3 = QIcon()
        icon3.addFile(u":/\u6309\u94ae\u56fe\u6807/Window/res/\u5e2e\u52a9.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolButton_4.setIcon(icon3)

        self.gridLayout_55.addWidget(self.toolButton_4, 1, 2, 1, 1)

        self.gridLayout_55.setColumnStretch(0, 1)
        self.gridLayout_55.setColumnStretch(1, 1)

        self.verticalLayout_80.addLayout(self.gridLayout_55)


        self.verticalLayout_81.addWidget(self.groupBox_51)

        self.groupBox_50 = QGroupBox(self.tab_37)
        self.groupBox_50.setObjectName(u"groupBox_50")
        self.gridLayout_54 = QGridLayout(self.groupBox_50)
        self.gridLayout_54.setObjectName(u"gridLayout_54")
        self.label_147 = QLabel(self.groupBox_50)
        self.label_147.setObjectName(u"label_147")
        self.label_147.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_54.addWidget(self.label_147, 0, 0, 1, 1)

        self.lineEdit_26 = QLineEdit(self.groupBox_50)
        self.lineEdit_26.setObjectName(u"lineEdit_26")

        self.gridLayout_54.addWidget(self.lineEdit_26, 0, 1, 1, 1)

        self.label_148 = QLabel(self.groupBox_50)
        self.label_148.setObjectName(u"label_148")
        self.label_148.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_54.addWidget(self.label_148, 1, 0, 1, 1)

        self.comboBox_56 = QComboBox(self.groupBox_50)
        self.comboBox_56.setObjectName(u"comboBox_56")

        self.gridLayout_54.addWidget(self.comboBox_56, 1, 1, 1, 1)

        self.gridLayout_54.setColumnStretch(0, 1)
        self.gridLayout_54.setColumnStretch(1, 1)

        self.verticalLayout_81.addWidget(self.groupBox_50)

        self.pushButton_40 = QPushButton(self.tab_37)
        self.pushButton_40.setObjectName(u"pushButton_40")
        palette17 = QPalette()
        palette17.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette17.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette17.setBrush(QPalette.Active, QPalette.Text, brush)
        palette17.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette17.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette17.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush55 = QBrush(QColor(255, 255, 255, 128))
        brush55.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette17.setBrush(QPalette.Active, QPalette.PlaceholderText, brush55)
#endif
        palette17.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette17.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette17.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette17.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette17.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette17.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush56 = QBrush(QColor(255, 255, 255, 128))
        brush56.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette17.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush56)
#endif
        palette17.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette17.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette17.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette17.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette17.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette17.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush57 = QBrush(QColor(255, 255, 255, 128))
        brush57.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette17.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush57)
#endif
        self.pushButton_40.setPalette(palette17)
        self.pushButton_40.setFont(font2)
        self.pushButton_40.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_81.addWidget(self.pushButton_40)

        self.tabWidget.addTab(self.tab_37, "")
        self.tab_44 = QWidget()
        self.tab_44.setObjectName(u"tab_44")
        self.verticalLayout_62 = QVBoxLayout(self.tab_44)
        self.verticalLayout_62.setObjectName(u"verticalLayout_62")
        self.groupBox_72 = QGroupBox(self.tab_44)
        self.groupBox_72.setObjectName(u"groupBox_72")
        self.verticalLayout_83 = QVBoxLayout(self.groupBox_72)
        self.verticalLayout_83.setObjectName(u"verticalLayout_83")
        self.gridLayout_69 = QGridLayout()
        self.gridLayout_69.setObjectName(u"gridLayout_69")
        self.textEdit_7 = QTextEdit(self.groupBox_72)
        self.textEdit_7.setObjectName(u"textEdit_7")
        self.textEdit_7.setFont(font6)

        self.gridLayout_69.addWidget(self.textEdit_7, 0, 0, 1, 2)

        self.pushButton_70 = QPushButton(self.groupBox_72)
        self.pushButton_70.setObjectName(u"pushButton_70")
        self.pushButton_70.setFont(font4)

        self.gridLayout_69.addWidget(self.pushButton_70, 1, 1, 1, 1)

        self.pushButton_71 = QPushButton(self.groupBox_72)
        self.pushButton_71.setObjectName(u"pushButton_71")
        self.pushButton_71.setFont(font4)

        self.gridLayout_69.addWidget(self.pushButton_71, 1, 0, 1, 1)

        self.gridLayout_69.setColumnStretch(0, 1)
        self.gridLayout_69.setColumnStretch(1, 1)

        self.verticalLayout_83.addLayout(self.gridLayout_69)


        self.verticalLayout_62.addWidget(self.groupBox_72)

        self.groupBox_75 = QGroupBox(self.tab_44)
        self.groupBox_75.setObjectName(u"groupBox_75")
        self.horizontalLayout_31 = QHBoxLayout(self.groupBox_75)
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.comboBox_72 = QComboBox(self.groupBox_75)
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.addItem("")
        self.comboBox_72.setObjectName(u"comboBox_72")
        self.comboBox_72.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.comboBox_72.setStyleSheet(u"")
        self.comboBox_72.setEditable(False)
        self.comboBox_72.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.comboBox_72.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.horizontalLayout_31.addWidget(self.comboBox_72)

        self.pushButton_73 = QPushButton(self.groupBox_75)
        self.pushButton_73.setObjectName(u"pushButton_73")

        self.horizontalLayout_31.addWidget(self.pushButton_73)

        self.horizontalLayout_31.setStretch(0, 1)
        self.horizontalLayout_31.setStretch(1, 1)

        self.verticalLayout_62.addWidget(self.groupBox_75)

        self.verticalSpacer_39 = QSpacerItem(20, 211, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_62.addItem(self.verticalSpacer_39)

        self.pushButton_72 = QPushButton(self.tab_44)
        self.pushButton_72.setObjectName(u"pushButton_72")
        palette18 = QPalette()
        palette18.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette18.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette18.setBrush(QPalette.Active, QPalette.Text, brush)
        palette18.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette18.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette18.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush58 = QBrush(QColor(255, 255, 255, 128))
        brush58.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette18.setBrush(QPalette.Active, QPalette.PlaceholderText, brush58)
#endif
        palette18.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette18.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette18.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette18.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette18.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette18.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush59 = QBrush(QColor(255, 255, 255, 128))
        brush59.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette18.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush59)
#endif
        palette18.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette18.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette18.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette18.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette18.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette18.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush60 = QBrush(QColor(255, 255, 255, 128))
        brush60.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette18.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush60)
#endif
        self.pushButton_72.setPalette(palette18)
        self.pushButton_72.setFont(font2)
        self.pushButton_72.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_62.addWidget(self.pushButton_72)

        self.tabWidget.addTab(self.tab_44, "")
        self.tab_38 = QWidget()
        self.tab_38.setObjectName(u"tab_38")
        self.verticalLayout_82 = QVBoxLayout(self.tab_38)
        self.verticalLayout_82.setObjectName(u"verticalLayout_82")
        self.groupBox_52 = QGroupBox(self.tab_38)
        self.groupBox_52.setObjectName(u"groupBox_52")
        self.gridLayout_56 = QGridLayout(self.groupBox_52)
        self.gridLayout_56.setObjectName(u"gridLayout_56")
        self.label_149 = QLabel(self.groupBox_52)
        self.label_149.setObjectName(u"label_149")

        self.gridLayout_56.addWidget(self.label_149, 0, 0, 1, 1)

        self.pushButton_43 = QPushButton(self.groupBox_52)
        self.pushButton_43.setObjectName(u"pushButton_43")
        self.pushButton_43.setFont(font4)

        self.gridLayout_56.addWidget(self.pushButton_43, 0, 1, 1, 1)

        self.lineEdit_27 = QLineEdit(self.groupBox_52)
        self.lineEdit_27.setObjectName(u"lineEdit_27")

        self.gridLayout_56.addWidget(self.lineEdit_27, 1, 0, 1, 2)

        self.gridLayout_56.setColumnStretch(0, 1)
        self.gridLayout_56.setColumnStretch(1, 1)

        self.verticalLayout_82.addWidget(self.groupBox_52)

        self.verticalSpacer_32 = QSpacerItem(20, 341, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_82.addItem(self.verticalSpacer_32)

        self.pushButton_42 = QPushButton(self.tab_38)
        self.pushButton_42.setObjectName(u"pushButton_42")
        palette19 = QPalette()
        palette19.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette19.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette19.setBrush(QPalette.Active, QPalette.Text, brush)
        palette19.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette19.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette19.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush61 = QBrush(QColor(255, 255, 255, 128))
        brush61.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette19.setBrush(QPalette.Active, QPalette.PlaceholderText, brush61)
#endif
        palette19.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette19.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette19.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette19.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette19.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette19.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush62 = QBrush(QColor(255, 255, 255, 128))
        brush62.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette19.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush62)
#endif
        palette19.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette19.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette19.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette19.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette19.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette19.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush63 = QBrush(QColor(255, 255, 255, 128))
        brush63.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette19.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush63)
#endif
        self.pushButton_42.setPalette(palette19)
        self.pushButton_42.setFont(font2)
        self.pushButton_42.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_82.addWidget(self.pushButton_42)

        self.tabWidget.addTab(self.tab_38, "")
        self.tab_39 = QWidget()
        self.tab_39.setObjectName(u"tab_39")
        self.verticalLayout_51 = QVBoxLayout(self.tab_39)
        self.verticalLayout_51.setObjectName(u"verticalLayout_51")
        self.groupBox_53 = QGroupBox(self.tab_39)
        self.groupBox_53.setObjectName(u"groupBox_53")
        self.verticalLayout_50 = QVBoxLayout(self.groupBox_53)
        self.verticalLayout_50.setObjectName(u"verticalLayout_50")
        self.gridLayout_57 = QGridLayout()
        self.gridLayout_57.setObjectName(u"gridLayout_57")
        self.label_150 = QLabel(self.groupBox_53)
        self.label_150.setObjectName(u"label_150")
        self.label_150.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_57.addWidget(self.label_150, 0, 0, 1, 1)

        self.comboBox_57 = QComboBox(self.groupBox_53)
        self.comboBox_57.setObjectName(u"comboBox_57")

        self.gridLayout_57.addWidget(self.comboBox_57, 0, 1, 1, 1)

        self.label_151 = QLabel(self.groupBox_53)
        self.label_151.setObjectName(u"label_151")
        self.label_151.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_57.addWidget(self.label_151, 1, 0, 1, 1)

        self.comboBox_58 = QComboBox(self.groupBox_53)
        self.comboBox_58.setObjectName(u"comboBox_58")

        self.gridLayout_57.addWidget(self.comboBox_58, 1, 1, 1, 1)

        self.label_152 = QLabel(self.groupBox_53)
        self.label_152.setObjectName(u"label_152")
        self.label_152.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_57.addWidget(self.label_152, 2, 0, 1, 1)

        self.lineEdit_28 = QLineEdit(self.groupBox_53)
        self.lineEdit_28.setObjectName(u"lineEdit_28")

        self.gridLayout_57.addWidget(self.lineEdit_28, 2, 1, 1, 1)

        self.gridLayout_57.setColumnStretch(0, 1)
        self.gridLayout_57.setColumnStretch(1, 5)

        self.verticalLayout_50.addLayout(self.gridLayout_57)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.horizontalSpacer_21 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_21)

        self.checkBox_10 = QCheckBox(self.groupBox_53)
        self.checkBox_10.setObjectName(u"checkBox_10")

        self.horizontalLayout_21.addWidget(self.checkBox_10)

        self.pushButton_44 = QPushButton(self.groupBox_53)
        self.pushButton_44.setObjectName(u"pushButton_44")
        self.pushButton_44.setFont(font4)

        self.horizontalLayout_21.addWidget(self.pushButton_44)

        self.horizontalLayout_21.setStretch(0, 1)
        self.horizontalLayout_21.setStretch(1, 1)
        self.horizontalLayout_21.setStretch(2, 2)

        self.verticalLayout_50.addLayout(self.horizontalLayout_21)


        self.verticalLayout_51.addWidget(self.groupBox_53)

        self.groupBox_54 = QGroupBox(self.tab_39)
        self.groupBox_54.setObjectName(u"groupBox_54")
        self.gridLayout_58 = QGridLayout(self.groupBox_54)
        self.gridLayout_58.setObjectName(u"gridLayout_58")
        self.textEdit_6 = QTextEdit(self.groupBox_54)
        self.textEdit_6.setObjectName(u"textEdit_6")

        self.gridLayout_58.addWidget(self.textEdit_6, 0, 0, 1, 2)

        self.horizontalSpacer_9 = QSpacerItem(218, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_58.addItem(self.horizontalSpacer_9, 1, 0, 1, 1)

        self.pushButton_45 = QPushButton(self.groupBox_54)
        self.pushButton_45.setObjectName(u"pushButton_45")
        self.pushButton_45.setFont(font4)

        self.gridLayout_58.addWidget(self.pushButton_45, 1, 1, 1, 1)

        self.gridLayout_58.setColumnStretch(0, 1)
        self.gridLayout_58.setColumnStretch(1, 1)

        self.verticalLayout_51.addWidget(self.groupBox_54)

        self.verticalSpacer_33 = QSpacerItem(20, 92, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_51.addItem(self.verticalSpacer_33)

        self.pushButton_59 = QPushButton(self.tab_39)
        self.pushButton_59.setObjectName(u"pushButton_59")
        palette20 = QPalette()
        palette20.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette20.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette20.setBrush(QPalette.Active, QPalette.Text, brush)
        palette20.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette20.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette20.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush64 = QBrush(QColor(255, 255, 255, 128))
        brush64.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette20.setBrush(QPalette.Active, QPalette.PlaceholderText, brush64)
#endif
        palette20.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette20.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette20.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette20.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette20.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette20.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush65 = QBrush(QColor(255, 255, 255, 128))
        brush65.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette20.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush65)
#endif
        palette20.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette20.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette20.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette20.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette20.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette20.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush66 = QBrush(QColor(255, 255, 255, 128))
        brush66.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette20.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush66)
#endif
        self.pushButton_59.setPalette(palette20)
        self.pushButton_59.setFont(font2)
        self.pushButton_59.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_51.addWidget(self.pushButton_59)

        self.tabWidget.addTab(self.tab_39, "")
        self.tab_40 = QWidget()
        self.tab_40.setObjectName(u"tab_40")
        self.verticalLayout_85 = QVBoxLayout(self.tab_40)
        self.verticalLayout_85.setObjectName(u"verticalLayout_85")
        self.groupBox_55 = QGroupBox(self.tab_40)
        self.groupBox_55.setObjectName(u"groupBox_55")
        self.verticalLayout_61 = QVBoxLayout(self.groupBox_55)
        self.verticalLayout_61.setObjectName(u"verticalLayout_61")
        self.verticalLayout_84 = QVBoxLayout()
        self.verticalLayout_84.setObjectName(u"verticalLayout_84")
        self.label_153 = QLabel(self.groupBox_55)
        self.label_153.setObjectName(u"label_153")
        self.label_153.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_84.addWidget(self.label_153)

        self.pushButton_46 = QPushButton(self.groupBox_55)
        self.pushButton_46.setObjectName(u"pushButton_46")

        self.verticalLayout_84.addWidget(self.pushButton_46)


        self.verticalLayout_61.addLayout(self.verticalLayout_84)


        self.verticalLayout_85.addWidget(self.groupBox_55)

        self.groupBox_56 = QGroupBox(self.tab_40)
        self.groupBox_56.setObjectName(u"groupBox_56")
        self.gridLayout_59 = QGridLayout(self.groupBox_56)
        self.gridLayout_59.setObjectName(u"gridLayout_59")
        self.comboBox_59 = QComboBox(self.groupBox_56)
        self.comboBox_59.setObjectName(u"comboBox_59")

        self.gridLayout_59.addWidget(self.comboBox_59, 0, 1, 1, 1)

        self.label_154 = QLabel(self.groupBox_56)
        self.label_154.setObjectName(u"label_154")
        self.label_154.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_59.addWidget(self.label_154, 0, 0, 1, 1)

        self.pushButton_48 = QPushButton(self.groupBox_56)
        self.pushButton_48.setObjectName(u"pushButton_48")
        self.pushButton_48.setFont(font4)

        self.gridLayout_59.addWidget(self.pushButton_48, 2, 1, 1, 1)

        self.pushButton_49 = QPushButton(self.groupBox_56)
        self.pushButton_49.setObjectName(u"pushButton_49")

        self.gridLayout_59.addWidget(self.pushButton_49, 2, 0, 1, 1)

        self.gridLayout_59.setColumnStretch(0, 1)
        self.gridLayout_59.setColumnStretch(1, 1)

        self.verticalLayout_85.addWidget(self.groupBox_56)

        self.verticalSpacer_34 = QSpacerItem(20, 308, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_85.addItem(self.verticalSpacer_34)

        self.pushButton_47 = QPushButton(self.tab_40)
        self.pushButton_47.setObjectName(u"pushButton_47")
        palette21 = QPalette()
        palette21.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette21.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette21.setBrush(QPalette.Active, QPalette.Text, brush)
        palette21.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette21.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette21.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush67 = QBrush(QColor(255, 255, 255, 128))
        brush67.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette21.setBrush(QPalette.Active, QPalette.PlaceholderText, brush67)
#endif
        palette21.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette21.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette21.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette21.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette21.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette21.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush68 = QBrush(QColor(255, 255, 255, 128))
        brush68.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette21.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush68)
#endif
        palette21.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        palette21.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette21.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette21.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette21.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette21.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        brush69 = QBrush(QColor(255, 255, 255, 128))
        brush69.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette21.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush69)
#endif
        self.pushButton_47.setPalette(palette21)
        self.pushButton_47.setFont(font2)
        self.pushButton_47.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(0, 170, 0);\n"
"    color: white;\n"
"    border-radius: 10px; /* \u8bbe\u7f6e\u5706\u89d2\u534a\u5f84 */\n"
"    font-family: 'Microsoft YaHei'; /* \u8bbe\u7f6e\u5b57\u4f53\u4e3a\u5fae\u8f6f\u96c5\u9ed1 */\n"
"    padding: 3px 5px; /* \u8bbe\u7f6e\u5185\u8fb9\u8ddd\uff0c\u4f7f\u6309\u94ae\u770b\u8d77\u6765\u66f4\u7f8e\u89c2 */\n"
"    border: 2px solid transparent; /* \u8bbe\u7f6e\u8fb9\u6846\u4e3a\u900f\u660e */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: rgb(0, 150, 0); /* \u8bbe\u7f6e\u9f20\u6807\u60ac\u505c\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: rgb(0, 100, 0); /* \u8bbe\u7f6e\u6309\u94ae\u6309\u4e0b\u65f6\u7684\u80cc\u666f\u989c\u8272 */\n"
"}\n"
"")

        self.verticalLayout_85.addWidget(self.pushButton_47)

        self.tabWidget.addTab(self.tab_40, "")

        self.verticalLayout_6.addWidget(self.tabWidget)

        self.tabWidget_2 = QTabWidget(navigation)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tab_20 = QWidget()
        self.tab_20.setObjectName(u"tab_20")
        self.verticalLayout_44 = QVBoxLayout(self.tab_20)
        self.verticalLayout_44.setObjectName(u"verticalLayout_44")
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_33 = QLabel(self.tab_20)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_33, 0, 2, 1, 1)

        self.lineEdit_5 = QLineEdit(self.tab_20)
        self.lineEdit_5.setObjectName(u"lineEdit_5")
        self.lineEdit_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.lineEdit_5, 2, 0, 1, 4)

        self.comboBox_9 = QComboBox(self.tab_20)
        self.comboBox_9.addItem("")
        self.comboBox_9.addItem("")
        self.comboBox_9.addItem("")
        self.comboBox_9.setObjectName(u"comboBox_9")

        self.gridLayout_5.addWidget(self.comboBox_9, 0, 3, 1, 1)

        self.spinBox = QSpinBox(self.tab_20)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(999)

        self.gridLayout_5.addWidget(self.spinBox, 0, 1, 1, 1)

        self.label_21 = QLabel(self.tab_20)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_21, 0, 0, 1, 1)


        self.verticalLayout_44.addLayout(self.gridLayout_5)

        self.tabWidget_2.addTab(self.tab_20, "")
        self.tab_21 = QWidget()
        self.tab_21.setObjectName(u"tab_21")
        self.verticalLayout_45 = QVBoxLayout(self.tab_21)
        self.verticalLayout_45.setObjectName(u"verticalLayout_45")
        self.gridLayout_34 = QGridLayout()
        self.gridLayout_34.setObjectName(u"gridLayout_34")
        self.label_43 = QLabel(self.tab_21)
        self.label_43.setObjectName(u"label_43")
        sizePolicy.setHeightForWidth(self.label_43.sizePolicy().hasHeightForWidth())
        self.label_43.setSizePolicy(sizePolicy)
        self.label_43.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_34.addWidget(self.label_43, 0, 0, 2, 1)

        self.pushButton_9 = QPushButton(self.tab_21)
        self.pushButton_9.setObjectName(u"pushButton_9")

        self.gridLayout_34.addWidget(self.pushButton_9, 0, 1, 1, 1)

        self.pushButton_10 = QPushButton(self.tab_21)
        self.pushButton_10.setObjectName(u"pushButton_10")

        self.gridLayout_34.addWidget(self.pushButton_10, 1, 1, 1, 1)

        self.gridLayout_34.setColumnStretch(0, 3)

        self.verticalLayout_45.addLayout(self.gridLayout_34)

        self.tabWidget_2.addTab(self.tab_21, "")
        self.tab_24 = QWidget()
        self.tab_24.setObjectName(u"tab_24")
        self.verticalLayout_49 = QVBoxLayout(self.tab_24)
        self.verticalLayout_49.setObjectName(u"verticalLayout_49")
        self.textBrowser = QTextBrowser(self.tab_24)
        self.textBrowser.setObjectName(u"textBrowser")
        palette22 = QPalette()
        brush70 = QBrush(QColor(0, 0, 255, 255))
        brush70.setStyle(Qt.SolidPattern)
        palette22.setBrush(QPalette.Active, QPalette.Text, brush70)
        brush71 = QBrush(QColor(0, 0, 255, 128))
        brush71.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette22.setBrush(QPalette.Active, QPalette.PlaceholderText, brush71)
#endif
        palette22.setBrush(QPalette.Inactive, QPalette.Text, brush70)
        brush72 = QBrush(QColor(0, 0, 255, 128))
        brush72.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette22.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush72)
#endif
        brush73 = QBrush(QColor(120, 120, 120, 255))
        brush73.setStyle(Qt.SolidPattern)
        palette22.setBrush(QPalette.Disabled, QPalette.Text, brush73)
        brush74 = QBrush(QColor(0, 0, 255, 128))
        brush74.setStyle(Qt.NoBrush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette22.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush74)
#endif
        self.textBrowser.setPalette(palette22)

        self.verticalLayout_49.addWidget(self.textBrowser)

        self.tabWidget_2.addTab(self.tab_24, "")

        self.verticalLayout_6.addWidget(self.tabWidget_2)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.pushButton_2 = QPushButton(navigation)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setFont(font4)
        self.pushButton_2.setStyleSheet(u"")

        self.horizontalLayout_14.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(navigation)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.horizontalLayout_14.addWidget(self.pushButton_3)


        self.verticalLayout_6.addLayout(self.horizontalLayout_14)


        self.horizontalLayout_16.addLayout(self.verticalLayout_6)

        self.horizontalLayout_16.setStretch(0, 1)
        self.horizontalLayout_16.setStretch(1, 3)

        self.retranslateUi(navigation)
        self.pushButton_3.clicked.connect(navigation.close)
        self.horizontalSlider.sliderMoved.connect(self.label_118.setNum)
        self.horizontalSlider_2.sliderMoved.connect(self.spinBox_19.setValue)
        self.horizontalSlider_3.sliderMoved.connect(self.spinBox_20.setValue)

        self.tabWidget.setCurrentIndex(0)
        self.comboBox_2.setCurrentIndex(0)
        self.comboBox_70.setCurrentIndex(0)
        self.comboBox_71.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(navigation)
    # setupUi

    def retranslateUi(self, navigation):
        navigation.setWindowTitle(QCoreApplication.translate("navigation", u"\u5bfc\u822a\u9875", None))
        self.lineEdit_22.setPlaceholderText(QCoreApplication.translate("navigation", u"\u641c\u7d22\u6307\u4ee4...", None))
        ___qtreewidgetitem = self.treeWidget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("navigation", u"\u6307\u4ee4\u9009\u62e9", None));

        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.treeWidget.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("navigation", u"\u952e\u9f20\u6307\u4ee4", None));
        ___qtreewidgetitem2 = ___qtreewidgetitem1.child(0)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("navigation", u"\u56fe\u50cf\u70b9\u51fb", None));
        ___qtreewidgetitem3 = ___qtreewidgetitem1.child(1)
        ___qtreewidgetitem3.setText(0, QCoreApplication.translate("navigation", u"\u591a\u56fe\u70b9\u51fb", None));
        ___qtreewidgetitem4 = ___qtreewidgetitem1.child(2)
        ___qtreewidgetitem4.setText(0, QCoreApplication.translate("navigation", u"\u5750\u6807\u70b9\u51fb", None));
        ___qtreewidgetitem5 = ___qtreewidgetitem1.child(3)
        ___qtreewidgetitem5.setText(0, QCoreApplication.translate("navigation", u"\u79fb\u52a8\u9f20\u6807", None));
        ___qtreewidgetitem6 = ___qtreewidgetitem1.child(4)
        ___qtreewidgetitem6.setText(0, QCoreApplication.translate("navigation", u"\u9f20\u6807\u70b9\u51fb", None));
        ___qtreewidgetitem7 = ___qtreewidgetitem1.child(5)
        ___qtreewidgetitem7.setText(0, QCoreApplication.translate("navigation", u"\u6eda\u8f6e\u6ed1\u52a8", None));
        ___qtreewidgetitem8 = ___qtreewidgetitem1.child(6)
        ___qtreewidgetitem8.setText(0, QCoreApplication.translate("navigation", u"\u6309\u4e0b\u952e\u76d8", None));
        ___qtreewidgetitem9 = ___qtreewidgetitem1.child(7)
        ___qtreewidgetitem9.setText(0, QCoreApplication.translate("navigation", u"\u6587\u672c\u8f93\u5165", None));
        ___qtreewidgetitem10 = ___qtreewidgetitem1.child(8)
        ___qtreewidgetitem10.setText(0, QCoreApplication.translate("navigation", u"\u4e2d\u952e\u6fc0\u6d3b", None));
        ___qtreewidgetitem11 = ___qtreewidgetitem1.child(9)
        ___qtreewidgetitem11.setText(0, QCoreApplication.translate("navigation", u"\u9f20\u6807\u62d6\u62fd", None));
        ___qtreewidgetitem12 = self.treeWidget.topLevelItem(1)
        ___qtreewidgetitem12.setText(0, QCoreApplication.translate("navigation", u"\u7b49\u5f85", None));
        ___qtreewidgetitem13 = ___qtreewidgetitem12.child(0)
        ___qtreewidgetitem13.setText(0, QCoreApplication.translate("navigation", u"\u65f6\u95f4\u7b49\u5f85", None));
        ___qtreewidgetitem14 = ___qtreewidgetitem12.child(1)
        ___qtreewidgetitem14.setText(0, QCoreApplication.translate("navigation", u"\u56fe\u50cf\u7b49\u5f85", None));
        ___qtreewidgetitem15 = ___qtreewidgetitem12.child(2)
        ___qtreewidgetitem15.setText(0, QCoreApplication.translate("navigation", u"\u5012\u8ba1\u65f6\u7a97\u53e3", None));
        ___qtreewidgetitem16 = ___qtreewidgetitem12.child(3)
        ___qtreewidgetitem16.setText(0, QCoreApplication.translate("navigation", u"\u6309\u952e\u7b49\u5f85", None));
        ___qtreewidgetitem17 = ___qtreewidgetitem12.child(4)
        ___qtreewidgetitem17.setText(0, QCoreApplication.translate("navigation", u"\u7a97\u53e3\u7126\u70b9\u7b49\u5f85", None));
        ___qtreewidgetitem18 = self.treeWidget.topLevelItem(2)
        ___qtreewidgetitem18.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6\u53d8\u91cf", None));
        ___qtreewidgetitem19 = ___qtreewidgetitem18.child(0)
        ___qtreewidgetitem19.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6\u65f6\u95f4", None));
        ___qtreewidgetitem20 = ___qtreewidgetitem18.child(1)
        ___qtreewidgetitem20.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6Excel", None));
        ___qtreewidgetitem21 = ___qtreewidgetitem18.child(2)
        ___qtreewidgetitem21.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6\u9f20\u6807\u4f4d\u7f6e", None));
        ___qtreewidgetitem22 = ___qtreewidgetitem18.child(3)
        ___qtreewidgetitem22.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6\u526a\u5207\u677f", None));
        ___qtreewidgetitem23 = ___qtreewidgetitem18.child(4)
        ___qtreewidgetitem23.setText(0, QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5bf9\u8bdd\u6846", None));
        ___qtreewidgetitem24 = ___qtreewidgetitem18.child(5)
        ___qtreewidgetitem24.setText(0, QCoreApplication.translate("navigation", u"\u6570\u5b57\u9a8c\u8bc1\u7801", None));
        ___qtreewidgetitem25 = ___qtreewidgetitem18.child(6)
        ___qtreewidgetitem25.setText(0, QCoreApplication.translate("navigation", u"OCR\u8bc6\u522b", None));
        ___qtreewidgetitem26 = self.treeWidget.topLevelItem(3)
        ___qtreewidgetitem26.setText(0, QCoreApplication.translate("navigation", u"Excel\u6307\u4ee4", None));
        ___qtreewidgetitem27 = ___qtreewidgetitem26.child(0)
        ___qtreewidgetitem27.setText(0, QCoreApplication.translate("navigation", u"\u5199\u5165\u5355\u5143\u683c", None));
        ___qtreewidgetitem28 = self.treeWidget.topLevelItem(4)
        ___qtreewidgetitem28.setText(0, QCoreApplication.translate("navigation", u"\u5176\u4ed6", None));
        ___qtreewidgetitem29 = ___qtreewidgetitem28.child(0)
        ___qtreewidgetitem29.setText(0, QCoreApplication.translate("navigation", u"\u8fd0\u884cPython", None));
        ___qtreewidgetitem30 = ___qtreewidgetitem28.child(1)
        ___qtreewidgetitem30.setText(0, QCoreApplication.translate("navigation", u"\u8fd0\u884ccmd", None));
        ___qtreewidgetitem31 = ___qtreewidgetitem28.child(2)
        ___qtreewidgetitem31.setText(0, QCoreApplication.translate("navigation", u"\u8fd0\u884c\u5916\u90e8\u6587\u4ef6", None));
        ___qtreewidgetitem32 = ___qtreewidgetitem28.child(3)
        ___qtreewidgetitem32.setText(0, QCoreApplication.translate("navigation", u"\u7a97\u53e3\u63a7\u5236", None));
        ___qtreewidgetitem33 = ___qtreewidgetitem28.child(4)
        ___qtreewidgetitem33.setText(0, QCoreApplication.translate("navigation", u"\u4fe1\u606f\u5f55\u5165", None));
        ___qtreewidgetitem34 = ___qtreewidgetitem28.child(5)
        ___qtreewidgetitem34.setText(0, QCoreApplication.translate("navigation", u"\u5c4f\u5e55\u622a\u56fe", None));
        ___qtreewidgetitem35 = ___qtreewidgetitem28.child(6)
        ___qtreewidgetitem35.setText(0, QCoreApplication.translate("navigation", u"\u63d0\u793a\u97f3", None));
        ___qtreewidgetitem36 = ___qtreewidgetitem28.child(7)
        ___qtreewidgetitem36.setText(0, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u901a\u77e5", None));
        ___qtreewidgetitem37 = ___qtreewidgetitem28.child(8)
        ___qtreewidgetitem37.setText(0, QCoreApplication.translate("navigation", u"\u63d0\u793a\u7a97\u53e3", None));
        ___qtreewidgetitem38 = self.treeWidget.topLevelItem(5)
        ___qtreewidgetitem38.setText(0, QCoreApplication.translate("navigation", u"\u6d41\u7a0b\u63a7\u5236", None));
        ___qtreewidgetitem39 = ___qtreewidgetitem38.child(0)
        ___qtreewidgetitem39.setText(0, QCoreApplication.translate("navigation", u"\u7ec8\u6b62\u6d41\u7a0b", None));
        self.treeWidget.setSortingEnabled(__sortingEnabled)

        self.label.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u5c06\u56fe\u50cf\u7edf\u4e00\u4fdd\u5b58\u81f3\u67d0\u6587\u4ef6\u5939\uff0c\u70b9\u51fb\u6dfb\u52a0\u6587\u4ef6\u5939\u5373\u53ef\u3002", None))
        self.label_2.setText(QCoreApplication.translate("navigation", u"\u5f53\u524d\u6587\u4ef6\u5939\uff1a", None))
        self.label_3.setText(QCoreApplication.translate("navigation", u"\u6682\u65e0", None))
        self.pushButton.setText(QCoreApplication.translate("navigation", u"\u5feb\u6377\u622a\u56fe", None))
        self.pushButton_7.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u8d44\u6e90\u6587\u4ef6\u5939", None))
        self.label_4.setText(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u540d\u79f0\uff1a", None))
        self.checkBox.setText(QCoreApplication.translate("navigation", u"\u542f\u7528\u7070\u5ea6\u8bc6\u522b", None))
        self.label_36.setText(QCoreApplication.translate("navigation", u"\u6587\u4ef6\u5939\u540d\u79f0\uff1a", None))
        self.label_5.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u540d\u79f0\uff1a", None))
        self.comboBox_8.setCurrentText("")
        self.pushButton_11.setText(QCoreApplication.translate("navigation", u"\u9ad8\u7ea7\u8bbe\u7f6e", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("navigation", u"\u5de6\u952e\u5355\u51fb", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("navigation", u"\u5de6\u952e\u53cc\u51fb", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("navigation", u"\u53f3\u952e\u5355\u51fb", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("navigation", u"\u53f3\u952e\u53cc\u51fb", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("navigation", u"\u4ec5\u79fb\u52a8\u9f20\u6807", None))

        self.groupBox_77.setTitle(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u70b9\u51fb\u4f4d\u7f6e\u548c\u7cbe\u5ea6", None))
        self.label_176.setText(QCoreApplication.translate("navigation", u"(0,0)", None))
        self.pushButton_76.setText(QCoreApplication.translate("navigation", u"\u8c03\u6574\u70b9\u51fb\u4f4d\u7f6e", None))
        self.label_177.setText(QCoreApplication.translate("navigation", u"\u8bc6\u522b\u7cbe\u5ea6\uff1a", None))
        self.label_178.setText(QCoreApplication.translate("navigation", u"0%", None))
        self.groupBox_57.setTitle(QCoreApplication.translate("navigation", u"\u542f\u7528\u6307\u5b9a\u533a\u57df\u8bc6\u522b", None))
        self.label_155.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_50.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u533a\u57df", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("navigation", u"\u62a5\u9519\u5904\u7406", None))
        self.radioButton_2.setText(QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u6307\u5b9a\u56fe\u50cf\u65f6\u81ea\u52a8\u7565\u8fc7\u8be5\u6307\u4ee4", None))
        self.radioButton_4.setText(QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u56fe\u7247\u8d85\u65f6\u62a5\u9519", None))
        self.label_42.setText(QCoreApplication.translate("navigation", u"\u79d2\u6570\uff1a", None))
        self.pushButton_6.setText(QCoreApplication.translate("navigation", u"\u627e\u56fe\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("navigation", u"\u56fe\u50cf\u70b9\u51fb", None))
        self.label_172.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u904d\u5386\u8bc6\u522b\u591a\u4e2a\u4e0d\u540c\u56fe\u50cf\uff0c\u5982\u679c\u6709\u5339\u914d\u5219\u6267\u884c\u9f20\u6807\u52a8\u4f5c\u3002", None))
        self.groupBox_71.setTitle(QCoreApplication.translate("navigation", u"\u5982\u679c\u5339\u914d\u5230\u5982\u4e0b\u56fe\u50cf\u4e4b\u4e00", None))
        self.pushButton_67.setText(QCoreApplication.translate("navigation", u"\u6dfb\u52a0\u56fe\u50cf", None))
        self.toolButton_2.setText(QCoreApplication.translate("navigation", u"...", None))
        self.pushButton_63.setText(QCoreApplication.translate("navigation", u"\u5feb\u6377\u622a\u56fe", None))
        self.pushButton_64.setText(QCoreApplication.translate("navigation", u"\u79fb\u9664\u9009\u4e2d", None))
        self.toolButton.setText(QCoreApplication.translate("navigation", u"...", None))
        self.pushButton_68.setText(QCoreApplication.translate("navigation", u"\u5220\u9664\u672c\u5730\u56fe\u50cf", None))
        self.groupBox_74.setTitle(QCoreApplication.translate("navigation", u"\u5219\u6267\u884c\u9f20\u6807\u52a8\u4f5c", None))
        self.comboBox_70.setItemText(0, QCoreApplication.translate("navigation", u"\u5de6\u952e\u5355\u51fb", None))
        self.comboBox_70.setItemText(1, QCoreApplication.translate("navigation", u"\u5de6\u952e\u53cc\u51fb", None))
        self.comboBox_70.setItemText(2, QCoreApplication.translate("navigation", u"\u53f3\u952e\u5355\u51fb", None))
        self.comboBox_70.setItemText(3, QCoreApplication.translate("navigation", u"\u53f3\u952e\u53cc\u51fb", None))
        self.comboBox_70.setItemText(4, QCoreApplication.translate("navigation", u"\u4ec5\u79fb\u52a8\u9f20\u6807", None))

        self.pushButton_66.setText(QCoreApplication.translate("navigation", u"\u9ad8\u7ea7\u8bbe\u7f6e", None))
        self.comboBox_71.setItemText(0, QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u5168\u90e8\u56fe\u50cf\u65f6\u7acb\u5373\u62a5\u9519", None))
        self.comboBox_71.setItemText(1, QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u5168\u90e8\u56fe\u50cf\u65f6\u81ea\u52a8\u7565\u8fc7", None))

        self.checkBox_11.setText(QCoreApplication.translate("navigation", u"\u542f\u7528\u7070\u5ea6\u8bc6\u522b", None))
        self.groupBox_78.setTitle(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u8bc6\u522b\u7cbe\u5ea6", None))
        self.label_181.setText(QCoreApplication.translate("navigation", u"0%", None))
        self.label_180.setText(QCoreApplication.translate("navigation", u"\u8bc6\u522b\u7cbe\u5ea6\uff1a", None))
        self.groupBox_73.setTitle(QCoreApplication.translate("navigation", u"\u542f\u7528\u6307\u5b9a\u533a\u57df\u8bc6\u522b", None))
        self.label_174.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_65.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u533a\u57df", None))
        self.pushButton_69.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_43), QCoreApplication.translate("navigation", u"\u591a\u56fe\u70b9\u51fb", None))
        self.label_6.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6309\u4f4f\u201c\u83b7\u53d6\u5750\u6807\u201d\u6309\u94ae\uff0c\u5e76\u79fb\u52a8\u9f20\u6807\u3002", None))
        self.pushButton_4.setText(QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5750\u6807\uff08\u6309\u4f4f\u62d6\u52a8\uff09", None))
        self.label_7.setText(QCoreApplication.translate("navigation", u"X\uff1a", None))
        self.label_9.setText(QCoreApplication.translate("navigation", u"0", None))
        self.label_8.setText(QCoreApplication.translate("navigation", u"Y\uff1a", None))
        self.label_10.setText(QCoreApplication.translate("navigation", u"0", None))
        self.label_11.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u540d\u79f0\uff1a", None))
        self.comboBox_3.setItemText(0, QCoreApplication.translate("navigation", u"\u5de6\u952e\u5355\u51fb", None))
        self.comboBox_3.setItemText(1, QCoreApplication.translate("navigation", u"\u5de6\u952e\u53cc\u51fb", None))
        self.comboBox_3.setItemText(2, QCoreApplication.translate("navigation", u"\u53f3\u952e\u5355\u51fb", None))
        self.comboBox_3.setItemText(3, QCoreApplication.translate("navigation", u"\u53f3\u952e\u53cc\u51fb", None))
        self.comboBox_3.setItemText(4, QCoreApplication.translate("navigation", u"\u5de6\u952e\uff08\u81ea\u5b9a\u4e49\u6b21\u6570\uff09", None))
        self.comboBox_3.setItemText(5, QCoreApplication.translate("navigation", u"\u4ec5\u79fb\u52a8\u9f20\u6807", None))

        self.label_22.setText(QCoreApplication.translate("navigation", u"\u81ea\u5b9a\u4e49\u6b21\u6570\uff1a", None))
        self.pushButton_23.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_27), QCoreApplication.translate("navigation", u"\u5750\u6807\u70b9\u51fb", None))
        self.groupBox_28.setTitle(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u6307\u5b9a\u8ddd\u79bb", None))
        self.label_13.setText(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u8ddd\u79bb\uff08\u50cf\u7d20\uff09\uff1a", None))
        self.comboBox_4.setItemText(0, QCoreApplication.translate("navigation", u"\u2192", None))
        self.comboBox_4.setItemText(1, QCoreApplication.translate("navigation", u"\u2190", None))
        self.comboBox_4.setItemText(2, QCoreApplication.translate("navigation", u"\u2191", None))
        self.comboBox_4.setItemText(3, QCoreApplication.translate("navigation", u"\u2193", None))

        self.label_12.setText(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u65b9\u5411\uff1a", None))
        self.groupBox_30.setTitle(QCoreApplication.translate("navigation", u"\u968f\u673a\u79fb\u52a8\u9f20\u6807", None))
        self.comboBox_16.setItemText(0, QCoreApplication.translate("navigation", u"\u7c7b\u578b1", None))
        self.comboBox_16.setItemText(1, QCoreApplication.translate("navigation", u"\u7c7b\u578b2", None))

        self.label_102.setText(QCoreApplication.translate("navigation", u"\u968f\u673a\u7c7b\u578b\uff1a", None))
        self.groupBox_59.setTitle(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u5230\u6307\u5b9a\u5750\u6807", None))
        self.label_157.setText(QCoreApplication.translate("navigation", u"X\uff1a", None))
        self.label_158.setText(QCoreApplication.translate("navigation", u"Y\uff1a", None))
        self.label_31.setText(QCoreApplication.translate("navigation", u"\u6301\u7eed\u65f6\u95f4\uff1a", None))
        self.pushButton_56.setText(QCoreApplication.translate("navigation", u"\u81ea\u52a8\u83b7\u53d6\u5750\u6807\uff08\u6309\u4f4f\u62d6\u52a8\uff09", None))
        self.groupBox_20.setTitle(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u5230\u53d8\u91cf\u5750\u6807", None))
        self.label_25.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_57.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u53d8\u91cf\u6c60", None))
        self.label_173.setText(QCoreApplication.translate("navigation", u"\uff08\u4e0e\u201c\u83b7\u53d6\u9f20\u6807\u4f4d\u7f6e\u201d\u6307\u4ee4\u914d\u5408\uff09", None))
        self.pushButton_52.setText(QCoreApplication.translate("navigation", u"\u79fb\u52a8\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("navigation", u"\u79fb\u52a8\u9f20\u6807", None))
        self.label_87.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0\u3002", None))
        self.groupBox_31.setTitle(QCoreApplication.translate("navigation", u"\u9f20\u6807\u5728\u5f53\u524d\u4f4d\u7f6e\u6267\u884c\uff1a", None))
        self.label_111.setText(QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.label_109.setText(QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.label_107.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u540d\u79f0\uff1a", None))
        self.comboBox_35.setItemText(0, QCoreApplication.translate("navigation", u"\u5de6\u952e\uff08\u81ea\u5b9a\u4e49\u6b21\u6570\uff09", None))
        self.comboBox_35.setItemText(1, QCoreApplication.translate("navigation", u"\u53f3\u952e\uff08\u81ea\u5b9a\u4e49\u6b21\u6570\uff09", None))

        self.label_32.setText(QCoreApplication.translate("navigation", u"\u9f20\u6807\u6309\u538b\u65f6\u957f\uff1a", None))
        self.label_108.setText(QCoreApplication.translate("navigation", u"\u70b9\u51fb\u6b21\u6570\uff1a", None))
        self.label_110.setText(QCoreApplication.translate("navigation", u"\u70b9\u51fb\u65f6\u95f4\u95f4\u9694\uff1a", None))
        self.groupBox_63.setTitle(QCoreApplication.translate("navigation", u"\u9f20\u6807\u70b9\u51fb\u65f6\u540c\u65f6\u6309\u4e0b\uff1a", None))
        self.label_162.setText(QCoreApplication.translate("navigation", u"\u6309\u952e\uff1a", None))
        self.comboBox_66.setItemText(0, QCoreApplication.translate("navigation", u"ctrl", None))
        self.comboBox_66.setItemText(1, QCoreApplication.translate("navigation", u"alt", None))
        self.comboBox_66.setItemText(2, QCoreApplication.translate("navigation", u"shift", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_9), QCoreApplication.translate("navigation", u"\u9f20\u6807\u70b9\u51fb", None))
        self.label_88.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0\u3002", None))
        self.groupBox.setTitle(QCoreApplication.translate("navigation", u"\u65f6\u95f4\u7b49\u5f85", None))
        self.label_14.setText(QCoreApplication.translate("navigation", u"\u7b49\u5f85\u65f6\u957f\uff1a", None))
        self.comboBox_25.setItemText(0, QCoreApplication.translate("navigation", u"\u79d2", None))
        self.comboBox_25.setItemText(1, QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.comboBox_25.setItemText(2, QCoreApplication.translate("navigation", u"\u5206\u949f", None))

        self.groupBox_16.setTitle(QCoreApplication.translate("navigation", u"\u968f\u673a\u7b49\u5f85", None))
        self.label_78.setText(QCoreApplication.translate("navigation", u"\u6700\u5c0f\u65f6\u95f4\uff1a", None))
        self.comboBox_64.setItemText(0, QCoreApplication.translate("navigation", u"\u79d2", None))
        self.comboBox_64.setItemText(1, QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.comboBox_64.setItemText(2, QCoreApplication.translate("navigation", u"\u5206\u949f", None))

        self.label_79.setText(QCoreApplication.translate("navigation", u"\u6700\u5927\u65f6\u95f4\uff1a", None))
        self.comboBox_65.setItemText(0, QCoreApplication.translate("navigation", u"\u79d2", None))
        self.comboBox_65.setItemText(1, QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.comboBox_65.setItemText(2, QCoreApplication.translate("navigation", u"\u5206\u949f", None))

        self.groupBox_15.setTitle(QCoreApplication.translate("navigation", u"\u5b9a\u65f6\u7b49\u5f85", None))
        self.label_15.setText(QCoreApplication.translate("navigation", u"\u7b49\u5f85\u81f3\u6307\u5b9a\u65f6\u95f4\uff1a", None))
        self.timeEdit.setDisplayFormat(QCoreApplication.translate("navigation", u"HH:mm:ss", None))
        self.label_26.setText(QCoreApplication.translate("navigation", u"\u65f6\u95f4\u68c0\u6d4b\u9891\u7387\uff08\u6beb\u79d2\uff09\uff1a", None))
        self.comboBox_6.setItemText(0, QCoreApplication.translate("navigation", u"1000", None))
        self.comboBox_6.setItemText(1, QCoreApplication.translate("navigation", u"500", None))
        self.comboBox_6.setItemText(2, QCoreApplication.translate("navigation", u"200", None))
        self.comboBox_6.setItemText(3, QCoreApplication.translate("navigation", u"100", None))
        self.comboBox_6.setItemText(4, QCoreApplication.translate("navigation", u"50", None))
        self.comboBox_6.setItemText(5, QCoreApplication.translate("navigation", u"10", None))

        self.comboBox_6.setCurrentText(QCoreApplication.translate("navigation", u"1000", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("navigation", u"\u65f6\u95f4\u7b49\u5f85", None))
        self.label_89.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0\u3002", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u7b49\u5f85", None))
        self.pushButton_21.setText(QCoreApplication.translate("navigation", u"\u5feb\u6377\u622a\u56fe", None))
        self.pushButton_22.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u8d44\u6e90\u6587\u4ef6\u5939", None))
        self.label_46.setText(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u540d\u79f0\uff1a", None))
        self.comboBox_19.setItemText(0, QCoreApplication.translate("navigation", u"\u7b49\u5f85\u5230\u6307\u5b9a\u56fe\u50cf\u51fa\u73b0", None))
        self.comboBox_19.setItemText(1, QCoreApplication.translate("navigation", u"\u7b49\u5f85\u5230\u6307\u5b9a\u56fe\u50cf\u6d88\u5931", None))

        self.label_48.setText(QCoreApplication.translate("navigation", u"\u8d85\u65f6\u62a5\u9519\u79d2\u6570\uff1a", None))
        self.label_45.setText(QCoreApplication.translate("navigation", u"\u6587\u4ef6\u5939\u540d\u79f0", None))
        self.label_47.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u540d\u79f0\uff1a", None))
        self.groupBox_79.setTitle(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u8bc6\u522b\u7cbe\u5ea6", None))
        self.label_182.setText(QCoreApplication.translate("navigation", u"0%", None))
        self.label_183.setText(QCoreApplication.translate("navigation", u"\u8bc6\u522b\u7cbe\u5ea6\uff1a", None))
        self.groupBox_61.setTitle(QCoreApplication.translate("navigation", u"\u542f\u7528\u6307\u5b9a\u533a\u57df\u8bc6\u522b", None))
        self.label_160.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_54.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u533a\u57df", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_19), QCoreApplication.translate("navigation", u"\u56fe\u50cf\u7b49\u5f85", None))
        self.label_165.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u5f53\u5305\u542b\u6307\u5b9a\u6807\u9898\u5185\u5bb9\u7684\u5e94\u7528\u7a97\u53e3\u83b7\u53d6\u5230\u7126\u70b9\uff0c\u5219\u7ed3\u675f\u7b49\u5f85\u3002", None))
        self.groupBox_70.setTitle(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u7126\u70b9\u7b49\u5f85", None))
        self.label_20.setText(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u6807\u9898\u5305\u542b\uff1a", None))
        self.label_169.setText(QCoreApplication.translate("navigation", u"\u6beb\u79d2", None))
        self.label_170.setText(QCoreApplication.translate("navigation", u"\u6700\u5927\u7b49\u5f85\u65f6\u957f\uff1a", None))
        self.label_168.setText(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u68c0\u6d4b\u9891\u7387\uff1a", None))
        self.label_171.setText(QCoreApplication.translate("navigation", u"\u79d2", None))
        self.comboBox_68.setItemText(0, QCoreApplication.translate("navigation", u"1000", None))
        self.comboBox_68.setItemText(1, QCoreApplication.translate("navigation", u"500", None))
        self.comboBox_68.setItemText(2, QCoreApplication.translate("navigation", u"200", None))
        self.comboBox_68.setItemText(3, QCoreApplication.translate("navigation", u"100", None))
        self.comboBox_68.setItemText(4, QCoreApplication.translate("navigation", u"50", None))

        self.label_166.setText(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u7b49\u5f85\u7c7b\u578b\uff1a", None))
        self.comboBox_69.setItemText(0, QCoreApplication.translate("navigation", u"\u7b49\u5f85\u7a97\u53e3\u83b7\u53d6\u7126\u70b9", None))
        self.comboBox_69.setItemText(1, QCoreApplication.translate("navigation", u"\u7b49\u5f85\u7a97\u53e3\u5931\u53bb\u7126\u70b9", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_42), QCoreApplication.translate("navigation", u"\u7a97\u53e3\u7126\u70b9\u7b49\u5f85", None))
        self.groupBox_44.setTitle(QCoreApplication.translate("navigation", u"\u4eceExcel\u5355\u5143\u683c\u83b7\u53d6\u5185\u5bb9", None))
        self.label_136.setText(QCoreApplication.translate("navigation", u"Excel\u5de5\u4f5c\u7c3f\u540d\u79f0\uff1a", None))
        self.label_137.setText(QCoreApplication.translate("navigation", u"\u5de5\u4f5c\u8868\u540d\uff1a", None))
        self.label_138.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\uff1a", None))
        self.lineEdit_23.setPlaceholderText(QCoreApplication.translate("navigation", u"\u5982\uff1aA1\u3001B2...", None))
        self.checkBox_9.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\u884c\u53f7\u81ea\u52a8\u9012\u589e", None))
        self.pushButton_29.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u5de5\u4f5c\u7c3f", None))
        self.groupBox_45.setTitle(QCoreApplication.translate("navigation", u"\u5199\u5165\u53d8\u91cf", None))
        self.label_139.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_35.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_36.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_23), QCoreApplication.translate("navigation", u"\u83b7\u53d6Excel", None))
        self.label_90.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0\u3002", None))
        self.groupBox_22.setTitle(QCoreApplication.translate("navigation", u"\u6ed1\u8f6e\u6eda\u52a8", None))
        self.label_17.setText(QCoreApplication.translate("navigation", u"\u6eda\u52a8\u8ddd\u79bb\uff1a", None))
        self.label_16.setText(QCoreApplication.translate("navigation", u"\u6eda\u52a8\u65b9\u5411\uff1a", None))
        self.label_105.setText(QCoreApplication.translate("navigation", u"\u50cf\u7d20", None))
        self.comboBox_5.setItemText(0, QCoreApplication.translate("navigation", u"\u2191", None))
        self.comboBox_5.setItemText(1, QCoreApplication.translate("navigation", u"\u2193", None))

        self.groupBox_29.setTitle(QCoreApplication.translate("navigation", u"\u968f\u673a\u6eda\u52a8", None))
        self.label_103.setText(QCoreApplication.translate("navigation", u"\u6700\u5927\u8ddd\u79bb\uff1a", None))
        self.label_101.setText(QCoreApplication.translate("navigation", u"\u6700\u5c0f\u8ddd\u79bb\uff1a", None))
        self.label_104.setText(QCoreApplication.translate("navigation", u"\u50cf\u7d20", None))
        self.label_106.setText(QCoreApplication.translate("navigation", u"\u50cf\u7d20", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("navigation", u"\u6eda\u8f6e\u6ed1\u52a8", None))
        self.checkBox_2.setText(QCoreApplication.translate("navigation", u"\u6a21\u62df\u624b\u52a8\u8f93\u5165", None))
        self.label_91.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0\u3002", None))
        self.pushButton_28.setText(QCoreApplication.translate("navigation", u"\u63d2\u5165\u53d8\u91cf", None))
        self.label_18.setText(QCoreApplication.translate("navigation", u"\u6587\u672c\u5185\u5bb9\uff1a", None))
        self.textEdit.setHtml(QCoreApplication.translate("navigation", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'\u5fae\u8f6f\u96c5\u9ed1'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'\u9ed1\u4f53,\u9ed1\u4f53';\"><br /></p></body></html>", None))
        self.textEdit.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8bf7\u8f93\u5165\u6587\u672c......", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("navigation", u"\u6587\u672c\u8f93\u5165", None))
        self.label_24.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u5728\u8f93\u5165\u6846\u4e2d\u6309\u4e0b\u5bf9\u5e94\u7684\u6309\u952e\u3002", None))
        self.groupBox_65.setTitle(QCoreApplication.translate("navigation", u"\u6309\u4e0b\u6309\u952e\uff1a", None))
        self.label_163.setText(QCoreApplication.translate("navigation", u"\u6309\u952e\u540d\u79f0\uff1a", None))
        self.label_167.setText(QCoreApplication.translate("navigation", u"\u6309\u538b\u65f6\u957f\uff08\u6beb\u79d2\uff09\uff1a", None))
        self.groupBox_80.setTitle(QCoreApplication.translate("navigation", u"\u7ec4\u5408\u952e\u5931\u6548\u7684\u89e3\u51b3\u65b9\u6cd5\uff1a", None))
        self.label_179.setText(QCoreApplication.translate("navigation", u"1\u3001\u4f7f\u7528\u201c\u8fd0\u884cPython\u201d\u6307\u4ee4\u3002", None))
        self.label_186.setText(QCoreApplication.translate("navigation", u"2\u3001", None))
        self.pushButton_77.setText(QCoreApplication.translate("navigation", u"\u6267\u884c\u65b9\u6cd5\u4e00", None))
        self.pushButton_78.setText(QCoreApplication.translate("navigation", u"\u6267\u884c\u65b9\u6cd5\u4e8c", None))
        self.label_185.setText(QCoreApplication.translate("navigation", u"3\u3001\u5c06\u4ee3\u7801\u4e2d\u7684\u7ec4\u5408\u952e\u66ff\u6362\u3002", None))
        self.label_184.setText(QCoreApplication.translate("navigation", u"4\u3001\u6dfb\u52a0\u547d\u4ee4\u5373\u53ef\u3002", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), QCoreApplication.translate("navigation", u"\u6309\u4e0b\u952e\u76d8", None))
        self.label_30.setText(QCoreApplication.translate("navigation", u"\u91cd\u8981\u63d0\u793a\uff1a\u5f53\u9009\u62e9\u6b64\u6307\u4ee4\u65f6\uff0c\u8bf7\u5728\u4e3b\u754c\u9762\u4e2d\u6253\u5f00\u201c\u65e0\u9650\u5faa\u73af\u201d\u529f\u80fd\u3002", None))
        self.groupBox_23.setTitle(QCoreApplication.translate("navigation", u"\u6309\u4e0b\u9f20\u6807\u4e2d\u952e\u89e6\u53d1\uff1a", None))
        self.label_27.setText(QCoreApplication.translate("navigation", u"\u5f53\u9f20\u6807\u4e2d\u952e\u6309\u4e0b\u65f6\uff0c\u6a21\u62df\u9f20\u6807\u5de6\u952e\u70b9\u51fb", None))
        self.label_28.setText(QCoreApplication.translate("navigation", u"\u6b21", None))
        self.radioButton_zi.setText(QCoreApplication.translate("navigation", u"\u7ed3\u675f\u7b49\u5f85\uff1a", None))
        self.label_29.setText(QCoreApplication.translate("navigation", u"\u5f53\u9f20\u6807\u4e2d\u952e\u6309\u4e0b\u65f6\uff0c\u81ea\u52a8\u6267\u884c\u8be5\u6307\u4ee4\u540e\u7684\u6240\u6709\u6307\u4ee4", None))
        self.radioButton.setText(QCoreApplication.translate("navigation", u"\u6a21\u62df\u70b9\u51fb\uff1a", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_8), QCoreApplication.translate("navigation", u"\u4e2d\u952e\u6fc0\u6d3b", None))
        self.label_67.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6309\u4e0b\u83b7\u53d6\u5750\u6807\u6309\u94ae\u5e76\u62d6\u52a8\u9f20\u6807\uff0c\u5373\u53ef\u663e\u793a\u9f20\u6807\u5f53\u524d\u7684\u4f4d\u7f6e\u3002", None))
        self.groupBox_64.setTitle(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u5750\u6807\uff1a", None))
        self.label_57.setText(QCoreApplication.translate("navigation", u"\u5f00\u59cb\u4f4d\u7f6e\uff1a", None))
        self.pushButton_12.setText(QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5750\u6807\uff08\u6309\u4f4f\u62d6\u52a8\uff09", None))
        self.label_58.setText(QCoreApplication.translate("navigation", u"X", None))
        self.label_59.setText(QCoreApplication.translate("navigation", u"0", None))
        self.label_61.setText(QCoreApplication.translate("navigation", u"0", None))
        self.label_60.setText(QCoreApplication.translate("navigation", u"Y", None))
        self.pushButton_13.setText(QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5750\u6807\uff08\u6309\u4f4f\u62d6\u52a8\uff09", None))
        self.label_64.setText(QCoreApplication.translate("navigation", u"Y", None))
        self.label_63.setText(QCoreApplication.translate("navigation", u"X", None))
        self.label_62.setText(QCoreApplication.translate("navigation", u"\u7ed3\u675f\u4f4d\u7f6e\uff1a", None))
        self.label_66.setText(QCoreApplication.translate("navigation", u"0", None))
        self.label_65.setText(QCoreApplication.translate("navigation", u"0", None))
        self.checkBox_8.setText(QCoreApplication.translate("navigation", u"\u5f00\u59cb\u4f7f\u7528\u968f\u673a\u4f4d\u7f6e", None))
        self.checkBox_7.setText(QCoreApplication.translate("navigation", u"\u7ed3\u675f\u4f7f\u7528\u968f\u673a\u4f4d\u7f6e", None))
        self.label_199.setText(QCoreApplication.translate("navigation", u"\u9f20\u6807\u79fb\u52a8\u901f\u5ea6\uff1a", None))
        self.label_200.setText(QCoreApplication.translate("navigation", u"\u6beb\u79d2ms", None))
        self.groupBox_84.setTitle(QCoreApplication.translate("navigation", u"\u4f7f\u7528\u53d8\u91cf\u5750\u6807\uff1a", None))
        self.pushButton_83.setText(QCoreApplication.translate("navigation", u"\u67e5\u770b\u793a\u4f8b", None))
        self.pushButton_14.setText(QCoreApplication.translate("navigation", u"\u62d6\u62fd\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_14), QCoreApplication.translate("navigation", u"\u9f20\u6807\u62d6\u62fd", None))
        self.label_92.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u5c06Excel\u8868\u4e2d\u7684\u503c\u586b\u5165\u5230\u5bf9\u5e94\u7684\u56fe\u50cf\u7a97\u53e3\u63a7\u4ef6\u4e2d\u3002", None))
        self.pushButton_5.setText(QCoreApplication.translate("navigation", u"\u5feb\u6377\u622a\u56fe", None))
        self.pushButton_8.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u8d44\u6e90\u6587\u4ef6\u5939", None))
        self.groupBox_67.setTitle(QCoreApplication.translate("navigation", u"Excel\u5de5\u4f5c\u7c3f\uff1a", None))
        self.label_37.setText(QCoreApplication.translate("navigation", u"Excel\u5de5\u4f5c\u7c3f\u540d\u79f0\uff1a", None))
        self.label_38.setText(QCoreApplication.translate("navigation", u"\u5de5\u4f5c\u8868\u540d\uff1a", None))
        self.label_39.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\uff1a", None))
        self.lineEdit_4.setPlaceholderText(QCoreApplication.translate("navigation", u"\u5982\uff1aA1\u3001B2...", None))
        self.groupBox_66.setTitle(QCoreApplication.translate("navigation", u"\u76ee\u6807\u63a7\u4ef6\u56fe\u50cf\uff1a", None))
        self.label_40.setText(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u6587\u4ef6\u5939\u8def\u5f84\uff1a", None))
        self.label_41.setText(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u540d\u79f0\uff1a", None))
        self.checkBox_3.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\u884c\u53f7\u81ea\u52a8\u9012\u589e", None))
        self.checkBox_4.setText(QCoreApplication.translate("navigation", u"\u6a21\u62df\u624b\u52a8\u8f93\u5165", None))
        self.groupBox_24.setTitle(QCoreApplication.translate("navigation", u"\u62a5\u9519\u5904\u7406", None))
        self.radioButton_5.setText(QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u56fe\u7247\u8d85\u65f6\u62a5\u9519", None))
        self.label_44.setText(QCoreApplication.translate("navigation", u"\u79d2\u6570\uff1a", None))
        self.radioButton_3.setText(QCoreApplication.translate("navigation", u"\u5339\u914d\u4e0d\u5230\u6307\u5b9a\u56fe\u50cf\u65f6\u81ea\u52a8\u7565\u8fc7\u8be5\u6307\u4ee4", None))
        self.pushButton_58.setText(QCoreApplication.translate("navigation", u"\u627e\u56fe\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_10), QCoreApplication.translate("navigation", u"\u4fe1\u606f\u5f55\u5165", None))
        self.label_97.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u6682\u65e0", None))
        self.groupBox_19.setTitle(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u9a8c\u8bc1\u7801\u622a\u56fe\u4f4d\u7f6e\uff1a", None))
        self.label_85.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_16.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u8bc6\u522b\u4f4d\u7f6e", None))
        self.groupBox_60.setTitle(QCoreApplication.translate("navigation", u"\u9a8c\u8bc1\u7801\u7c7b\u578b\uff1a", None))
        self.comboBox_62.setItemText(0, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u82f11-4\u4f4d", None))
        self.comboBox_62.setItemText(1, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u82f15-8\u4f4d", None))
        self.comboBox_62.setItemText(2, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u82f19~11\u4f4d", None))
        self.comboBox_62.setItemText(3, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u82f112\u4f4d\u53ca\u4ee5\u4e0a", None))
        self.comboBox_62.setItemText(4, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u82f11~6\u4f4dplus", None))
        self.comboBox_62.setItemText(5, QCoreApplication.translate("navigation", u"\u5b9a\u5236-\u6570\u82f15\u4f4d~qcs", None))
        self.comboBox_62.setItemText(6, QCoreApplication.translate("navigation", u"\u901a\u7528\u4e2d\u6587\u5b57\u7b261~2\u4f4d", None))
        self.comboBox_62.setItemText(7, QCoreApplication.translate("navigation", u"\u901a\u7528\u4e2d\u6587\u5b57\u7b26 3~5\u4f4d", None))
        self.comboBox_62.setItemText(8, QCoreApplication.translate("navigation", u"\u901a\u7528\u4e2d\u6587\u5b57\u7b266~8\u4f4d", None))
        self.comboBox_62.setItemText(9, QCoreApplication.translate("navigation", u"\u901a\u7528\u4e2d\u6587\u5b57\u7b269\u4f4d\u53ca\u4ee5\u4e0a", None))
        self.comboBox_62.setItemText(10, QCoreApplication.translate("navigation", u"\u901a\u7528\u6570\u5b57\u8ba1\u7b97\u9898", None))
        self.comboBox_62.setItemText(11, QCoreApplication.translate("navigation", u"\u901a\u7528\u4e2d\u6587\u8ba1\u7b97\u9898", None))

        self.groupBox_62.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u8bc6\u522b\u7ed3\u679c\u5199\u5165\u53d8\u91cf\uff1a", None))
        self.label_161.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_55.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_53.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6eToken", None))
        self.pushButton_17.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_25), QCoreApplication.translate("navigation", u"\u6570\u5b57\u9a8c\u8bc1\u7801", None))
        self.label_99.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u622a\u56fe\u5f53\u524d\u5c4f\u5e55\u3002", None))
        self.groupBox_68.setTitle(QCoreApplication.translate("navigation", u"\u622a\u56fe\u533a\u57df", None))
        self.label_19.setText(QCoreApplication.translate("navigation", u"\u622a\u56fe\u7c7b\u578b\uff1a", None))
        self.comboBox_67.setItemText(0, QCoreApplication.translate("navigation", u"\u5168\u5c4f\u622a\u56fe", None))
        self.comboBox_67.setItemText(1, QCoreApplication.translate("navigation", u"\u533a\u57df\u622a\u56fe", None))

        self.label_164.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_60.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u533a\u57df", None))
        self.groupBox_69.setTitle(QCoreApplication.translate("navigation", u"\u622a\u56fe\u540e\uff0c\u5c06\u56fe\u50cf", None))
        self.radioButton_9.setText(QCoreApplication.translate("navigation", u"\u4fdd\u5b58\u5230\u8def\u5f84", None))
        self.radioButton_8.setText(QCoreApplication.translate("navigation", u"\u5199\u5165\u526a\u5207\u677f", None))
        self.groupBox_14.setTitle(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u4fdd\u5b58\u8def\u5f84", None))
        self.label_76.setText(QCoreApplication.translate("navigation", u"\u6587\u4ef6\u5939\u540d\u79f0:", None))
        self.label_77.setText(QCoreApplication.translate("navigation", u"\u56fe\u50cf\u540d\u79f0\uff1a", None))
        self.pushButton_62.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u6587\u4ef6\u5939", None))
        self.pushButton_61.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_17), QCoreApplication.translate("navigation", u"\u5c4f\u5e55\u622a\u56fe", None))
        self.groupBox_32.setTitle(QCoreApplication.translate("navigation", u"\u64ad\u653e\u97f3\u9891\u4fe1\u53f7", None))
        self.label_116.setText(QCoreApplication.translate("navigation", u"\u95f4\u9694\u65f6\u95f4\uff08\u6beb\u79d2\uff09\uff1a", None))
        self.label_112.setText(QCoreApplication.translate("navigation", u"\u9891\u7387\uff1a", None))
        self.label_114.setText(QCoreApplication.translate("navigation", u"\u6301\u7eed\u65f6\u95f4\uff08\u6beb\u79d2\uff09\uff1a", None))
        self.label_113.setText(QCoreApplication.translate("navigation", u"\u64ad\u653e\u6b21\u6570\uff1a", None))
        self.groupBox_33.setTitle(QCoreApplication.translate("navigation", u"\u64ad\u653e\u63d0\u793a\u97f3", None))
        self.label_115.setText(QCoreApplication.translate("navigation", u"\u63d0\u793a\u97f3\u7c7b\u578b\uff1a", None))
        self.comboBox_7.setItemText(0, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u8b66\u544a", None))
        self.comboBox_7.setItemText(1, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u9519\u8bef", None))
        self.comboBox_7.setItemText(2, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u8be2\u95ee", None))
        self.comboBox_7.setItemText(3, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u4fe1\u606f", None))
        self.comboBox_7.setItemText(4, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u542f\u52a8", None))
        self.comboBox_7.setItemText(5, QCoreApplication.translate("navigation", u"\u7cfb\u7edf\u5173\u95ed", None))

        self.groupBox_34.setTitle(QCoreApplication.translate("navigation", u"\u64ad\u653e\u8bed\u97f3", None))
        self.textEdit_4.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u64ad\u653e\u7684\u8bed\u97f3\uff0c\u4f8b\u5982\uff1a\u8bf7\u6c42\u4eba\u5de5\u63a5\u7ba1......", None))
        self.label_117.setText(QCoreApplication.translate("navigation", u"\u8bed\u901f\uff1a", None))
        self.label_118.setText(QCoreApplication.translate("navigation", u"200", None))
        self.pushButton_32.setText(QCoreApplication.translate("navigation", u"\u63d2\u5165\u53d8\u91cf", None))
        self.pushButton_24.setText(QCoreApplication.translate("navigation", u"\u64ad\u653e\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("navigation", u"\u63d0\u793a\u97f3", None))
        self.groupBox_35.setTitle(QCoreApplication.translate("navigation", u"\u5f39\u51fa\u5012\u8ba1\u65f6\u7a97\u53e3", None))
        self.label_119.setText(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u6807\u9898\uff1a", None))
        self.lineEdit_2.setText("")
        self.lineEdit_2.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8bf7\u8f93\u5165\u7a97\u53e3\u6807\u9898...", None))
        self.label_120.setText(QCoreApplication.translate("navigation", u"\u63d0\u793a\u4fe1\u606f\uff1a", None))
        self.lineEdit_6.setText("")
        self.lineEdit_6.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8bf7\u8f93\u5165\u63d0\u793a\u4fe1\u606f...", None))
        self.label_121.setText(QCoreApplication.translate("navigation", u"\u7b49\u5f85\u65f6\u95f4\uff1a", None))
        self.label_122.setText(QCoreApplication.translate("navigation", u"\u79d2", None))
        self.pushButton_25.setText(QCoreApplication.translate("navigation", u"\u663e\u793a\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_28), QCoreApplication.translate("navigation", u"\u5012\u8ba1\u65f6\u7a97\u53e3", None))
        self.groupBox_39.setTitle(QCoreApplication.translate("navigation", u"\u4efb\u52a1\u680f\u5e94\u7528\u63a7\u5236", None))
        self.label_130.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u7c7b\u578b\uff1a", None))
        self.comboBox_40.setItemText(0, QCoreApplication.translate("navigation", u"\u663e\u793a\u7a97\u53e3", None))
        self.comboBox_40.setItemText(1, QCoreApplication.translate("navigation", u"\u5173\u95ed\u7a97\u53e3", None))
        self.comboBox_40.setItemText(2, QCoreApplication.translate("navigation", u"\u6700\u5927\u5316", None))
        self.comboBox_40.setItemText(3, QCoreApplication.translate("navigation", u"\u6700\u5c0f\u5316", None))

        self.lineEdit_21.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8bf7\u8f93\u5165\u5e94\u7528\u7a0b\u5e8f\u7684\u5305\u542b\u7684\u7a97\u53e3\u6807\u9898...", None))
        self.label_129.setText(QCoreApplication.translate("navigation", u"\u7a97\u53e3\u6807\u9898\uff08\u5305\u542b\uff09\uff1a", None))
        self.checkBox_5.setText(QCoreApplication.translate("navigation", u"\u5982\u679c\u672a\u627e\u5230\u7a97\u53e3\u5219\u62a5\u9519", None))
        self.pushButton_27.setText(QCoreApplication.translate("navigation", u"\u63a7\u5236\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_32), QCoreApplication.translate("navigation", u"\u7a97\u53e3\u63a7\u5236", None))
        self.groupBox_36.setTitle(QCoreApplication.translate("navigation", u"\u5f39\u51fa\u63d0\u793a\u6846\uff1a", None))
        self.label_123.setText(QCoreApplication.translate("navigation", u"\u5bf9\u8bdd\u6846\u6807\u9898\uff1a", None))
        self.lineEdit_8.setText("")
        self.lineEdit_8.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u6807\u9898...", None))
        self.label_125.setText(QCoreApplication.translate("navigation", u"\u56fe\u6807\u7c7b\u578b\uff1a", None))
        self.comboBox_36.setItemText(0, QCoreApplication.translate("navigation", u"STOP", None))
        self.comboBox_36.setItemText(1, QCoreApplication.translate("navigation", u"WARNING", None))
        self.comboBox_36.setItemText(2, QCoreApplication.translate("navigation", u"INFO", None))
        self.comboBox_36.setItemText(3, QCoreApplication.translate("navigation", u"QUESTION", None))

        self.label_124.setText(QCoreApplication.translate("navigation", u"\u5bf9\u8bdd\u6846\u5185\u5bb9\uff1a", None))
        self.lineEdit_20.setText("")
        self.lineEdit_20.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u63d0\u793a\u4fe1\u606f...", None))
        self.pushButton_26.setText(QCoreApplication.translate("navigation", u"\u5bf9\u8bdd\u6846\u9884\u89c8", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_29), QCoreApplication.translate("navigation", u"\u63d0\u793a\u7a97\u53e3", None))
        self.groupBox_38.setTitle(QCoreApplication.translate("navigation", u"\u7ec8\u6b62\u6d41\u7a0b", None))
        self.label_128.setText(QCoreApplication.translate("navigation", u"\u6d41\u7a0b\u7c7b\u578b\uff1a", None))
        self.comboBox_39.setItemText(0, QCoreApplication.translate("navigation", u"\u7ec8\u6b62\u6240\u6709\u4efb\u52a1", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_31), QCoreApplication.translate("navigation", u"\u7ec8\u6b62\u6d41\u7a0b", None))
        self.groupBox_42.setTitle(QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5f53\u524d\u65f6\u95f4\uff1a", None))
        self.label_134.setText(QCoreApplication.translate("navigation", u"\u65f6\u95f4\u683c\u5f0f\uff1a", None))
        self.comboBox_43.setItemText(0, QCoreApplication.translate("navigation", u"\u5e74-\u6708-\u65e5 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.comboBox_43.setItemText(1, QCoreApplication.translate("navigation", u"\u5e74/\u6708/\u65e5 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.comboBox_43.setItemText(2, QCoreApplication.translate("navigation", u"\u6708/\u65e5/\u5e74 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.comboBox_43.setItemText(3, QCoreApplication.translate("navigation", u"\u65e5-\u6708-\u5e74 \u5c0f\u65f6:\u5206\u949f:\u79d2", None))
        self.comboBox_43.setItemText(4, QCoreApplication.translate("navigation", u"\u5e74-\u6708-\u65e5", None))
        self.comboBox_43.setItemText(5, QCoreApplication.translate("navigation", u"\u6708/\u65e5/\u5e74", None))
        self.comboBox_43.setItemText(6, QCoreApplication.translate("navigation", u"\u65e5-\u6708-\u5e74", None))
        self.comboBox_43.setItemText(7, QCoreApplication.translate("navigation", u"\u6708/\u5e74", None))
        self.comboBox_43.setItemText(8, QCoreApplication.translate("navigation", u"\u65f6\u95f4\u6233", None))

        self.groupBox_43.setTitle(QCoreApplication.translate("navigation", u"\u5199\u5165\u53d8\u91cf\uff1a", None))
        self.label_135.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_33.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_34.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_34), QCoreApplication.translate("navigation", u"\u83b7\u53d6\u65f6\u95f4", None))
        self.label_159.setText(QCoreApplication.translate("navigation", u"\u64cd\u4f5c\u8bf4\u660e\uff1a\u4e0e\u201c\u79fb\u52a8\u9f20\u6807\u201d\u6307\u4ee4\u642d\u914d\u4f7f\u7528\u3002", None))
        self.groupBox_58.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u5f53\u524d\u9f20\u6807\u4f4d\u7f6e\u5199\u5165\u53d8\u91cf", None))
        self.label_156.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_51.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_41), QCoreApplication.translate("navigation", u"\u83b7\u53d6\u9f20\u6807\u4f4d\u7f6e", None))
        self.groupBox_40.setTitle(QCoreApplication.translate("navigation", u"\u6309\u952e\u540d\u79f0", None))
        self.label_131.setText(QCoreApplication.translate("navigation", u"\u6309\u952e\uff1a", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_33), QCoreApplication.translate("navigation", u"\u6309\u952e\u7b49\u5f85", None))
        self.groupBox_47.setTitle(QCoreApplication.translate("navigation", u"\u5f39\u51fa\u8f93\u5165\u5bf9\u8bdd\u6846\u6846\uff1a", None))
        self.label_141.setText(QCoreApplication.translate("navigation", u"\u5bf9\u8bdd\u6846\u6807\u9898\uff1a", None))
        self.lineEdit_24.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u6807\u9898...", None))
        self.label_142.setText(QCoreApplication.translate("navigation", u"\u63d0\u793a\u4fe1\u606f\uff1a", None))
        self.lineEdit_25.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u63d0\u793a\u4fe1\u606f...", None))
        self.groupBox_46.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u8f93\u5165\u6846\u4e2d\u7684\u503c\u5199\u5165\u5230\u53d8\u91cf\uff1a", None))
        self.label_140.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_37.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_35), QCoreApplication.translate("navigation", u"\u83b7\u53d6\u5bf9\u8bdd\u6846", None))
        self.groupBox_76.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u526a\u5207\u677f\u4e2d\u7684\u503c\u5199\u5165\u5230\u53d8\u91cf\uff1a", None))
        self.label_175.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_74.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_75.setText(QCoreApplication.translate("navigation", u"\u8fd0\u884c\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_45), QCoreApplication.translate("navigation", u"\u83b7\u53d6\u526a\u5207\u677f", None))
        self.groupBox_51.setTitle(QCoreApplication.translate("navigation", u"\u6267\u884c\u4ee3\u7801", None))
        self.textEdit_5.setHtml(QCoreApplication.translate("navigation", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cascadia Code'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Cascadia Code,\u5fae\u8f6f\u96c5\u9ed1,\u5fae\u8f6f\u96c5\u9ed1';\"><br /></p></body></html>", None))
        self.textEdit_5.setPlaceholderText(QCoreApplication.translate("navigation", u"\u6267\u884cpythond\u4ee3\u7801...", None))
        self.pushButton_41.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_39.setText(QCoreApplication.translate("navigation", u"\u63d2\u5165\u53d8\u91cf", None))
        self.toolButton_4.setText(QCoreApplication.translate("navigation", u"...", None))
        self.groupBox_50.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u8fd4\u56de\u503c\u5199\u5165\u53d8\u91cf", None))
        self.label_147.setText(QCoreApplication.translate("navigation", u"\u4ee3\u7801\u4e2d\u7684return\u503c:", None))
        self.lineEdit_26.setPlaceholderText(QCoreApplication.translate("navigation", u"\u4ee3\u7801\u4e2d\u7684\u8fd4\u56de\u503c...", None))
        self.label_148.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0:", None))
        self.pushButton_40.setText(QCoreApplication.translate("navigation", u"\u8fd0\u884c\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_37), QCoreApplication.translate("navigation", u"\u8fd0\u884cPython", None))
        self.groupBox_72.setTitle(QCoreApplication.translate("navigation", u"\u6267\u884cCMD\u547d\u4ee4", None))
        self.textEdit_7.setHtml(QCoreApplication.translate("navigation", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cascadia Code'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Cascadia Code,\u5fae\u8f6f\u96c5\u9ed1,\u5fae\u8f6f\u96c5\u9ed1';\"><br /></p></body></html>", None))
        self.textEdit_7.setPlaceholderText(QCoreApplication.translate("navigation", u"\u6267\u884cCMD\u547d\u4ee4\u884c...", None))
        self.pushButton_70.setText(QCoreApplication.translate("navigation", u"\u63d2\u5165\u53d8\u91cf", None))
        self.pushButton_71.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.groupBox_75.setTitle(QCoreApplication.translate("navigation", u"\u5199\u5165\u5e38\u89c1\u547d\u4ee4", None))
        self.comboBox_72.setItemText(0, QCoreApplication.translate("navigation", u"\u9501\u5b9a\u5c4f\u5e55", None))
        self.comboBox_72.setItemText(1, QCoreApplication.translate("navigation", u"\u7acb\u5373\u5173\u95ed\u8ba1\u7b97\u673a", None))
        self.comboBox_72.setItemText(2, QCoreApplication.translate("navigation", u"1\u5206\u949f\u540e\u5173\u95ed\u8ba1\u7b97\u673a", None))
        self.comboBox_72.setItemText(3, QCoreApplication.translate("navigation", u"\u91cd\u542f\u8ba1\u7b97\u673a", None))
        self.comboBox_72.setItemText(4, QCoreApplication.translate("navigation", u"\u6ce8\u9500\u8d26\u6237", None))
        self.comboBox_72.setItemText(5, QCoreApplication.translate("navigation", u"\u521b\u5efa\u65b0\u76ee\u5f55", None))
        self.comboBox_72.setItemText(6, QCoreApplication.translate("navigation", u"\u5220\u9664\u76ee\u5f55", None))
        self.comboBox_72.setItemText(7, QCoreApplication.translate("navigation", u"\u7ec8\u6b62\u8fdb\u7a0b", None))
        self.comboBox_72.setItemText(8, QCoreApplication.translate("navigation", u"\u6253\u5f00\u8bb0\u4e8b\u672c", None))
        self.comboBox_72.setItemText(9, QCoreApplication.translate("navigation", u"\u6253\u5f00\u8ba1\u7b97\u5668", None))
        self.comboBox_72.setItemText(10, QCoreApplication.translate("navigation", u"\u6253\u5f00\u63a7\u5236\u9762\u677f", None))
        self.comboBox_72.setItemText(11, QCoreApplication.translate("navigation", u"\u6253\u5f00\u8d44\u6e90\u7ba1\u7406\u5668", None))

        self.pushButton_73.setText(QCoreApplication.translate("navigation", u"\u5199\u5165\u547d\u4ee4", None))
        self.pushButton_72.setText(QCoreApplication.translate("navigation", u"\u8fd0\u884c\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_44), QCoreApplication.translate("navigation", u"\u8fd0\u884ccmd", None))
        self.groupBox_52.setTitle(QCoreApplication.translate("navigation", u"\u8fd0\u884c\u5916\u90e8\u6587\u4ef6", None))
        self.label_149.setText(QCoreApplication.translate("navigation", u"\u6587\u4ef6\u8def\u5f84\uff08\u652f\u6301\u4efb\u610f\u683c\u5f0f\uff09\uff1a", None))
        self.pushButton_43.setText(QCoreApplication.translate("navigation", u"\u9009\u62e9\u6587\u4ef6", None))
        self.lineEdit_27.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u6587\u4ef6\u8def\u5f84......", None))
        self.pushButton_42.setText(QCoreApplication.translate("navigation", u"\u8fd0\u884c\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_38), QCoreApplication.translate("navigation", u"\u8fd0\u884c\u5916\u90e8\u6587\u4ef6", None))
        self.groupBox_53.setTitle(QCoreApplication.translate("navigation", u"Excel\u5355\u5143\u683c\u4f4d\u7f6e", None))
        self.label_150.setText(QCoreApplication.translate("navigation", u"Excel\u5de5\u4f5c\u7c3f\uff1a", None))
        self.label_151.setText(QCoreApplication.translate("navigation", u"\u5de5\u4f5c\u8868\u540d\uff1a", None))
        self.label_152.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\uff1a", None))
        self.lineEdit_28.setPlaceholderText(QCoreApplication.translate("navigation", u"\u5982\uff1aA1\u3001B2...", None))
        self.checkBox_10.setText(QCoreApplication.translate("navigation", u"\u5355\u5143\u683c\u884c\u53f7\u81ea\u52a8\u9012\u589e", None))
        self.pushButton_44.setText(QCoreApplication.translate("navigation", u"\u6253\u5f00\u5de5\u4f5c\u7c3f", None))
        self.groupBox_54.setTitle(QCoreApplication.translate("navigation", u"\u5199\u5165\u7684\u6587\u672c\u5185\u5bb9", None))
        self.textEdit_6.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u6587\u672c\u5185\u5bb9......", None))
        self.pushButton_45.setText(QCoreApplication.translate("navigation", u"\u63d2\u5165\u53d8\u91cf", None))
        self.pushButton_59.setText(QCoreApplication.translate("navigation", u"\u6307\u4ee4\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_39), QCoreApplication.translate("navigation", u"\u5199\u5165\u5355\u5143\u683c", None))
        self.groupBox_55.setTitle(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u5c4f\u5e55\u8bc6\u522b\u533a\u57df\uff1a", None))
        self.label_153.setText(QCoreApplication.translate("navigation", u"(0,0,0,0)", None))
        self.pushButton_46.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u622a\u56fe\u533a\u57df", None))
        self.groupBox_56.setTitle(QCoreApplication.translate("navigation", u"\u5c06\u8bc6\u522b\u7ed3\u679c\u5199\u5165\u53d8\u91cf\uff1a", None))
        self.label_154.setText(QCoreApplication.translate("navigation", u"\u53d8\u91cf\u540d\u79f0\uff1a", None))
        self.pushButton_48.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6e\u53d8\u91cf", None))
        self.pushButton_49.setText(QCoreApplication.translate("navigation", u"\u8bbe\u7f6eOCR\u4fe1\u606f", None))
        self.pushButton_47.setText(QCoreApplication.translate("navigation", u"\u8bc6\u522b\u6d4b\u8bd5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_40), QCoreApplication.translate("navigation", u"OCR\u8bc6\u522b", None))
        self.label_33.setText(QCoreApplication.translate("navigation", u"\u62a5\u9519\u540e\uff1a", None))
        self.lineEdit_5.setPlaceholderText(QCoreApplication.translate("navigation", u"\u8f93\u5165\u6307\u4ee4\u5907\u6ce8\u4fe1\u606f...", None))
        self.comboBox_9.setItemText(0, QCoreApplication.translate("navigation", u"\u63d0\u793a\u5f02\u5e38\u5e76\u6682\u505c", None))
        self.comboBox_9.setItemText(1, QCoreApplication.translate("navigation", u"\u81ea\u52a8\u8df3\u8fc7", None))
        self.comboBox_9.setItemText(2, QCoreApplication.translate("navigation", u"\u63d0\u793a\u5f02\u5e38\u5e76\u505c\u6b62", None))

        self.label_21.setText(QCoreApplication.translate("navigation", u"\u91cd\u590d\u6b21\u6570\uff1a", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_20), QCoreApplication.translate("navigation", u"\u529f\u80fd\u533a\u53c2\u6570", None))
        self.label_43.setText(QCoreApplication.translate("navigation", u"\u6682\u65e0", None))
        self.pushButton_9.setText(QCoreApplication.translate("navigation", u"\u67e5\u770b\u56fe\u50cf", None))
        self.pushButton_10.setText(QCoreApplication.translate("navigation", u"\u5220\u9664\u56fe\u50cf", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_21), QCoreApplication.translate("navigation", u"\u56fe\u50cf\u9884\u89c8", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_24), QCoreApplication.translate("navigation", u"\u6d4b\u8bd5\u65e5\u5fd7", None))
        self.pushButton_2.setText(QCoreApplication.translate("navigation", u"\u6dfb\u52a0\u6307\u4ee4", None))
        self.pushButton_3.setText(QCoreApplication.translate("navigation", u"\u53d6\u6d88", None))
    # retranslateUi

