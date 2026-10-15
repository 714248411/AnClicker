import sys

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QCursor
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QApplication

from WindowControl.变量池窗口 import VariablePool_Win
from 数据库操作 import DatabaseOperation
from Window.variable_selection_ui import Ui_VariableSelection
from WindowControl.窗口状态 import install_window_state


class Variable_selection_win(QDialog, Ui_VariableSelection):
    """变量选择窗口。"""

    def __init__(self, parent=None, modes='变量选择'):
        super().__init__(parent)
        self.setupUi(self)
        self.db = getattr(parent, "db", None) or DatabaseOperation()
        # self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        del modes
        self.setWindowTitle('选择变量')
        self.label.setText('请选择要插入的变量')
        self.pushButton.setText('设置变量')
        self.listView.doubleClicked.connect(self.write_to_textedit)
        self.pushButton.clicked.connect(self.show_variable_pool)
        install_window_state(
            self, self.db, self.windowTitle(), center=False, enable_maximize_button=False
        )
        self.listView.installEventFilter(self)  # 安装事件过滤器,重新设置表格的快捷键

    def load_lists(self):
        """设置初始参数"""

        def add_listview(list_, listview):
            """添加listview"""
            model = QStandardItemModel()
            listview.setModel(model)
            for item in list_:
                # item前面加上数字序号
                item = str(list_.index(item) + 1) + '. ' + item
                model.appendRow(QStandardItem(item))

        variable_list = self.db.get_variable_info('list')
        add_listview(variable_list, self.listView)

    def trigger_using_number_keys(self, number):
        """设置到对应的行"""
        if number <= self.listView.model().rowCount():
            self.listView.setCurrentIndex(self.listView.model().index(number - 1, 0))
            self.write_to_textedit()

    def write_to_textedit(self):
        """将选中的值写入textedit，用于写入变量的模式"""
        try:
            indexes = self.listView.selectedIndexes()
            value = self.listView.model().itemFromIndex(indexes[0]).text().split('. ')[1]  # 获取选中的值
            self.parent().write_value_to_textedit(value)
            self.close()
        except Exception as e:
            print(e)

    def show_variable_pool(self):
        variable_pool = VariablePool_Win(self)
        variable_pool.exec_()

    def showEvent(self, a0) -> None:
        # 移动窗口到鼠标位置
        cursor_pos = QCursor.pos()
        # 移动窗口使窗口中心与鼠标位置重合
        self.move(cursor_pos.x() - int(self.width() / 2), cursor_pos.y() - int(self.height() / 2))
        self.load_lists()

    def eventFilter(self, obj, event):
        # 重写self.tableWidget的快捷键事件
        if obj == self.listView:
            if event.type() == 6:  # 键盘按下事件
                key_to_row = {  # 数字键对应的行
                    Qt.Key.Key_1: 1,
                    Qt.Key.Key_2: 2,
                    Qt.Key.Key_3: 3,
                    Qt.Key.Key_4: 4,
                    Qt.Key.Key_5: 5,
                    Qt.Key.Key_6: 6,
                    Qt.Key.Key_7: 7,
                    Qt.Key.Key_8: 8,
                    Qt.Key.Key_9: 9,
                }
                # 检查事件的键是否在字典中
                if event.key() in key_to_row:
                    row_number = key_to_row[event.key()]
                    self.trigger_using_number_keys(row_number)  # 使用数字键触发对应的行
        return super().eventFilter(obj, event)


class ShortcutTable(QDialog):
    def __init__(self, parent=None, title=None, data=None, width=300):
        super().__init__(parent)

        # Set window title
        self.setWindowTitle("快捷键说明")
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(12)  # 调整行数，确保足够显示所有数据
        self.table.setColumnCount(2)
        if title:
            self.table.setHorizontalHeaderLabels(title)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        self.button = QtWidgets.QPushButton("我知道了")
        self.button.clicked.connect(self.close)

        if data:
            self.table.setRowCount(len(data))
            for row, (shortcut, description) in enumerate(data):
                shortcut_item = QTableWidgetItem(shortcut)
                shortcut_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                description_item = QTableWidgetItem(description)
                description_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                description_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, shortcut_item)
                self.table.setItem(row, 1, description_item)

        # Set layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # 获取表格的总高度，设置窗口的高度
        table_height = self.table.verticalHeader().length()
        self.resize(width, table_height + 150)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = Variable_selection_win()
    window.show()
    sys.exit(app.exec_())
