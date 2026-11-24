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

import shutil
import collections
import gc
import html
import os.path
import sqlite3
import sys
import tempfile
import zipfile
from time import time as current_time
from typing import Optional

import openpyxl
from anclicker.platform.qt_compat.QtCore import QTimer, Signal, Slot, QUrl, Qt, QSignalBlocker
from anclicker.platform.qt_compat.QtGui import QAction, QDesktopServices, QPixmapCache, QShortcut, QKeySequence
from anclicker.platform.qt_compat.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
)
from anclicker.app.paths import LOGS_FOLDER, RESOURCE_FOLDER
from anclicker.platform.services import create_system_hotkey, global_hotkeys_supported, is_hotkey_valid, normalize_hotkey, open_path
from anclicker.app.time_utils import get_str_now_time
from anclicker.storage.graph_repository import WorkbookValidationError
from anclicker.ui.window_arrangement_tool import install_window_arrangement_tool
from anclicker.ui.information_dialogs import InformationDialog, style_about_dialog
from anclicker.ui.project_files import install_new_blank_action, is_blank_project_path, next_project_path, project_directory, remember_project_directory
from anclicker.ui.workspace_constants import CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING, TASK_NAME_SETTING, WINDOW_TITLE_SETTING
from anclicker.ui.recent_projects import install_recent_context_menu
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.app.main_work import CommandThread
from anclicker.ui.view_workspace import ViewWorkspace
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.generated.windows.about_ui import Ui_About
from anclicker.ui.generated.windows.mainwindow_ui import Ui_MainWindow
from anclicker.ui.dialogs.设置窗口 import Setting
from anclicker.ui.dialogs.资源文件夹窗口 import Global_s
from info import CURRENT_VERSION, MAIN_WEBSITE, ISSUE_WEBSITE, ISSUE_WEBSITE_2, QQ_GROUP, QQ, \
    QQ_GROUP_OLD, QQ_OLD, QQ_CONTACTS, EMAIL_CONTACTS, CONTRIBUTORS, APP_NAME, \
    GITEE_WEBSITE_SECOND, GITHUB_WEBSITE_OLD, Github_WEBSITE, WINDOW_TITLE
from anclicker.ui.dialogs.快捷键说明 import ShortcutTable
from anclicker.ui.dialogs.窗口状态 import install_window_state

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'FramelessMainWindow': ('from', 'anclicker.ui.window_chrome', ('FramelessMainWindow',), 0),
    'ApplicationState_application_state': ('from', 'anclicker.app.state', ('ApplicationState', 'application_state'), 0),
    'OcrPool': ('from', 'anclicker.ui.ocr_pool', ('OcrPool',), 0),
    'QCheckBox_QWidget_QVBoxLayout': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QCheckBox', 'QWidget', 'QVBoxLayout'), 0),
    'RecentProjectPicker_ProjectDropFilter': ('from', 'anclicker.ui.recent_projects', ('RecentProjectPicker', 'ProjectDropFilter', 'install_folder_import'), 0),
    'TaskScheduler': ('from', 'anclicker.app.scheduled_tasks', ('TaskScheduler',), 0),
    'AutoUpdateManager': ('from', 'anclicker.app.updates.自动更新接入', ('AutoUpdateManager',), 0),
    'missing_startup_resources': ('from', 'anclicker.app.startup_resources', ('missing_startup_resources',), 0),
    'convert_legacy_workbook_save_converted_copy': ('from', 'anclicker.storage.legacy_workbook', ('convert_legacy_workbook', 'save_converted_copy'), 0),
    'needs_batch_migration_choose_migration': ('from', 'anclicker.storage.migration_tool', ('needs_batch_migration', 'choose_migration'), 0),
})


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


FramelessMainWindow = _module_imports.load('FramelessMainWindow')
ApplicationState, application_state = _module_imports.load('ApplicationState_application_state')


