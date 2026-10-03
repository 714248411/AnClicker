from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QMessageBox
from system_hotkey import SystemHotkey

from functions import is_hotkey_valid
from 数据库操作 import DatabaseOperation
from Window.setting_ui import Ui_Setting
from WindowControl.窗口状态 import install_window_state

BAIDU_OCR = 'https://ai.baidu.com/tech/ocr'
YUN_CODE = 'https://www.jfbym.com'


class Setting(QDialog, Ui_Setting):
    """添加设置窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化设置窗口
        self.setupUi(self)
        self.db = getattr(parent, "db", None) or DatabaseOperation()
        install_window_state(self, self.db, self.windowTitle())
        # 绑定快捷键事件
        self.main_window_open = True  # 设置窗口是否是主窗口打开，如果不是则不注册全局快捷键，并隐藏快捷键设置
        self.unregister_global_shortcut_keys()

        self.pushButton.clicked.connect(self.save_setting)  # 点击保存（应用）按钮
        self.pushButton_2.clicked.connect(lambda: self.open_link(BAIDU_OCR))  # 打开百度OCR链接
        self.pushButton_4.clicked.connect(lambda: self.open_link(YUN_CODE))  # 打开云码链接
        self.load_setting_data()  # 加载设置数据

    def unregister_global_shortcut_keys(self):
        """如果是主窗口打开，则注销全局快捷键，否则隐藏全局快捷键设置"""
        try:
            self.parent().unregister_global_shortcut_keys()  # 注销全局快捷键
        except AttributeError:
            self.main_window_open = False
            # 如果tabWidget中tab页名称为“快捷键”，则隐藏该tab页
            for i in range(self.tabWidget.count()):
                if self.tabWidget.tabText(i) == '快捷键':
                    self.tabWidget.removeTab(i)
                    break

    def save_setting_date(self):
        """保存设置数据"""

        def validate_and_set_hotkey(hotkey, key_sequence_edit_, action_):
            """验证并设置快捷键"""
            if self.main_window_open:
                key_sequence = key_sequence_edit_.keySequence().toString().lower().split('+')
                key_sequence = [key.replace('ctrl', 'control') for key in key_sequence]
                if is_hotkey_valid(hotkey, key_sequence):
                    self.db.set_global_shortcut(**{action_: key_sequence})
                else:
                    QMessageBox.information(
                        self, '提醒',
                        f'快捷键{key_sequence_edit_.keySequence().toString()}为无效按键！'
                        f'\n\n可能的原因：'
                        f'\n1.系统不支持注册的按键。'
                        f'\n2.按键已被其他程序占用。'
                    )
                    raise Exception('无效的快捷键！')

        self.db.update_settings(
            退出提醒清空指令=str(True if self.checkBox_2.isChecked() else False),
            系统提示音=str(True if self.checkBox_3.isChecked() else False),
            任务完成后显示主窗口=str(True if self.checkBox_4.isChecked() else False)
        )
        self.db.update_settings(
            appId=str(self.lineEdit.text()),
            apiKey=str(self.lineEdit_2.text()),
            secretKey=str(self.lineEdit_3.text()),
            云码Token=str(self.lineEdit_6.text())
        )

        # 更新快捷键设置，检查快捷键是否有效，无效则弹出提示
        key_mapping = {
            '开始运行': self.keySequenceEdit,
            '结束运行': self.keySequenceEdit_2,
            '暂停和恢复': self.keySequenceEdit_4
        }
        for action, key_sequence_edit in key_mapping.items():
            validate_and_set_hotkey(SystemHotkey(), key_sequence_edit, action)


    def save_setting(self):
        """保存按钮事件"""
        try:
            self.save_setting_date()
            QMessageBox.information(self, '提醒', '设置成功！')
            # 退出设置窗口
            self.close()
        except Exception as e:
            print('保存设置失败！', e)

    def load_setting_data(self):
        """加载设置数据库中的数据"""
        # 加载设置数据
        app_data_dic = self.db.get_setting_data(
            'appId',
            'apiKey',
            'secretKey',
            '云码Token'
        )
        self.checkBox_2.setChecked(self.db.get_bool_setting('退出提醒清空指令'))
        self.checkBox_3.setChecked(self.db.get_bool_setting('系统提示音'))
        self.checkBox_4.setChecked(self.db.get_bool_setting('任务完成后显示主窗口'))

        # 填入OCR API信息
        self.lineEdit.setText(app_data_dic.get('appId', ''))
        self.lineEdit_2.setText(app_data_dic.get('apiKey', ''))
        self.lineEdit_3.setText(app_data_dic.get('secretKey', ''))
        # 填入云码Token
        self.lineEdit_6.setText(app_data_dic.get('云码Token', ''))

        # 加载快捷键设置
        global_shortcut_dic = self.db.get_global_shortcut()
        self.keySequenceEdit.setKeySequence('+'.join(global_shortcut_dic['开始运行']))
        self.keySequenceEdit_2.setKeySequence('+'.join(global_shortcut_dic['结束运行']))
        self.keySequenceEdit_4.setKeySequence('+'.join(global_shortcut_dic['暂停和恢复']))

    @staticmethod
    def open_link(url):
        """打开网页"""
        QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event):
        if self.main_window_open:  # 如果是主窗口打开
            # 注册全局快捷键
            self.parent().register_global_shortcut_keys()
