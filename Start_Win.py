# coding: utf-8
# Copyright (c) [2022] [federalsadler@sohu.com]
# [Clicker] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
# http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
from __future__ import print_function

import collections
import gc
import os.path
import sqlite3
import sys
import tempfile
import zipfile
from time import time as current_time
from typing import Optional

import openpyxl
from PySide6.QtCore import QTimer, Signal, Slot, QUrl, Qt
from PySide6.QtGui import QAction, QDesktopServices, QPixmapCache, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
)
from functions import EXPORTS_FOLDER, LOGS_FOLDER, RESOURCE_FOLDER, \
    create_system_hotkey, get_str_now_time, global_hotkeys_supported, \
    is_hotkey_valid, open_path
from graph_repository import WorkbookValidationError
from instruction_workspace import InstructionWorkspace
from main_work import CommandThread
from view_workspace import ViewWorkspace
from 数据库操作 import DatabaseOperation
from Window.about_ui import Ui_About
from Window.mainwindow_ui import Ui_MainWindow
from WindowControl.设置窗口 import Setting
from WindowControl.资源文件夹窗口 import Global_s
from info import CURRENT_VERSION, MAIN_WEBSITE, ISSUE_WEBSITE, ISSUE_WEBSITE_2, QQ_GROUP, QQ, \
    QQ_GROUP_OLD, QQ_OLD, QQ_CONTACTS, EMAIL_CONTACTS, CONTRIBUTORS, APP_NAME, \
    GITEE_WEBSITE_SECOND, GITHUB_WEBSITE_OLD, Github_WEBSITE, WINDOW_TITLE
from WindowControl.快捷键说明 import ShortcutTable
from WindowControl.窗口状态 import install_window_state

collections.Iterable = collections.abc.Iterable

# Compatibility alias kept for extensions/tests that replace the hotkey factory.
SystemHotkey = create_system_hotkey


# todo: 指令可编译为python代码
# todo: 可暂时禁用指令功能
# todo: win通知指令
# todo: excel指令集
# todo: 调试模式
# todo: 动作录制功能
# todo: 使用将指定标题的窗口正常显示后会出现菜单栏阴影的问题

# 用户需求
# todo: 绑定窗口指令
# todo: 快捷导入指令，拖动文件到窗口导入指令
# todo: 成功和失败改变变量值的功能
# todo: 鼠标随机移动添加区域限制
# todo: 设置窗口打开时，按全局快捷键也会触发运行
# todo: 指令可以选择执行，表格中使用checkbox控制
# todo: 指令可导出为json
# todo: 鼠标拖动可设置速度
# todo: 后台截图点击指令
# done: 命令添加窗口不能缩小
# done: 图像点击位置可设置随机范围

# https://blog.csdn.net/qq_41567921/article/details/134813496

# activate clicker

# pyinstaller --clean -y packaging\main.spec

# 指令由 instructions.registry 统一注册，主窗口与执行线程按需惰性加载。