class Main_window(FramelessMainWindow, Ui_MainWindow):
    """主窗口"""
    clear_signal = Signal()  # 自定义信号，textEdit清空信息，防止在全局快捷键调用时程序崩溃
    shortcut_requested = Signal(str)

    def __init__(self):
        super().__init__()
        # 初始化窗体
        self.application_state = ApplicationState(self)
        self.setupUi(self)
        self.merge_control_and_operation_panel()
        self.setWindowTitle(WINDOW_TITLE)
        # 窗口和信息
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)  # 实例化状态栏
        self.db = DatabaseOperation()
        OcrPool = _module_imports.load('OcrPool')
        self.ocr_pool = OcrPool()
        QApplication.instance().aboutToQuit.connect(self.ocr_pool.close)
        self.workspace = InstructionWorkspace(self.db.db_path, self)
        self._install_instruction_workspace()
        self.view_workspace = ViewWorkspace(self)
        from anclicker.ui.tooltip_policy import TooltipPolicy
        self.tooltip_policy = TooltipPolicy(self)
        QCheckBox, QWidget, QVBoxLayout = _module_imports.load('QCheckBox_QWidget_QVBoxLayout')
        self.run_unconnected_checkbox = QCheckBox('运行未连接模块', self.groupBox_3)
        self.run_unconnected_checkbox.setObjectName('runUnconnectedCheckBox')
        self.run_unconnected_checkbox.setChecked(self.db.get_setting_value('运行未连接模块') != 'False')
        self.run_unconnected_checkbox.setToolTip('默认运行没有任何连线的节点；取消后跳过孤立节点。单行运行不受影响。')
        self.run_unconnected_checkbox.toggled.connect(lambda checked: self.db.set_setting_value('运行未连接模块', str(checked)))
        self.gridLayout_2.removeWidget(self.checkBox_2)
        options = QWidget(self.groupBox_3)
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.addWidget(self.run_unconnected_checkbox)
        options_layout.addWidget(self.checkBox_2)
        self.gridLayout_2.addWidget(options, 2, 0, 1, 2)
        RecentProjectPicker, ProjectDropFilter, install_folder_import = _module_imports.load('RecentProjectPicker_ProjectDropFilter')
        self.recent_project_picker = RecentProjectPicker(self.groupBox_3)
        self.gridLayout_2.addWidget(self.recent_project_picker, 3, 0, 1, 2)
        self.gridLayout_2.setRowStretch(3, 0)
        self.gridLayout_2.setRowStretch(4, 1)
        self.recent_project_picker.openRequested.connect(self.open_project_path)
        self.recent_project_picker.removeRequested.connect(self.remove_recent_project)
        install_folder_import(self)
        from anclicker.ui.data_transfer import install_data_transfer
        install_data_transfer(self)
        self.project_drop_filter = ProjectDropFilter(self, self.open_project_path)
        self._initial_graph_fit_pending = True
        self.tabWidget.currentChanged.connect(self._schedule_initial_graph_fit)
        self.check_file_integrity()  # 检查文件完整性
        self.add_recent_to_fileMenu()  # 将最近文件添加到菜单中
        self.pushButton.clicked.connect(self.workspace.add_selected_instruction)
        self.pushButton_3.clicked.connect(
            lambda: self.show_windows("全局")
        )  # 显示全局参数窗口
        from anclicker.platform.qt_compat.QtWidgets import QMenu
        from anclicker.ui.dialogs.设置窗口 import SETTINGS_SECTIONS
        self.settings_sections_menu = QMenu('设置', self)
        self.actions_2.setMenu(self.settings_sections_menu)
        for section in SETTINGS_SECTIONS:
            action = self.settings_sections_menu.addAction(section)
            action.triggered.connect(lambda checked=False, section=section: self.show_windows('设置', section))
        from anclicker.ui.settings_menu import install_settings_click
        install_settings_click(self)
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
        install_new_blank_action(self)
        install_window_arrangement_tool(self)
        from anclicker.ui.view_shortcuts import install_all_menu_shortcuts
        install_all_menu_shortcuts(self)
        # 主窗体开始按钮
        self.pushButton_5.clicked.connect(lambda: self.global_shortcut_key("开始线程"))
        self.start_time = None
        self._runtime_messages = collections.deque(maxlen=1500)
        self._runtime_message_timer = QTimer(self)
        self._runtime_message_timer.setInterval(40)
        self._runtime_message_timer.timeout.connect(self._flush_runtime_messages)
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
        self.command_thread.error_requested.connect(self._show_runtime_error, Qt.QueuedConnection)
        self._runtime_error_box = None
        self.command_thread.send_type_and_id.connect(self._follow_running_command, Qt.QueuedConnection)
        flow_view = self.workspace.editor.view
        flow_view.set_continuous_animation(self.db.get_setting_value('流程图持续动画') == 'True')
        flow_view.continuousAnimationChanged.connect(self._save_flow_animation_setting)
        flow_view.set_arrows_visible(self.db.get_setting_value('流程图显示箭头') != 'False')
        flow_view.arrowsVisibilityChanged.connect(self._save_flow_arrows_setting)
        self.command_thread.started.connect(flow_view.play_run_animation, Qt.QueuedConnection)
        self.shortcut_requested.connect(self.global_shortcut_key, Qt.QueuedConnection)
        self._escape_registered = False
        self._escape_hotkey = None
        self._escape_previous_action = None
        self.escape_stop = QShortcut(QKeySequence('+'.join(self.db.get_global_shortcut()['结束运行2'])), self)
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
        from anclicker.ui.project_run_controls import ProjectRunControls
        self.project_run_controls = ProjectRunControls(self)
        from anclicker.ui.project_changes import BASELINE_KEY, mark_clean
        if not self.db.get_setting_value(BASELINE_KEY):
            mark_clean(self)
        self.view_workspace.restore_last_view()
        self._install_updates()
        TaskScheduler = _module_imports.load('TaskScheduler')
        self.task_scheduler = TaskScheduler(self)
        self.view_workspace.title_bar.schedule_button.clicked.connect(self.task_scheduler.show_settings)

    def _install_updates(self):
        if sys.platform != 'win32':
            return
        AutoUpdateManager = _module_imports.load('AutoUpdateManager')
        self.auto_update = AutoUpdateManager(self)
        # Use the existing help menu that contains About.
        menu = next((action.menu() for action in self.menubar.actions()
                     if action.menu() and self.actionabout in action.menu().actions()), None)
        if menu is None:
            menu = self.menubar.addMenu('帮助')
        if menu.actions() and not menu.actions()[-1].isSeparator():
            menu.addSeparator()
        check = menu.addAction('检查更新')
        check.setObjectName('actionCheckForUpdates')
        check.triggered.connect(lambda: self.auto_update.check_for_updates(True))
        self.auto_update.update_ready.connect(self.view_workspace.title_bar.show_update)
        self.auto_update.update_progress.connect(self._update_progress)
        self.view_workspace.title_bar.updateButton.clicked.connect(self._apply_ready_update)
        if not any(flag in sys.argv for flag in ('--startup-smoke-test', '--release-smoke', '--velopack-local-smoke')):
            QTimer.singleShot(1500, self.auto_update.check_on_startup)

    def _update_progress(self, text, value):
        self.statusBar.showMessage(f'{text} {value}%' if value >= 0 else text)
        if value == -2 and self.auto_update.ready_update_info is not None:
            self.view_workspace.title_bar.set_update_applying(False)

    def _apply_ready_update(self):
        if getattr(self, '_update_preparing', False):
            return
        bar = self.view_workspace.title_bar
        bar.set_update_applying(True)
        if not self.auto_update.activate_update_entry():
            bar.set_update_applying(False)

    def prepare_for_update(self):
        if getattr(self, "task_scheduler", None) and self.task_scheduler.busy:
            return False, "请先结束定时任务，再更新。"
        if (self.command_thread.isRunning() or (self.view_workspace.recording_page.busy or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'busy', False))
                or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'unsaved', False)
                or application_state(self).is_busy(excluding=('execution', 'recording', 'web_recording', 'schedule', 'update'))
                or (self.view_workspace.recording_page.drafts and not self.view_workspace.recording_page.written)
                or QApplication.activeModalWidget() is not None):
            return False, '请先结束运行、录制或指令测试并关闭编辑窗口。'
        if not self.auto_update.shutdown():
            return False, '正在检查或下载更新，请稍后重试。'
        # Persist the debounced editor text only; updating never exports Excel or
        # touches recent-file menus, dialogs, or the normal exit-clear workflow.
        self.view_workspace._save_code()
        return True, ''

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
            remember_position=True,
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
        # Validate the resources actually used by this version, not legacy PNGs.
        missing_startup_resources = _module_imports.load('missing_startup_resources')
        missing = missing_startup_resources(RESOURCE_FOLDER)
        if missing:
            QMessageBox.critical(
                self, '启动资源缺失',
                '缺少启动资源：' + '、'.join(missing) + '。请完整解压安装包后重试。',
                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            sys.exit(1)

    def register_global_shortcut_keys(self):
        """注册全局快捷键"""
        # 从数据库获取全局快捷键
        global_shortcut = self.db.get_global_shortcut()
        self.escape_stop.setKey(QKeySequence('+'.join(global_shortcut['结束运行2'])))
        self._primary_stop_available=False
        self._registered_shortcut_help = {}
        # 检查快捷键是否有效，无效则弹出提示
        try:
            global_shortcuts = {
                "开始运行": "开始线程",
                "结束运行": "终止线程",
                "暂停和恢复": "暂停和恢复线程",
            }

            shared = normalize_hotkey(global_shortcut['开始运行']) == normalize_hotkey(global_shortcut['结束运行'])
            for shortcut_name, action_ in global_shortcuts.items():
                if shared and shortcut_name == '结束运行':
                    continue
                if shared and shortcut_name == '开始运行':
                    action_ = '启停共享按键'
                # 将ctrl替换为control
                global_shortcut[shortcut_name] = list(normalize_hotkey(global_shortcut[shortcut_name]))
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
                    self._registered_shortcut_help['开始/结束运行' if shared and shortcut_name == '开始运行' else shortcut_name] = '+'.join(global_shortcut[shortcut_name])
                    if shortcut_name=='结束运行' or shared and shortcut_name=='开始运行':self._primary_stop_available=True
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
            if self.command_thread.isRunning() or bool(getattr(self, 'task_scheduler', None) and self.task_scheduler.busy):
                self._arm_escape_stop()
            if not global_hotkeys_supported(self.hk_stop):
                self.statusBar.showMessage(
                    "当前桌面环境不支持全局快捷键，请使用界面按钮操作。", 5000
                )
        except Exception as e:
            print(e)
            QMessageBox.critical(self, "错误", "全局快捷键已失效！", QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)

    def unregister_global_shortcut_keys(self):
        """Release configured hotkeys while settings captures replacement keys."""
        self.escape_stop.setEnabled(False)
        self._registered_shortcut_help = {}
        shortcuts=self.db.get_global_shortcut()
        released = set()
        for name,keys in shortcuts.items():
            if name=='结束运行2' and not self._escape_registered:
                continue
            hotkey=self._escape_hotkey if name=='结束运行2' else normalize_hotkey(keys)
            if tuple(hotkey) in released:
                continue
            released.add(tuple(hotkey))
            try:
                self.hk_stop.unregister(tuple(hotkey))
            except Exception as error:
                print(error)
        self._escape_registered=False
        self._escape_hotkey=None
        self._primary_stop_available=False

    def add_recent_to_fileMenu(self):
        """将最近文件添加到菜单中"""
        install_recent_context_menu(self)
        recently_opened_list = self.db.get_recently_opened_file("文件列表")
        current_file_path = self.db.get_setting_value("当前文件路径")
        self.menuzv.clear()
        if hasattr(self, 'recent_project_picker'):
            self.recent_project_picker.refresh(recently_opened_list, current_file_path)
        # 将最近打开文件添加到菜单中
        if len(recently_opened_list) != 0:
            for file in recently_opened_list:
                file_action = QAction(text=file, parent=self.menuzv)
                file_action.setData(file)
                # 设置信号
                file_action.triggered.connect(
                    lambda checked=False, file_=file: self.open_recent_file(file_)
                )
                file_action.setCheckable(True)
                # 设置当前文件为选中状态
                if file == current_file_path:
                    file_action.setChecked(True)
                self.menuzv.addAction(file_action)
        home = getattr(getattr(self, 'view_workspace', None), 'main_page', None)
        if home is not None:
            home.refresh_projects()
        # 关闭菜单栏
        self.menuzv.close()

    def remove_recent_project(self,file_path):
        self.db.remove_recently_opened_file(file_path)
        self.add_recent_to_fileMenu()
        home=getattr(getattr(self,'view_workspace',None),'main_page',None)
        if home is not None:home.refresh_projects()
        self.statusBar.showMessage('已从最近列表删除记录，磁盘文件保持不变。',4000)

    def open_recent_file(self, file_path):
        """Reopen even the current path so external workbook edits are read."""
        return self.open_project_path(file_path)

    def delete_data(self):
        """Delete from the active workspace, not stale flow selections."""
        if self.tabWidget.currentIndex() == 1:
            return self.view_workspace.delete_table_commands()
        return self.workspace.remove_commands()

    def open_project_path(self, file_path):
        """One guarded entry point for recent selection, edited paths and drops."""
        if not os.path.isfile(file_path):
            self.db.remove_recently_opened_file(file_path)
            self.add_recent_to_fileMenu()
            home = getattr(getattr(self, 'view_workspace', None), 'main_page', None)
            if home is not None:
                home.refresh_projects()
            QMessageBox.critical(
                self, "错误", "文件不存在！已经从最近打开文件中删除。",
                QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
            return
        thread = getattr(self, 'command_thread', None)
        if (thread is not None and thread.isRunning()) or (self.view_workspace.recording_page.busy or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'busy', False)):
            self.statusBar.showMessage('请先停止任务和录制，再切换项目。', 5000)
            self.add_recent_to_fileMenu()
            return
        current = self.db.get_setting_value('当前文件路径')
        same_project = bool(current and current != 'None' and
                            os.path.normcase(os.path.abspath(file_path)) == os.path.normcase(os.path.abspath(current)))
        recording = self.view_workspace.recording_page
        if (recording.drafts and not recording.written) or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'unsaved', False):
            QMessageBox.warning(self, '录制尚未写入', '请先写入或清空录制，再切换项目。')
            self.add_recent_to_fileMenu()
            return
        from anclicker.ui.project_changes import is_modified
        modified = is_modified(self)
        if same_project and modified:
            # An external Excel edit must never be overwritten by the stale
            # in-memory task before reloading that very same workbook.
            answer = QMessageBox.question(self, '重新打开项目',
                '是否从文件重新读取最新内容？\n当前未保存的修改将被替换，磁盘文件不会被覆盖。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                self.add_recent_to_fileMenu()
                return
        elif modified:
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

    def show_windows(self, judge, section=None):
        """打开窗体"""
        if judge == "设置":
            if section == '快捷键设置':
                self.open_view_shortcut_settings()
                return
            setting_win = Setting(self)  # 设置窗体
            setting_win.tabWidget.setCurrentIndex(next((i for i in range(setting_win.tabWidget.count())
                if setting_win.tabWidget.tabText(i) == section), 0))
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
            from anclicker.ui.view_shortcuts import active_shortcut_help
            data = active_shortcut_help(self)
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

        original_project_path_ = self.db.get_setting_value('当前文件路径')

        def choose_save_path_() -> Optional[str]:
            directory_ = project_directory(self.db)
            default_path_ = next_project_path(os.path.join(directory_, '指令数据.xlsx'), fill_gaps=True)
            imported_path_ = self.db.get_setting_value("当前文件路径")
            if imported_path_ and imported_path_ != 'None' and not is_blank_project_path(imported_path_):
                default_path_ = next_project_path(os.path.join(directory_, os.path.basename(imported_path_)))
            selected_path_, _ = QFileDialog.getSaveFileName(
                self, "另存为", default_path_, "Excel 工作簿 (*.xlsx)",
                options=QFileDialog.DontConfirmOverwrite,
            )
            return os.path.normpath(selected_path_) if selected_path_ else None

        save_path_ = None
        if judge == "保存新空白页":
            save_path_ = self.db.get_setting_value('本机新建默认保存路径')
        if judge == "自动保存":
            recent_path_ = self.db.get_setting_value("当前文件路径")
            if recent_path_ and recent_path_ != "None":
                save_path_ = os.path.normpath(recent_path_)
                if os.path.splitext(save_path_)[1].lower() == ".xlsm":
                    save_path_ = None
                elif not os.path.isdir(os.path.dirname(save_path_)):
                    save_path_ = None
            if not save_path_:
                self.statusBar.showMessage(
                    "当前项目无法直接保存，已切换为另存为 .xlsx。", 3000
                )
        direct_save_ = bool(save_path_)
        save_path_ = save_path_ or choose_save_path_()
        if not save_path_:
            return False
        save_path_ = os.path.abspath(save_path_)
        if save_path_.lower().endswith('.xlsm'):
            QMessageBox.warning(self, '保存格式', '项目另存为仅支持 .xlsx，请选择新的 .xlsx 文件名；原 .xlsm 文件保留。')
            return False
        if not save_path_.lower().endswith(".xlsx"):
            save_path_ += ".xlsx"

        def confirm_overwrite_():
            return QMessageBox.question(
                self, '确认覆盖', f'文件已存在：\n{save_path_}\n是否覆盖？选择否将取消本次保存。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            ) == QMessageBox.Yes

        overwrite_allowed_ = direct_save_ and judge != '保存新空白页'
        if not direct_save_ and os.path.exists(save_path_):
            if not confirm_overwrite_():
                return False
            overwrite_allowed_ = True

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

        controls = getattr(self, 'project_run_controls', None)
        if controls is not None:
            controls.changed()
        workbook_ = openpyxl.Workbook()
        temporary_path_ = None
        try:
            self.workspace.repository.export_to_workbook(workbook_, self.db)
            from anclicker.storage.project_paths import save_workbook_paths, project_root
            path_root_ = project_root(original_project_path_, os.path.dirname(self.db.db_path), project_directory(self.db))
            save_workbook_paths(workbook_, original_project_path_, save_path_, path_root_,
                                fallback=os.path.dirname(self.db.db_path))
            with tempfile.NamedTemporaryFile(
                prefix=".yanyi-", suffix=".xlsx", dir=target_directory_, delete=False
            ) as temporary_file_:
                temporary_path_ = temporary_file_.name
            workbook_.save(temporary_path_)
            # Replace only after the workbook has been written completely, so
            # a failed save never damages the user's last valid task file.
            if not overwrite_allowed_:
                while True:
                    try:
                        # Exclusive creation prevents a concurrent new file being overwritten.
                        with open(save_path_, 'xb') as destination:
                            try:
                                with open(temporary_path_, 'rb') as source:
                                    shutil.copyfileobj(source, destination)
                            except Exception:
                                destination.close()
                                os.remove(save_path_)
                                raise
                        break
                    except FileExistsError:
                        if judge == '保存新空白页':
                            save_path_ = next_project_path(save_path_)
                        elif confirm_overwrite_():
                            os.replace(temporary_path_, save_path_)
                            temporary_path_ = None
                            break
                        else:
                            return False
                if temporary_path_:
                    os.remove(temporary_path_)
            else:
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

        from anclicker.storage.project_paths import rebase_saved_commands
        rebase_saved_commands(self.db, original_project_path_, save_path_, path_root_)
        self.db.update_settings(当前文件路径=save_path_)
        remember_project_directory(self.db, save_path_)
        self.db.set_setting_value('本机新建默认保存路径', '')
        if controls is not None:
            controls.saved_as(save_path_)
        from anclicker.ui.project_changes import mark_clean
        mark_clean(self)
        if (judge != "保存新空白页" and is_blank_project_path(original_project_path_)
                and os.path.normcase(os.path.abspath(original_project_path_)) != os.path.normcase(save_path_)):
            self.db.remove_recently_opened_file(os.path.normpath(original_project_path_))
        self.db.writes_to_recently_opened_files(save_path_)
        self.add_recent_to_fileMenu()
        if judge not in ("自动保存", "新建前另存为", "保存新空白页") and QMessageBox.question(
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
        if getattr(self, "_update_exit_requested", False):
            self.view_workspace.save_last_view()
            event.accept()
            return
        if getattr(self, 'task_scheduler', None) and self.task_scheduler.busy:
            self.task_scheduler.stop()
            self.statusBar.showMessage('正在停止定时任务，请停止后再关闭窗口。', 5000)
            event.ignore()
            return
        agent = getattr(self.view_workspace, 'agent_page', None)
        if agent is not None and agent.busy:
            agent.stop()
            self.statusBar.showMessage('正在停止对话Ai编程，请结束后再关闭窗口。', 5000)
            event.ignore()
            return
        if getattr(self.workspace, '_instruction_test_active', False):
            context = getattr(self.workspace, '_instruction_test_context', None)
            if context is not None:
                context.stop_requested = True
            self.statusBar.showMessage('正在停止指令测试，请结束后再关闭窗口。', 5000)
            event.ignore()
            return
        agent = getattr(self.view_workspace, 'agent_page', None)
        if agent is not None and agent.unsaved:
            if QMessageBox.question(self, '未写入的指令草稿', '对话Ai编程 草稿尚未写入，确定退出并丢弃？') != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        cancel_update = False
        if hasattr(self, "auto_update") and not self.auto_update.shutdown():
            box = QMessageBox(self)
            box.setWindowTitle('更新尚未完成')
            box.setText('正在检查或下载更新。继续结束将停止本次更新并退出；等待将返回程序继续更新。')
            finish_button = box.addButton('继续结束', QMessageBox.ButtonRole.DestructiveRole)
            wait_button = box.addButton('等待', QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(wait_button)
            box.exec()
            if box.clickedButton() is not finish_button:
                event.ignore()
                return
            cancel_update = True
        recording = self.view_workspace.recording_page
        if getattr(getattr(self.view_workspace, 'web_recording_page', None), 'busy', False):
            self.statusBar.showMessage('请先停止网页录制，再退出。', 5000)
            event.ignore()
            return
        if recording.busy or (recording.drafts and not recording.written) or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'unsaved', False):
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
        importing_data = (getattr(QApplication.instance(), "_whole_data_import", None)
                          or getattr(QApplication.instance(), "_whole_workspace_import", None))
        if self.db.get_bool_setting("退出提醒清空指令") and not importing_data:
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

        if self.command_thread.isRunning():
            self.global_shortcut_key('终止线程')
            self.statusBar.showMessage('正在停止任务，请在停止后关闭窗口。', 5000)
            event.ignore()
            return

        self.view_workspace._save_code()
        if cancel_update and not self.auto_update.cancel_for_exit():
            self.statusBar.showMessage('正在停止更新，请稍后再关闭。', 5000)
            event.ignore()
            return
        if self.db.get_bool_setting("退出提醒清空指令") and not importing_data:
            self.db.clear_all_ins()
        self.view_workspace.save_last_view()
        web_recording = getattr(self.view_workspace, 'web_recording_page', None)
        if web_recording is not None:
            web_recording.shutdown()
        agent = getattr(self.view_workspace, 'agent_page', None)
        if agent is not None:
            agent.shutdown()
        recording.shutdown()
        self._closing = True
        if getattr(self, 'task_scheduler', None):
            self.task_scheduler.timer.stop()
        event.accept()

    def data_import(self, file_path: str, *, use_cached_controls=True) -> None:
        """识别旧版备份，完整验证并另存新版后，事务性替换指令图。"""
        thread_ = getattr(self, 'command_thread', None)
        recording_ = getattr(self.view_workspace, 'recording_page', None)
        if (thread_ is not None and thread_.isRunning()) or (recording_ is not None and recording_.busy) or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'busy', False):
            self.statusBar.showMessage('请先停止任务和录制，再导入项目。', 5000)
            return
        if file_path == "资源文件夹路径":
            target_path_, _ = QFileDialog.getOpenFileName(
                self,
                "导入单文件",
                project_directory(self.db),
                "Excel 工作簿 (*.xlsx *.xlsm)",
            )
            if not target_path_:
                return
        else:
            target_path_ = file_path
        target_path_ = os.path.abspath(target_path_)
        if os.path.splitext(target_path_)[1].lower() not in {".xlsx", ".xlsm"}:
            QMessageBox.warning(
                self, "导入失败", "请选择 Clicker / AnClicker 导出的 .xlsx / .xlsm 文件。",
                QMessageBox.StandardButton.Ok,
            )
            return

        controls = getattr(self, 'project_run_controls', None)
        if controls is not None:
            controls.changed()
        imported_controls = {}
        workbook_ = None
        converted_ = None
        migration_message_ = ""
        migrated_branch_ = False
        automatic_outputs_ = {}
        original_legacy_path_ = None
        try:
            convert_legacy_workbook, save_converted_copy = _module_imports.load('convert_legacy_workbook_save_converted_copy')

            workbook_ = openpyxl.load_workbook(target_path_)
            from anclicker.storage.legacy_workbook import is_graph_workbook
            if not is_graph_workbook(workbook_):
                from anclicker.storage.migration_tool import migrate_automatically
                folder_, automatic_outputs_, selected_path_ = migrate_automatically(workbook_, target_path_)
                backup_ = openpyxl.Workbook()
                try:
                    self.workspace.repository.export_to_workbook(backup_, self.db)
                    save_converted_copy(backup_, os.path.join(folder_, "导入前指令备份.xlsx"))
                finally:
                    backup_.close()
                original_legacy_path_ = target_path_
                workbook_.close()
                target_path_ = selected_path_
                workbook_ = openpyxl.load_workbook(target_path_)
                migration_message_ = f"旧版数据已自动迁移，原文件已备份。当前项目：{target_path_}"
            converted_ = convert_legacy_workbook(workbook_, os.path.dirname(os.path.abspath(target_path_)))
            self.workspace.repository.validate_workbook(converted_)
            project_defaults = {CODE_SETTING: '', CODE_GRAPH_SIGNATURE_SETTING: '',
                                TASK_NAME_SETTING: '默认任务', WINDOW_TITLE_SETTING: ''}
            settings_sheet = converted_['设置']
            present = {row[1] for row in settings_sheet.iter_rows(min_row=2, values_only=True) if row[0] == '设置'}
            for key, value in project_defaults.items():
                if key not in present:
                    settings_sheet.append(['设置', key, value, '其他', None])
            migrated_branch_ = any(row[1] == "旧版迁移来源分支" for row in
                                   converted_["设置"].iter_rows(min_row=2, values_only=True))
            from anclicker.ui.project_run_controls import DEFAULTS as CONTROL_DEFAULTS
            imported_controls = {row[1]: str(row[2]) for row in converted_['设置'].iter_rows(min_row=2, values_only=True)
                                 if row[0] == '设置' and row[1] in (*CONTROL_DEFAULTS, '有限重复次数') and row[2] is not None}
            from anclicker.storage.data_partitions import prepare_project_paths
            data_root_ = os.path.dirname(os.path.abspath(self.db.db_path))
            if not prepare_project_paths(converted_, target_path_, data_root_, os.path.dirname(data_root_),
                    lambda missing: QMessageBox.question(self, '是否适配资源路径',
                        f'有 {len(missing)} 个资源原路径不可用。是否在当前 AnClicker 的 Data 分区内查找并适配？\n选择否将取消打开，保留当前项目。',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes):
                return
            self.workspace.repository.import_from_workbook(converted_, source_path=target_path_, preserve_paths=True)
            self.workspace.clear_connection_history()
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

        # Discard the previous editor's pending write only after import succeeds.
        self.view_workspace._code_save_timer.stop()
        self.view_workspace._code_dirty = False
        self.db.update_settings(当前文件路径=target_path_)
        remember_project_directory(self.db, original_legacy_path_ or target_path_, opened=True)
        self.workspace.reload_graph(reset_view=True)
        if hasattr(self.view_workspace, '_load_code'):
            self.view_workspace._load_code()
        for attribute, setting in (('task_name', TASK_NAME_SETTING), ('window_title', WINDOW_TITLE_SETTING)):
            control = getattr(self.view_workspace, attribute, None)
            if control is not None:
                with QSignalBlocker(control):
                    control.setText(str(self.db.get_setting_value(setting) or project_defaults[setting]))
        self.view_workspace.refresh_all()
        if migrated_branch_:
            repeat_number_ = int(self.db.get_setting_value("运行重复次数") or 1)
            self.radioButton.setChecked(repeat_number_ == -1)
            self.radioButton_2.setChecked(repeat_number_ != -1)
            self.spinBox.setValue(max(repeat_number_, 1))
        self.db.set_setting_value('本机新建默认保存路径', '')
        if controls is not None:
            controls.restore(target_path_, imported_controls, use_cache=use_cached_controls)
        from anclicker.ui.project_changes import mark_clean
        mark_clean(self)
        if original_legacy_path_:
            self.db.remove_recently_opened_file(original_legacy_path_)
            self.db.add_recent_files(automatic_outputs_.values())
        self.db.writes_to_recently_opened_files(target_path_)
        self.menuzv.clear()
        self.add_recent_to_fileMenu()
        self.statusBar.showMessage(migration_message_ or "指令数据导入成功，已自动设置保存路径。", 6000)
        if file_path == "资源文件夹路径" and not migration_message_:
            QMessageBox.information(
                self, "提示", migration_message_ or "指令数据导入成功！", QMessageBox.StandardButton.Ok
            )

    def _save_flow_arrows_setting(self, visible):
        self.db.set_setting_value('流程图显示箭头', str(bool(visible)))

    def _save_flow_animation_setting(self, enabled):
        self.db.set_setting_value('流程图持续动画', str(bool(enabled)))

    def start(self, run_mode='全部指令', info=0) -> bool:
        if 'agent' in self.application_state.activities():
            self.statusBar.showMessage('请先结束对话Ai编程，再启动主任务。', 5000)
            return False
        if getattr(self.workspace, '_instruction_test_active', False):
            self.statusBar.showMessage('请先结束对话Ai编程 或指令测试，再启动主任务。', 5000)
            return False
        if getattr(self, 'task_scheduler', None) and self.task_scheduler.blocks_main_start:
            self.statusBar.showMessage('定时任务正在等待或执行，请稍后启动主任务。', 5000)
            return False
        if getattr(self, '_update_preparing', False):
            self.statusBar.showMessage('正在准备更新，暂时无法启动任务。', 3000)
            return False
        """主窗体开始按钮
        :param run_mode: 运行模式（全部指令、单行指令、从当前行运行）
        :param info: 指令ID"""

        if (self.view_workspace.recording_page.busy or getattr(getattr(self.view_workspace, 'web_recording_page', None), 'busy', False)):
            self.statusBar.showMessage("请先停止键鼠录制，再运行任务。", 5000)
            return False

        def operation_before_execution():
            """执行前的操作"""
            self.clear_signal.emit()  # 清空日志
            self.view_workspace.highlight_running_command(None)
            self._capture_run_window_state()
            self.view_workspace.begin_runtime_view()
            if self.checkBox_2.isChecked() and escape_available_:  # Keep stop controls visible if global Esc is unavailable.
                self.hide()

        if self.command_thread.isRunning():
            self.statusBar.showMessage("原任务尚未停止，未启动新任务。", 5000)
            return False
        if self._runtime_error_box is not None:
            self._runtime_error_box.reject()
        from anclicker.storage.data_partitions import ensure_runtime_paths
        if not ensure_runtime_paths(self):
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
        self.command_thread.run_unconnected = self.run_unconnected_checkbox.isChecked()
        self.command_thread.start()
        self.run_unconnected_checkbox.setEnabled(False)
        return True

    def _arm_escape_stop(self):
        """Arm the optional configurable runtime stop key."""
        shortcuts=self.db.get_global_shortcut()
        keys=normalize_hotkey(shortcuts['结束运行2'])
        self.escape_stop.setKey(QKeySequence('+'.join(shortcuts['结束运行2'])))
        self.escape_stop.setEnabled(bool(keys))
        if not keys:
            return bool(getattr(self,'_primary_stop_available',False))
        if self._escape_registered and self._escape_hotkey==keys:
            return True
        actions_={'开始运行':'开始线程','结束运行':'终止线程','暂停和恢复':'暂停和恢复线程'}
        self._escape_previous_action=next((actions_[name] for name in actions_
            if normalize_hotkey(shortcuts[name])==keys),None)
        try:
            if not global_hotkeys_supported(self.hk_stop):
                raise RuntimeError('当前环境不支持全局快捷键')
            if self._escape_previous_action is None and not is_hotkey_valid(self.hk_stop,list(keys)):
                raise RuntimeError('结束运行2快捷键已被其他程序占用')
            self.hk_stop.register(keys,callback=lambda *_:self.shortcut_requested.emit('终止线程'),overwrite=True)
            self._escape_hotkey=keys
            self._escape_registered=True
            return True
        except Exception as error:
            self.statusBar.showMessage(f'{error}；本次不隐藏窗口，请使用结束任务按钮。',6000)
            return False

    def _sync_stop_shortcut(self):
        busy=self.command_thread.isRunning() or bool(getattr(self,'task_scheduler',None) and self.task_scheduler.busy)
        if busy:
            self._arm_escape_stop()
            return
        self.escape_stop.setEnabled(False)
        if self._escape_registered:
            try:
                self.hk_stop.unregister(self._escape_hotkey)
                if self._escape_previous_action:
                    action = self._escape_previous_action
                    self.hk_stop.register(self._escape_hotkey, callback=lambda *_: self.shortcut_requested.emit(action), overwrite=True)
            except Exception as error:
                self.statusBar.showMessage(f'恢复结束运行2快捷键失败：{error}', 5000)
            finally:
                self._escape_registered = False
                self._escape_hotkey = None

    def _show_runtime_error(self, request):
        if self.command_thread._stop_requested:
            request['event'].set()
            return
        box = QMessageBox(self)
        box.setWindowTitle('指令执行异常')
        box.setText(request['text'])
        box.setIcon(QMessageBox.Warning)
        buttons = QMessageBox.Abort
        if request['retry']:
            buttons |= QMessageBox.Retry | QMessageBox.Ignore
        box.setStandardButtons(buttons)
        box.setWindowModality(Qt.NonModal)
        def resolved(result):
            request['action'] = {int(QMessageBox.Retry): 'retry',
                                 int(QMessageBox.Ignore): 'continue'}.get(result, 'stop')
            request['event'].set()
            if self._runtime_error_box is box:
                self._runtime_error_box = None
            box.deleteLater()
        box.finished.connect(resolved)
        self._runtime_error_box = box
        self.show()
        box.show()

    def _capture_run_window_state(self):
        self._run_window_snapshot = (self.saveGeometry(), self.windowState(),
                                     self.view_workspace.tabs.currentIndex())

    def _restore_run_window_state(self):
        saved = getattr(self, '_run_window_snapshot', None)
        if saved is not None:
            self.restoreGeometry(saved[0])
            self.setWindowState(saved[1])
            self.view_workspace.tabs.setCurrentIndex(saved[2])
            self._run_window_snapshot = None
        self.show()

    def _runtime_finished(self):
        self._flush_runtime_messages(all_pending=True)
        if getattr(self, '_closing', False):
            return
        if self.command_thread.isRunning():
            return
        self.view_workspace.end_runtime_view()
        self.run_unconnected_checkbox.setEnabled(True)
        self._sync_stop_shortcut()
        self._restore_run_window_state()
        self.raise_()
        self.activateWindow()

    @Slot(str, str)
    def _follow_running_command(self, _type_id: str, command_id: str) -> None:
        self.view_workspace.highlight_running_command(command_id)

    def clear_textEdit(self):
        """清空日志，主要用于在全局快捷键线程中调用，避免线程阻塞引发的程序闪退"""
        self._runtime_message_timer.stop()
        self._runtime_messages.clear()
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
        self._flush_runtime_messages(all_pending=True)
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
        busy = self.command_thread.isRunning() or bool(getattr(self, 'task_scheduler', None) and self.task_scheduler.busy)
        if i_str == '启停共享按键':
            i_str = '终止线程' if busy else '开始线程'
        scheduler = getattr(self, 'task_scheduler', None)
        if i_str == '开始线程' and (self.command_thread.isRunning() or (scheduler and scheduler.blocks_main_start)):
            return
        if i_str == '终止线程' and not busy:
            agent = getattr(self.view_workspace, 'agent_page', None)
            if not bool(agent and agent.busy) and getattr(self.workspace, '_instruction_test_context', None) is None:
                return
        self.db.system_prompt_tone("全局快捷键")  # 发出提示音

        if i_str == "终止线程":
            agent = getattr(self.view_workspace, 'agent_page', None)
            if agent is not None and agent.busy:
                agent.stop()
            test_context = getattr(self.workspace, "_instruction_test_context", None)
            if test_context is not None:
                test_context.stop_requested = True
            if getattr(self, "task_scheduler", None):
                self.task_scheduler.stop()
            if self.command_thread.isRunning():
                self.command_thread.request_stop()
                if self._runtime_error_box is not None:
                    self._runtime_error_box.reject()
                self.send_message("已请求停止，正在释放运行资源。")
                if self.isMinimized():
                    self.showNormal()
                else:
                    self.show()
                self.raise_()
                self.activateWindow()

        elif i_str == "开始线程":
            if self.start('全部指令', 0):  # 开始线程
                self.send_message("任务开始！")

        elif i_str == "暂停和恢复线程":
            scheduled = getattr(getattr(self, "task_scheduler", None), "worker", None)
            if scheduled is not None:
                scheduled.resume() if scheduled.is_paused else scheduled.pause()
                return
            if self.command_thread.isRunning():
                if self.command_thread.is_paused:
                    self.send_message("任务恢复！")
                    self.command_thread.resume()
                else:
                    self.send_message("任务暂停！")
                    self.command_thread.pause()

    def send_message(self, message):
        """向日志窗口发送信息"""
        color = self.view_workspace.THEMES[self.view_workspace.theme_mode]["accent"]
        time_message = f'<font color="{color}">{get_str_now_time()}</font>'
        escaped = html.escape(str(message)).replace("\n", "<br>")
        text_ = (f"{time_message}&nbsp;&nbsp;&nbsp;&nbsp;{escaped}"
                 if message != "换行" else "<br>")
        self._runtime_messages.append(text_)
        scheduled = getattr(getattr(self, "task_scheduler", None), "worker", None)
        if self.command_thread.isRunning() or (scheduled is not None and scheduled.isRunning()):
            if not self._runtime_message_timer.isActive():
                self._runtime_message_timer.start()
        else:
            self._flush_runtime_messages(all_pending=True)

    def _flush_runtime_messages(self, all_pending=False):
        count_ = len(self._runtime_messages) if all_pending else min(128, len(self._runtime_messages))
        if count_:
            text_ = "".join(f"<p>{self._runtime_messages.popleft()}</p>" for _ in range(count_))
            self.textEdit.append(text_)
        if not self._runtime_messages:
            self._runtime_message_timer.stop()

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
        self._flush_runtime_messages(all_pending=True)
        if self.checkBox_2.isChecked():  # 显示窗口
            self.show()
            QApplication.processEvents()
        self.db.system_prompt_tone("线程结束")  # 发出提示音
        self.db.show_normal_window_with_specified_title(self.windowTitle())  # 显示窗口

class About(InformationDialog, Ui_About):
    """关于窗体"""

    def __init__(self, parent: Optional[Main_window] = None):
        super().__init__(parent)
        # 初始化窗体
        self.setupUi(self)
        self.db = getattr(parent, "db", None) or DatabaseOperation()
        install_window_state(self, self.db, self.windowTitle())
        self.label_2.setText(f'版本：{CURRENT_VERSION}<br>'
            '国际官网地址1：<a href="https://www.anclicker.com">www.anclicker.com</a><br>'
            '国内官网地址：<a href="https://www.anclicker.eogee.com">www.anclicker.eogee.com</a>')
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setWordWrap(True)
        self.gridLayout.removeItem(self.horizontalSpacer_7)
        self.gridLayout.removeItem(self.horizontalSpacer_8)
        self.gridLayout.removeWidget(self.label_2)
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 3)
        self.label_7.setText('<a href="{}"><font color="red">{}</font></a>'.format(QQ_GROUP, QQ))
        self.label_9.setText('<a href="{}"><font color="red">{}</font></a>'.format(QQ_GROUP_OLD, QQ_OLD))
        self.label_4.setText(
            "<b>贡献者：</b>{}　　{}<br>"
            "<b>QQ：</b>{}　　{}<br>"
            "<b>邮箱：</b><a href=\"mailto:{}\">{}</a>　　"
            "<a href=\"mailto:{}\">{}</a><br>"
            "<br>"
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

        style_about_dialog(self, parent)

    def closeEvent(self, event):
        super().closeEvent(event)