class Main_window(QMainWindow, Ui_MainWindow):
    """主窗口"""
    clear_signal = Signal()  # 自定义信号，textEdit清空信息，防止在全局快捷键调用时程序崩溃
    shortcut_requested = Signal(str)

    def __init__(self):
        super().__init__()
        # 初始化窗体
        self.setupUi(self)
        self.merge_control_and_operation_panel()
        self.setWindowTitle(WINDOW_TITLE)
        # 窗口和信息
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)  # 实例化状态栏
        self.db = DatabaseOperation()
        self.workspace = InstructionWorkspace(self.db.db_path, self)
        self._install_instruction_workspace()
        self.view_workspace = ViewWorkspace(self)
        from recent_projects import RecentProjectPicker, ProjectDropFilter
        self.recent_project_picker = RecentProjectPicker(self.groupBox_3)
        self.gridLayout_2.addWidget(self.recent_project_picker, 3, 0, 1, 2)
        self.gridLayout_2.setRowStretch(3, 0)
        self.gridLayout_2.setRowStretch(4, 1)
        self.recent_project_picker.openRequested.connect(self.open_project_path)
        self.project_drop_filter = ProjectDropFilter(self, self.open_project_path)
        self._initial_graph_fit_pending = True
        self.tabWidget.currentChanged.connect(self._schedule_initial_graph_fit)
        self.check_file_integrity()  # 检查文件完整性
        self.add_recent_to_fileMenu()  # 将最近文件添加到菜单中
        self.pushButton.clicked.connect(self.workspace.add_selected_instruction)
        self.pushButton_3.clicked.connect(
            lambda: self.show_windows("全局")
        )  # 显示全局参数窗口
        self.actions_2.triggered.connect(lambda: self.show_windows("设置"))  # 打开设置
        self.actionabout.triggered.connect(
            lambda: self.show_windows("关于")
        )  # 打开关于窗体
        self.actionhelp.triggered.connect(
            lambda: self.show_windows("说明")
        )  # 打开使用说明
        self.actionk.triggered.connect(
            lambda: self.show_windows("快捷键说明")
        )  # 打开快捷键说明
        # 节点图导入导出
        self.actionx.triggered.connect(
            lambda: self.save_data("自动保存")
        )  # 保存指令数据
        self.actiona.triggered.connect(
            lambda: self.save_data("excel")
        )  # 导出数据，导出按钮
        self.actionf.triggered.connect(
            lambda: self.data_import("资源文件夹路径")
        )  # 导入数据
        # 主窗体开始按钮
        self.pushButton_5.clicked.connect(lambda: self.global_shortcut_key("开始线程"))
        self.start_time = None
        self.pushButton_6.clicked.connect(
            lambda: self.global_shortcut_key("终止线程")
        )  # 结束任务按钮
        self.pushButton_7.clicked.connect(
            lambda: self.global_shortcut_key("暂停和恢复线程")
        )  # 暂停和恢复按钮
        self.toolButton_8.clicked.connect(self.exporting_operation_logs)  # 导出日志按钮
        # 指令执行线程
        self.command_thread = CommandThread(self)
        self.command_thread.send_message.connect(self.send_message)
        self.command_thread.finished_signal.connect(self.thread_finished)
        self.command_thread.finished.connect(self._runtime_finished)
        self.shortcut_requested.connect(self.global_shortcut_key, Qt.QueuedConnection)
        self._escape_registered = False
        self._escape_previous_action = None
        self.escape_stop = QShortcut(QKeySequence('Esc'), self)
        self.escape_stop.setContext(Qt.ApplicationShortcut)
        self.escape_stop.setEnabled(False)
        self.escape_stop.activated.connect(lambda: self.shortcut_requested.emit('终止线程'))
        self.command_thread.cache_cleanup_requested.connect(self.clear_runtime_cache, Qt.QueuedConnection)
        # Prevent long/infinite runs from retaining an unbounded log document.
        self.textEdit.document().setMaximumBlockCount(1500)
        self.workspace.statusMessage.connect(self.statusBar.showMessage)
        self.workspace.runSingleRequested.connect(
            lambda command_id_: self.start("单行指令", command_id_)
        )
        self.workspace.runFromRequested.connect(
            lambda command_id_: self.start("从当前行运行", command_id_)
        )
        # 设置全局快捷键,用于执行指令的终止
        self.clear_signal.connect(self.clear_textEdit)
        self.hk_stop = SystemHotkey()
        # 加载上次的节点图
        self.get_data()
        # 加载窗体初始值
        self.load_initialization()

    def showEvent(self, event_) -> None:
        """首次真正显示并完成布局后再适应节点画布。"""
        super().showEvent(event_)
        self._schedule_initial_graph_fit()

    def _schedule_initial_graph_fit(self, index_=None) -> None:
        del index_
        if self._initial_graph_fit_pending:
            QTimer.singleShot(0, self._fit_graph_when_visible)

    def _fit_graph_when_visible(self) -> None:
        if (
            self._initial_graph_fit_pending
            and self.isVisible()
            and self.tabWidget.currentWidget() is self.view_workspace.editor_page
        ):
            self.workspace.editor.view.fit_graph()
            self._initial_graph_fit_pending = False

    def merge_control_and_operation_panel(self):
        """配置 .ui 中位于右侧的统一控制与操作区。"""
        self.groupBox_3.setTitle("控制与操作")
        self.groupBox_3.setMinimumWidth(260)
        self.gridLayout_2.setRowStretch(3, 1)
        self.gridLayout_4.setColumnStretch(0, 0)
        self.gridLayout_4.setColumnStretch(1, 4)
        self.gridLayout_4.setColumnStretch(2, 1)

    def _install_instruction_workspace(self) -> None:
        """Place host-neutral palette/editor widgets into their .ui hosts."""
        palette_host_ = self.instructionPaletteHost
        palette_layout_ = palette_host_.layout() or QVBoxLayout(palette_host_)
        palette_layout_.setContentsMargins(0, 0, 0, 0)
        palette_layout_.addWidget(self.workspace.palette)

        editor_host_ = self.nodeEditorHost
        editor_layout_ = editor_host_.layout() or QVBoxLayout(editor_host_)
        editor_layout_.setContentsMargins(0, 0, 0, 0)
        editor_layout_.addWidget(self.workspace.editor)

    def load_initialization(self):
        """加载窗体初始值"""

        def check_file_integrity():
            """检查文件完整性"""
            # 检查命令集.db文件是否存在
            if not os.path.exists(self.db.db_path):
                QMessageBox.critical(
                    self, "错误", "命令集.db文件不存在！\n请重新下载软件！", QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.NoButton
                )
                sys.exit(1)

        install_window_state(
            self,
            self.db,
            self.windowTitle().split("v")[0].strip(),
        )
        check_file_integrity()  # 检查文件完整性
        # 显示工具栏
        judge = self.db.get_bool_setting("显示工具栏")
        self.toolBar.setVisible(judge)
        self.actiong.setChecked(judge)
        self.checkBox_2.setChecked(
            self.db.get_bool_setting("执行中隐藏主窗口")
        )
        # 注册全局快捷键
        self.register_global_shortcut_keys()
        # 设置状态栏信息
        self.statusBar.showMessage(
            "软件版本：{}准备就绪...".format(CURRENT_VERSION), 3000
        )

    def check_file_integrity(self):
        """检查文件完整性"""
        # 检查命令集.db文件是否存在
        if not os.path.exists(self.db.db_path):
            QMessageBox.critical(self, '致命错误', '命令集.db文件不存在！请重新下载！', QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)
            sys.exit(1)
        # 检查开屏和qss文件夹是否存在
        if not os.path.exists(os.path.join(RESOURCE_FOLDER, 'flat')):
            QMessageBox.critical(self, '致命错误', 'flat文件夹不存在！', QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)
            sys.exit(1)
        # 检查qss文件夹下是否有模型文件
        model_files = os.listdir(os.path.join(RESOURCE_FOLDER, 'flat'))
        if not any(x.endswith('.qss') for x in model_files) or not any(x.endswith('.png') for x in model_files):
            QMessageBox.critical(self, '致命错误', 'flat文件夹下没有文件！', QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)
            sys.exit(1)

    def register_global_shortcut_keys(self):
        """注册全局快捷键"""
        # 从数据库获取全局快捷键
        global_shortcut = self.db.get_global_shortcut()
        # 检查快捷键是否有效，无效则弹出提示
        try:
            global_shortcuts = {
                "开始运行": "开始线程",
                "结束运行": "终止线程",
                "暂停和恢复": "暂停和恢复线程",
            }

            for shortcut_name, action_ in global_shortcuts.items():
                # 将ctrl替换为control
                global_shortcut[shortcut_name] = [
                    key.replace("ctrl", "control") for key in global_shortcut[shortcut_name]
                ]
                if not global_hotkeys_supported(self.hk_stop):
                    continue
                if is_hotkey_valid(self.hk_stop, global_shortcut[shortcut_name]):
                    self.hk_stop.register(
                        global_shortcut[shortcut_name],
                        callback=lambda x_, action_name_=action_: self.shortcut_requested.emit(
                            action_name_
                        ),
                        overwrite=True
                    )
                else:
                    str_shortcut = "+".join(global_shortcut[shortcut_name])
                    QMessageBox.information(
                        self,
                        "提醒",
                        f"快捷键{str_shortcut}已被占用！“{shortcut_name}”的全局快捷键已失效！"
                        f"\n\n请在设置窗口中重新设置全局快捷键。",
                        QMessageBox.StandardButton.Ok,
                    )
            # 将主界面的按钮显示为快捷键；无全局后端时这些仍是操作提示。
            self.pushButton_5.setText(f"开始运行\t{'+'.join(global_shortcut['开始运行'])}".upper())
            self.pushButton_6.setText(f"结束任务\t{'+'.join(global_shortcut['结束运行'])}".upper())
            self.pushButton_7.setText(f"暂停和恢复\t{'+'.join(global_shortcut['暂停和恢复'])}".upper())
            if not global_hotkeys_supported(self.hk_stop):
                self.statusBar.showMessage(
                    "当前桌面环境不支持全局快捷键，请使用界面按钮操作。", 5000
                )
        except Exception as e:
            print(e)
            QMessageBox.critical(self, "错误", "全局快捷键已失效！", QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)

    def unregister_global_shortcut_keys(self):
        """注销全局忷键"""
        global_shortcut = self.db.get_global_shortcut()
        try:
            for shortcut_name, action_ in global_shortcut.items():
                # 将ctrl替换为control
                action_ = [key.replace("ctrl", "control") for key in action_]
                self.hk_stop.unregister(tuple(action_))
        except Exception as e:
            print(e)

    def add_recent_to_fileMenu(self):
        """将最近文件添加到菜单中"""
        recently_opened_list = self.db.get_recently_opened_file("文件列表")
        current_file_path = self.db.get_setting_value("当前文件路径")
        self.menuzv.clear()
        if hasattr(self, 'recent_project_picker'):
            self.recent_project_picker.refresh(recently_opened_list, current_file_path)
        # 将最近打开文件添加到菜单中
        if len(recently_opened_list) != 0:
            for file in recently_opened_list:
                file_action = QAction(text=file, parent=self)
                # 设置信号
                file_action.triggered.connect(
                    lambda checked, file_=file: self.open_recent_file(file_)
                )
                file_action.setCheckable(True)
                # 设置当前文件为选中状态
                if file == current_file_path:
                    file_action.setChecked(True)
                self.menuzv.addAction(file_action)
        # 关闭菜单栏
        self.menuzv.close()

    def open_recent_file(self, file_path):
        """打开最近打开的文件
        :param file_path: 文件路径"""
        recent_file = self.db.get_setting_value("当前文件路径")
        if file_path != recent_file:
            if os.path.exists(file_path):
                self.open_project_path(file_path)
            elif not os.path.exists(file_path):
                # 如果文件不存在，则删除最近打开文件列表中的文件
                self.db.remove_recently_opened_file(file_path)
                # 从菜单中删除文件
                for action in self.menuzv.actions():
                    if action.text() == file_path:
                        self.menuzv.removeAction(action)
                QMessageBox.critical(
                    self, "错误", "文件不存在！已经从最近打开文件中删除。",
                    QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
        else:
            for action in self.menuzv.actions():
                if action.text() == file_path:
                    action.setChecked(True)

    def delete_data(self):
        """删除节点画布中选中的指令。"""
        return self.workspace.remove_commands()

    def open_project_path(self, file_path):
        """One guarded entry point for recent selection, edited paths and drops."""
        thread = getattr(self, 'command_thread', None)
        if (thread is not None and thread.isRunning()) or self.view_workspace.recording_page.busy:
            self.statusBar.showMessage('请先停止任务和录制，再切换项目。', 5000)
            self.add_recent_to_fileMenu()
            return
        current = self.db.get_setting_value('当前文件路径')
        if current and os.path.normcase(os.path.abspath(file_path)) == os.path.normcase(os.path.abspath(current)):
            self.add_recent_to_fileMenu()
            return
        recording = self.view_workspace.recording_page
        if recording.drafts and not recording.written:
            QMessageBox.warning(self, '录制尚未写入', '请先写入或清空录制，再切换项目。')
            self.add_recent_to_fileMenu()
            return
        if self.workspace.repository.list_commands():
            answer = QMessageBox.question(self, '切换项目',
                '是否先保存当前项目？尚未写入的录制请先写入后再切换。',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
            if answer == QMessageBox.Cancel or (answer == QMessageBox.Save and not self.save_data('自动保存')):
                self.add_recent_to_fileMenu()
                return
        try:
            self.data_import(file_path)
        finally:
            self.add_recent_to_fileMenu()

    def copy_data(self):
        """复制节点画布中选中的指令。"""
        return self.workspace.copy_commands()

    def modify_parameters(self):
        """用对应的独立参数窗口修改当前节点。"""
        selected_ = self.workspace.selected_command_ids()
        if not selected_:
            QMessageBox.information(
                self,
                "提示",
                "请先选择一条待修改的指令。",
                QMessageBox.StandardButton.Ok,
            )
            return False
        return self.workspace.edit_command(selected_[0])

    def show_windows(self, judge):
        """打开窗体"""
        if judge == "设置":
            setting_win = Setting(self)  # 设置窗体
            setting_win.tabWidget.setCurrentIndex(0)
            setting_win.setModal(True)
            setting_win.exec()
        elif judge == "全局":
            global_s = Global_s(self)  # 全局设置窗口
            global_s.setModal(True)
            global_s.exec()
        elif judge == "关于":
            about = About(self)  # 设置关于窗体
            about.setModal(True)
            about.exec()
        elif judge == "说明":
            QDesktopServices.openUrl(QUrl(MAIN_WEBSITE))
        elif judge == "快捷键说明":
            title = ["快捷键", "说明"]
            data = [
                ("Ctrl+Enter", "添加指令"),
                ("Ctrl+C", "复制指令"),
                ("Delete", "删除指令"),
                ("Ctrl+D", "导入指令"),
                ("Ctrl+S", "保存指令"),
                ("Ctrl+Alt+S", "另存为Excel")
            ]
            shortcut_win = ShortcutTable(self, title, data)  # 快捷键说明窗口
            shortcut_win.setModal(True)
            shortcut_win.exec()

    def get_data(self, row=None):
        """重新加载节点图和全局运行次数。"""
        self.workspace.reload_graph(row)
        if hasattr(self, "view_workspace"):
            self.view_workspace.refresh_all()
        repeat_number_ = int(self.db.get_setting_value("运行重复次数") or 1)
        self.radioButton.setChecked(repeat_number_ == -1)
        self.radioButton_2.setChecked(repeat_number_ != -1)
        self.spinBox.setValue(max(repeat_number_, 1))

    def save_data(self, judge: str) -> bool:
        """按节点编辑器四工作表协议导出指令、图和设置。"""

        def choose_save_path_() -> Optional[str]:
            default_path_ = os.path.normpath(os.path.join(EXPORTS_FOLDER, "指令数据.xlsx"))
            selected_path_, _ = QFileDialog.getSaveFileName(
                self, "保存文件", default_path_, "Excel 工作簿 (*.xlsx)"
            )
            return os.path.normpath(selected_path_) if selected_path_ else None

        save_path_ = None
        if judge == "自动保存":
            recent_path_ = self.db.get_setting_value("当前文件路径")
            if recent_path_ and recent_path_ != "None":
                save_path_ = os.path.normpath(recent_path_)
                if not os.path.isdir(os.path.dirname(save_path_)):
                    save_path_ = None
            if not save_path_:
                self.statusBar.showMessage(
                    "未找到最近导入的文件路径，已切换为另存为。", 3000
                )
        save_path_ = save_path_ or choose_save_path_()
        if not save_path_:
            return False
        save_path_ = os.path.abspath(save_path_)
        if not save_path_.lower().endswith(".xlsx"):
            save_path_ += ".xlsx"

        target_directory_ = os.path.dirname(save_path_)
        try:
            os.makedirs(target_directory_, exist_ok=True)
        except OSError as error_:
            QMessageBox.warning(
                self, "保存失败", f"无法创建保存目录：{error_}", QMessageBox.StandardButton.Ok
            )
            return False
        if hasattr(self, "view_workspace"):
            self.view_workspace._save_code()

        workbook_ = openpyxl.Workbook()
        temporary_path_ = None
        try:
            self.workspace.repository.export_to_workbook(workbook_, self.db)
            with tempfile.NamedTemporaryFile(
                prefix=".yanyi-", suffix=".xlsx", dir=target_directory_, delete=False
            ) as temporary_file_:
                temporary_path_ = temporary_file_.name
            workbook_.save(temporary_path_)
            # Replace only after the workbook has been written completely, so
            # a failed save never damages the user's last valid task file.
            os.replace(temporary_path_, save_path_)
            temporary_path_ = None
        except PermissionError:
            QMessageBox.critical(
                self, "错误", "保存失败，文件被占用！", QMessageBox.StandardButton.Ok
            )
            return False
        except Exception as error_:
            QMessageBox.warning(
                self, "保存失败", str(error_), QMessageBox.StandardButton.Ok
            )
            return False
        finally:
            workbook_.close()
            if temporary_path_ and os.path.exists(temporary_path_):
                try:
                    os.remove(temporary_path_)
                except OSError:
                    pass

        self.db.update_settings(当前文件路径=save_path_)
        self.db.writes_to_recently_opened_files(save_path_)
        self.add_recent_to_fileMenu()
        if judge != "自动保存" and QMessageBox.question(
            self,
            "提示",
            "指令数据保存成功！是否打开所在文件夹？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            try:
                open_path(os.path.dirname(save_path_))
            except OSError as error_:
                self.statusBar.showMessage(f"无法打开文件夹：{error_}", 3000)
        self.statusBar.showMessage(f"指令数据已保存至{save_path_}。", 3000)
        return True

    def closeEvent(self, event):
        """关闭窗口事件"""
        recording = self.view_workspace.recording_page
        if recording.busy or (recording.drafts and not recording.written):
            if QMessageBox.question(
                    self, "未保存的录制", "录制内容尚未全部写入，退出会丢弃未写入部分。确定退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        # 是否隐藏工具栏
        self.db.update_settings(
            显示工具栏=str(self.actiong.isChecked()),
            执行中隐藏主窗口=str(self.checkBox_2.isChecked()),
        )
        # 是否退出清空数据库
        if self.db.get_bool_setting("退出提醒清空指令"):
            choice = QMessageBox.question(
                self, "提示", "确定退出并清空所有指令？\n将自动保存当前指令数据。"
                , QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if choice == QMessageBox.StandardButton.Yes:
                # 只有确认保存成功后才能清空数据。
                if not self.save_data("自动保存"):
                    event.ignore()
                    return
            else:
                event.ignore()
                return

        if self.command_thread.isRunning() and not self.command_thread.stop_and_wait():
            QMessageBox.warning(
                self,
                "无法退出",
                "执行线程尚未停止，已取消退出。",
                QMessageBox.StandardButton.Ok,
            )
            event.ignore()
            return

        if self.db.get_bool_setting("退出提醒清空指令"):
            self.db.clear_all_ins()
        recording.shutdown()
        self._closing = True
        event.accept()

    def data_import(self, file_path: str) -> None:
        """识别旧版备份，完整验证并另存新版后，事务性替换指令图。"""
        thread_ = getattr(self, 'command_thread', None)
        recording_ = getattr(self.view_workspace, 'recording_page', None)
        if (thread_ is not None and thread_.isRunning()) or (recording_ is not None and recording_.busy):
            self.statusBar.showMessage('请先停止任务和录制，再导入项目。', 5000)
            return
        if file_path == "资源文件夹路径":
            target_path_, _ = QFileDialog.getOpenFileName(
                self,
                "请选择指令备份文件",
                EXPORTS_FOLDER,
                "Excel 工作簿 (*.xlsx)",
            )
            if not target_path_:
                return
        else:
            target_path_ = file_path
        target_path_ = os.path.normpath(target_path_)
        if os.path.splitext(target_path_)[1].lower() != ".xlsx":
            QMessageBox.warning(
                self, "导入失败", "请选择 Clicker / An Clicker 导出的 .xlsx 文件。",
                QMessageBox.StandardButton.Ok,
            )
            return

        workbook_ = None
        converted_ = None
        migration_message_ = ""
        migrated_branch_ = False
        try:
            from legacy_workbook import convert_legacy_workbook, save_converted_copy

            workbook_ = openpyxl.load_workbook(target_path_)
            from migration_tool import needs_batch_migration, choose_migration
            if needs_batch_migration(workbook_):
                selected_path_ = choose_migration(self, workbook_, target_path_)
                if selected_path_:
                    self.data_import(selected_path_)
                return
            converted_ = convert_legacy_workbook(workbook_, os.path.dirname(os.path.abspath(target_path_)))
            self.workspace.repository.validate_workbook(converted_)
            migrated_branch_ = any(row[1] == "旧版迁移来源分支" for row in
                                   converted_["设置"].iter_rows(min_row=2, values_only=True))
            if converted_ is not workbook_:
                count_ = converted_["命令"].max_row - 1
                if QMessageBox.question(
                    self, "转换旧版数据",
                    f"识别到 {count_} 条旧版指令，将按表格行顺序生成新版表格和流程图。\n"
                    "原文件不会修改，将在旁边另存“原文件名-新版.xlsx”。\n"
                    "当前指令也会先备份。是否转换并导入？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                ) != QMessageBox.StandardButton.Yes:
                    return
                backup_ = openpyxl.Workbook()
                try:
                    self.workspace.repository.export_to_workbook(backup_, self.db)
                    backup_path_ = save_converted_copy(
                        backup_, os.path.join(os.path.dirname(target_path_), "导入前指令备份.xlsx")
                    )
                finally:
                    backup_.close()
                target_path_ = save_converted_copy(converted_, target_path_)
                migration_message_ = f"旧版数据已转换。\n新版文件：{target_path_}\n导入前备份：{backup_path_}"
            self.workspace.repository.import_from_workbook(converted_)
        except (WorkbookValidationError, ValueError, sqlite3.DatabaseError, OSError, zipfile.BadZipFile) as error_:
            QMessageBox.warning(
                self, "导入失败", str(error_), QMessageBox.StandardButton.Ok
            )
            return
        finally:
            if converted_ is not None and converted_ is not workbook_:
                converted_.close()
            if workbook_ is not None:
                workbook_.close()

        self.workspace.reload_graph()
        self.view_workspace.refresh_all()
        if migrated_branch_:
            repeat_number_ = int(self.db.get_setting_value("运行重复次数") or 1)
            self.radioButton.setChecked(repeat_number_ == -1)
            self.radioButton_2.setChecked(repeat_number_ != -1)
            self.spinBox.setValue(max(repeat_number_, 1))
        self.db.update_settings(当前文件路径=target_path_)
        self.db.writes_to_recently_opened_files(target_path_)
        self.menuzv.clear()
        self.add_recent_to_fileMenu()
        self.statusBar.showMessage(migration_message_ or "指令数据导入成功，已自动设置保存路径。", 6000)
        if file_path == "资源文件夹路径" or migration_message_:
            QMessageBox.information(
                self, "提示", migration_message_ or "指令数据导入成功！", QMessageBox.StandardButton.Ok
            )

    def start(self, run_mode='全部指令', info=0) -> bool:
        """主窗体开始按钮
        :param run_mode: 运行模式（全部指令、单行指令、从当前行运行）
        :param info: 指令ID"""

        if self.view_workspace.recording_page.busy:
            self.statusBar.showMessage("请先停止键鼠录制，再运行任务。", 5000)
            return False

        def operation_before_execution():
            """执行前的操作"""
            self.clear_signal.emit()  # 清空日志
            self.view_workspace.show_table()  # 切换到保留日志的表格视图
            if self.checkBox_2.isChecked() and escape_available_:  # Keep stop controls visible if global Esc is unavailable.
                self.hide()

        if self.command_thread.isRunning():
            if not self.command_thread.stop_and_wait():
                self.statusBar.showMessage("原任务尚未停止，未启动新任务。", 5000)
                return False
        self.command_thread.prepare_for_start()
        escape_available_ = self._arm_escape_stop()
        operation_before_execution()  # 执行前的操作
        self.command_thread.set_run_mode(run_mode, info)
        # 设置重复次数
        repeat_number = self.spinBox.value() if self.radioButton_2.isChecked() else -1
        self.command_thread.set_repeat_number(repeat_number)  # 设置重复次数
        self.db.set_setting_value("运行重复次数", repeat_number)
        # 记录开始时间的时间戳
        self.start_time = current_time()
        # 开始运行
        self.command_thread.start()
        return True

    def _arm_escape_stop(self):
        self.escape_stop.setEnabled(True)
        actions_ = {'开始运行':'开始线程', '结束运行':'终止线程', '暂停和恢复':'暂停和恢复线程'}
        self._escape_previous_action = next((actions_.get(name) for name, keys in self.db.get_global_shortcut().items()
            if [key.lower() for key in keys] in (['esc'], ['escape'])), None)
        try:
            if not global_hotkeys_supported(self.hk_stop):
                raise RuntimeError('当前环境不支持全局快捷键')
            if self._escape_previous_action is None and not is_hotkey_valid(self.hk_stop, ['escape']):
                raise RuntimeError('Esc 已被其他程序占用')
            self.hk_stop.register(('escape',), callback=lambda *_: self.shortcut_requested.emit('终止线程'), overwrite=True)
            self._escape_registered = True
            return True
        except Exception as error:
            self.statusBar.showMessage(f'{error}；本次不隐藏窗口，请使用结束任务按钮。', 6000)
            return False

    def _runtime_finished(self):
        if getattr(self, '_closing', False):
            return
        if self.command_thread.isRunning():
            return
        self.escape_stop.setEnabled(False)
        if self._escape_registered:
            try:
                self.hk_stop.unregister(('escape',))
                if self._escape_previous_action:
                    action = self._escape_previous_action
                    self.hk_stop.register(('escape',), callback=lambda *_: self.shortcut_requested.emit(action), overwrite=True)
            except Exception as error:
                self.statusBar.showMessage(f'恢复 Esc 快捷键失败：{error}', 5000)
            finally:
                self._escape_registered = False
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.view_workspace.show_main()
        self.raise_()
        self.activateWindow()

    def clear_textEdit(self):
        """清空日志，主要用于在全局快捷键线程中调用，避免线程阻塞引发的程序闪退"""
        self.textEdit.clear()

    @Slot(int)
    def clear_runtime_cache(self, iteration: int) -> None:
        """Bound GUI/Python caches during long repeated runs."""
        QPixmapCache.clear()
        gc.collect()
        if iteration > 0:
            self.statusBar.showMessage(f"第 {iteration} 次循环后已自动释放运行缓存", 2500)

    def exporting_operation_logs(self):
        """导出操作日志"""
        # 打开保存文件对话框
        target_path = QFileDialog.getSaveFileName(
            parent=self,
            caption="请选择保存路径",
            dir=os.path.join(LOGS_FOLDER, "操作日志.txt"),
            filter="(*.txt)",
        )
        # 判断是否选择了文件
        if target_path[0] != "":
            # 获取操作日志
            logs = self.textEdit.toPlainText()
            # 将操作日志写入文件
            with open(target_path[0], "w") as f:
                f.write(f"日志导出时间：{get_str_now_time()}\n")
                f.write(logs)
            QMessageBox.information(
                self,
                "提示",
                "操作日志导出成功！",
                QMessageBox.StandardButton.Ok,
            )

    def global_shortcut_key(self, i_str):
        """全局热键处理函数"""
        self.db.system_prompt_tone("全局快捷键")  # 发出提示音

        if i_str == "终止线程":
            if self.command_thread.isRunning():
                stopped_ = self.command_thread.stop_and_wait()
                # 获取当前时间
                self.send_message("任务终止！" if stopped_ else "任务正在等待当前指令结束。")
                if stopped_:
                    self._runtime_finished()
                if self.checkBox_2.isChecked():
                    self.show()
                QApplication.processEvents()
                self.db.show_normal_window_with_specified_title(self.windowTitle())  # 显示窗口

        elif i_str == "开始线程":
            if self.start('全部指令', 0):  # 开始线程
                self.send_message("任务开始！")

        elif i_str == "暂停和恢复线程":
            if self.command_thread.isRunning():
                if self.command_thread.is_paused:
                    self.send_message("任务恢复！")
                    self.command_thread.resume()
                else:
                    self.send_message("任务暂停！")
                    self.command_thread.pause()

    def send_message(self, message):
        """向日志窗口发送信息"""
        time_message = f"<font color=#ffff00>{get_str_now_time()}</font>"
        if message != "换行":
            self.textEdit.append(f"{time_message}&nbsp;&nbsp;&nbsp;&nbsp;{message}")
        else:
            self.textEdit.append('')

    def thread_finished(self, message):

        def send_elapsed_time():
            """发送耗时"""
            elapsed_time = current_time() - (self.start_time or current_time())
            # 将秒转换为毫秒或者保留两位小数的秒数
            if elapsed_time < 1:
                elapsed_time_ms = round(elapsed_time * 1000)  # 毫秒
                return f"{elapsed_time_ms}毫秒"
            else:
                elapsed_time_sec = round(elapsed_time, 2)  # 秒，保留两位小数
                return f"{elapsed_time_sec}秒"

        self.send_message(f"{message}，耗时{send_elapsed_time()}。")
        if self.checkBox_2.isChecked():  # 显示窗口
            self.show()
            QApplication.processEvents()
        self.db.system_prompt_tone("线程结束")  # 发出提示音
        self.db.show_normal_window_with_specified_title(self.windowTitle())  # 显示窗口

class About(QDialog, Ui_About):
    """关于窗体"""

    def __init__(self, parent: Optional[Main_window] = None):
        super().__init__(parent)
        # 初始化窗体
        self.setupUi(self)
        self.db = getattr(parent, "db", None) or DatabaseOperation()
        install_window_state(self, self.db, self.windowTitle())
        self.label_2.setText(f"版本：{CURRENT_VERSION}")  # 设置版本号
        self.label_7.setText('<a href="{}"><font color="red">{}</font></a>'.format(QQ_GROUP, QQ))
        self.label_9.setText('<a href="{}"><font color="red">{}</font></a>'.format(QQ_GROUP_OLD, QQ_OLD))
        self.label_4.setText(
            "<b>贡献者：</b>{}　　{}<br>"
            "<b>QQ：</b>{}　　{}<br>"
            "<b>邮箱：</b><a href=\"mailto:{}\">{}</a>　　"
            "<a href=\"mailto:{}\">{}</a><br>"
            "Copyright © 2022–2026".format(
                *CONTRIBUTORS,
                *QQ_CONTACTS,
                EMAIL_CONTACTS[0], EMAIL_CONTACTS[0],
                EMAIL_CONTACTS[1], EMAIL_CONTACTS[1],
            )
        )
        self.label_4.setOpenExternalLinks(True)
        self.gitee.setToolTip(GITEE_WEBSITE_SECOND)
        self.gitee_3.setToolTip(MAIN_WEBSITE)
        self.gitee_2.setToolTip(Github_WEBSITE)
        self.gitee_4.setToolTip(GITHUB_WEBSITE_OLD)
        # 绑定事件
        self.gitee.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITEE_WEBSITE_SECOND))
        )
        self.gitee_2.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(Github_WEBSITE))
        )
        self.gitee_3.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(MAIN_WEBSITE))
        )
        self.gitee_4.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITHUB_WEBSITE_OLD))
        )
        self.pushButton_2.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(ISSUE_WEBSITE))
        )
        self.pushButton_feedback_2.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(ISSUE_WEBSITE_2))
        )

    def closeEvent(self, event):
        super().closeEvent(event)
