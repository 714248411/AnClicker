"""Linked Clicker workspaces and the light/dark desktop themes."""

from __future__ import annotations
from anclicker.ui.workspace_constants import MAIN_VIEW, TABLE_VIEW, FLOW_VIEW, CODE_VIEW, RECORDING_VIEW, WEB_RECORDING_VIEW, AGENT_VIEW, CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING, TASK_NAME_SETTING, WINDOW_TITLE_SETTING, THEME_SETTING

from anclicker.ui.theme import THEMES, apply_theme

import hashlib
import json
import os

from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QSize, QSignalBlocker, Signal, Qt, QTimer, QMimeData, QItemSelectionModel
from anclicker.platform.qt_compat.QtGui import QAction, QColor, QGuiApplication, QKeySequence, QPalette, QPixmap, QDrag, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QTextEdit,
    QPushButton,
    QSplitter,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTabBar,
    QTableWidget,
    QStyledItemDelegate,
    QStyle,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from anclicker.instructions.registry import iter_instruction_specs
from anclicker.ui.node_editor.palette import INSTRUCTION_MIME_TYPE
from anclicker.app.paths import RESOURCE_FOLDER
from anclicker.ui.recording_view import RecordingView
from anclicker.ui.web_recording_view import WebRecordingView




from anclicker.ui.instruction_table import CommentRowDelegate, InstructionTableWidget, InstructionTableController
from anclicker.ui.navigation import NavigationController
from anclicker.ui.code_workspace import CodeWorkspace


from anclicker.ui.navigation import _ToolbarDockOnDoubleClick

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'DockWorkspace': ('from', 'anclicker.ui.dock_workspace', ('DockWorkspace',), 0),
    'InterfaceScale': ('from', 'anclicker.ui.interface_scale', ('InterfaceScale',), 0),
    'WorkspaceTabBar': ('from', 'anclicker.ui.workspace_tabs', ('WorkspaceTabBar',), 0),
    'AgentView': ('from', 'anclicker.ui.agent_view', ('AgentView',), 0),
    'HomeWorkspace': ('from', 'anclicker.ui.home_workspace', ('HomeWorkspace',), 0),
    'VariablePool_Win': ('from', 'anclicker.ui.dialogs.变量池窗口', ('VariablePool_Win',), 0),
    'FlowTips': ('from', 'anclicker.ui.flow_tips', ('FlowTips',), 0),
})



class ViewWorkspace:
    """Coordinate pages, palette layout and application theme."""

    THEMES = THEMES

    def _install_controllers(self):
        """Compose page behavior while widgets remain owned by the workspace."""
        self.instruction_table_controller = InstructionTableController(self)
        self.navigation_controller = NavigationController(self)
        self.code_workspace_controller = CodeWorkspace(self)

    def __init__(self, window):
        self._install_controllers()
        self.window = window
        self.tabs = window.tabWidget
        self._loading_code = False
        self._code_dirty = False
        self._code_save_timer = QTimer(window)
        self._code_save_timer.setSingleShot(True)
        self._code_save_timer.setInterval(350)
        self._code_save_timer.timeout.connect(self._save_code)
        self._table_rows = []
        self._table_command_rows = {}
        self.running_command_id = None
        self.theme_mode = str(window.db.get_setting_value(THEME_SETTING) or "light")
        if self.theme_mode not in self.THEMES:
            self.theme_mode = "light"
        self.palette_side = "left"
        self.palette_collapsed = False
        self.controls_collapsed = str(window.db.get_setting_value('控制与操作收起') or 'False').lower() == 'true'
        guidance = str(window.db.get_setting_value('中文编程提示') or 'True').lower() not in ('false', '0', '关闭')
        window.workspace.palette.set_guidance_enabled(guidance)
        window.workspace.palette.guidanceEnabledChanged.connect(
            lambda enabled: window.db.set_setting_value('中文编程提示', str(enabled)))
        try:
            order = json.loads(window.db.get_setting_value('指令栏置顶顺序') or '{}')
        except (TypeError, ValueError):
            order = {}
        window.workspace.palette.restore_instruction_order(order)
        window.workspace.palette.orderChanged.connect(
            lambda order: window.db.set_setting_value('指令栏置顶顺序', json.dumps(order, ensure_ascii=False)))
        self._normalize_existing_controls()
        self._apply_theme()
        self._assemble_views()
        # The first pass themes widgets loaded from the .ui file; this pass
        # also covers the table/code/navigation widgets created above.
        self._apply_theme()
        self.window.workspace.graphFinalized.connect(self._graph_finalized)
        self._build_navigation()
        self.tabs.currentChanged.connect(self._view_changed)
        self._sync_code_if_needed()
        self.show_main()
        self._view_changed(self.tabs.currentIndex())
        DockWorkspace = _module_imports.load('DockWorkspace')
        self.docking = DockWorkspace(self)
        self.docking.sync_visibility()
        InterfaceScale = _module_imports.load('InterfaceScale')
        self.interface_scale = InterfaceScale(self.window)

    def _normalize_existing_controls(self) -> None:
        """Remove legacy hard-coded colors so both themes stay coherent."""
        for widget in (
            self.window.textEdit,
            self.window.pushButton_3,
            self.window.pushButton_5,
            self.window.pushButton_6,
            self.window.pushButton_7,
        ):
            widget.setStyleSheet("")
        self.window.pushButton_5.setObjectName("accentButton")
        self.window.pushButton_6.setObjectName("dangerButton")
        self.window.textEdit.setReadOnly(True)
        self.window.groupBox_3.setStyleSheet('')
        status = self.window.statusBar
        status.setSizeGripEnabled(False)
        status.setFixedHeight(max(18, status.fontMetrics().height() + 2))
        status.messageChanged.connect(self._sync_status_visibility)
        self._sync_status_visibility(status.currentMessage())
        self.window.gridLayout_4.setContentsMargins(4, 3, 4, 8)
        self.window.gridLayout_4.setSpacing(4)
        self.tabs.setMinimumWidth(0)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.window.instructionPaletteHost.setMinimumWidth(120)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.window.textEdit.setMinimumHeight(0)
        self.window.textEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)

    def _sync_status_visibility(self, message):
        compact = getattr(getattr(self, 'compact', None), 'active', False)
        self.window.statusBar.setVisible(bool(message) and not compact)

    def _assemble_views(self) -> None:
        self.table_page = self.window.tab
        self._build_table_view()
        self.main_page = self._build_main_view()
        self.editor_page = self._build_editor_view()
        self.code_page = self._build_code_view()
        self.recording_page = RecordingView(self.window)
        self.tabs.clear()
        WorkspaceTabBar = _module_imports.load('WorkspaceTabBar')
        self.tabs.setObjectName("workspaceTabs")
        self.tabs.setTabBar(WorkspaceTabBar(self.tabs))
        self.tabs.tabBar().setExpanding(False)
        self.tabs.addTab(self.main_page, "主界面")
        self.tabs.addTab(self.table_page, "表格图")
        self.tabs.addTab(self.editor_page, "流程图")
        self.tabs.addTab(self.code_page, "多功能")
        self.tabs.addTab(self.recording_page, "录制")
        self.web_recording_page = WebRecordingView(self.window)
        self.tabs.addTab(self.web_recording_page, "网页录制")
        AgentView = _module_imports.load('AgentView')
        self.agent_page = AgentView(self.window)
        self.tabs.addTab(self.agent_page, "对话 Agent")

    def _build_main_view(self) -> QWidget:
        HomeWorkspace = _module_imports.load('HomeWorkspace')
        page = HomeWorkspace(self)
        self.main_stats = page.summary
        return page

    def _build_beginner_view(self) -> QWidget:
        page = QWidget()
        page.setObjectName("beginnerView")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        nav_frame = QFrame()
        nav_frame.setObjectName("viewNavigation")
        nav_layout = QVBoxLayout(nav_frame)
        nav_title = QLabel("功能导航")
        nav_title.setObjectName("navTitle")
        nav_layout.addWidget(nav_title)
        self.beginner_nav = QListWidget()
        self.beginner_nav.setObjectName("beginnerNavigation")
        for text in ("任务", "窗口绑定", "图色", "录制", "AI 识图", "DLL", "变量"):
            self.beginner_nav.addItem(text)
        nav_layout.addWidget(self.beginner_nav, 1)
        layout.addWidget(nav_frame)
        self.beginner_stack = QStackedWidget()
        self.beginner_stack.addWidget(self._build_task_panel())
        self.beginner_stack.addWidget(self._build_binding_panel())
        self.beginner_stack.addWidget(self._build_action_panel(
            "图色与资源", "统一管理模板图片和外部资源目录。",
            (("设置资源文件夹", lambda: self.window.show_windows("全局")),
             ("添加图像点击指令", lambda: self.window.workspace.add_command("图像点击"))),
        ))
        self.beginner_stack.addWidget(self._build_action_panel(
            "操作录制", "录制实际键盘鼠标操作，停止后同步写入表格与流程图。",
            (("打开键鼠录制", self.show_recording),
             ("添加鼠标点击", lambda: self.window.workspace.add_command("鼠标点击")),
             ("添加按键指令", lambda: self.window.workspace.add_command("按下键盘")),
             ("打开流程图", self.show_flow)),
        ))
        self.beginner_stack.addWidget(self._build_action_panel(
            "AI 识图", "使用现有 OCR 与图像匹配指令完成离线识别流程。",
            (("添加 OCR 识别", lambda: self.window.workspace.add_command("OCR识别")),
             ("添加图像等待", lambda: self.window.workspace.add_command("图像等待"))),
        ))
        self.beginner_stack.addWidget(self._build_action_panel(
            "DLL 与外部能力", "可通过运行 Python、CMD 或外部文件指令接入本地组件。",
            (("运行 Python", lambda: self.window.workspace.add_command("运行Python")),
             ("运行外部文件", lambda: self.window.workspace.add_command("运行外部文件"))),
        ))
        self.beginner_stack.addWidget(self._build_action_panel(
            '变量管理', '自定义全局变量与普通变量，供获取时间、剪切板、Excel、条件判断等指令使用。',
            (('设置变量', self.show_variables),
             ('添加获取时间', lambda: self.window.workspace.add_command('获取时间'))),
        ))
        self.beginner_nav.currentRowChanged.connect(self.beginner_stack.setCurrentIndex)
        self.beginner_nav.setCurrentRow(0)
        layout.addWidget(self.beginner_stack, 1)
        return page

    def _card(self, title: str, description: str = ""):
        card = QFrame()
        card.setObjectName("contentCard")
        layout = QVBoxLayout(card)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        if description:
            detail = QLabel(description)
            detail.setObjectName("mutedText")
            detail.setWordWrap(True)
            layout.addWidget(detail)
        return card, layout

    def show_variables(self):
        if self.window.command_thread.isRunning():
            QMessageBox.information(self.window, '任务正在运行', '请停止任务后再修改变量定义。')
            return
        VariablePool_Win = _module_imports.load('VariablePool_Win')
        manager = VariablePool_Win(self.window, database=self.window.db)
        manager.exec()

    def _build_task_panel(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card, card_layout = self._card("当前任务", "名称、流程、代码和运行控制实时联动。")
        form = QFormLayout()
        self.task_name = QLineEdit(str(self.window.db.get_setting_value(TASK_NAME_SETTING) or "默认任务"))
        self.task_name.editingFinished.connect(self._save_task_name)
        form.addRow("任务名称", self.task_name)
        card_layout.addLayout(form)
        self.stats = QLabel()
        self.stats.setObjectName("taskStats")
        self.stats.setWordWrap(True)
        card_layout.addWidget(self.stats)
        buttons = QHBoxLayout()
        edit_button = QPushButton("打开流程图")
        edit_button.setObjectName("accentButton")
        edit_button.clicked.connect(self.show_flow)
        table_button = QPushButton("打开表格图")
        table_button.clicked.connect(self.show_table)
        code_button = QPushButton("打开多功能代码")
        code_button.clicked.connect(self.show_code)
        for button in (edit_button, table_button, code_button):
            buttons.addWidget(button)
        card_layout.addLayout(buttons)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_binding_panel(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card, card_layout = self._card("窗口绑定", "保存目标窗口标题，供窗口控制和自动化指令统一使用。")
        form = QFormLayout()
        self.window_title = QLineEdit(str(self.window.db.get_setting_value(WINDOW_TITLE_SETTING) or ""))
        self.window_title.setPlaceholderText("输入目标窗口标题")
        form.addRow("窗口标题", self.window_title)
        card_layout.addLayout(form)
        save_button = QPushButton("保存绑定")
        save_button.setObjectName("accentButton")
        save_button.clicked.connect(self._save_window_binding)
        card_layout.addWidget(save_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_action_panel(self, title, description, actions) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card, card_layout = self._card(title, description)
        for label, callback in actions:
            button = QPushButton(label)
            button.clicked.connect(callback)
            card_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_table_view(self) -> None:
        return self.instruction_table_controller._build_table_view()

    def _build_editor_view(self) -> QWidget:
        page = QWidget()
        page.setObjectName("editorView")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        FlowTips = _module_imports.load('FlowTips')
        self.flow_tips = FlowTips(self.window, page)
        layout.addWidget(self.flow_tips)
        self.window.nodeEditorLayout.removeWidget(self.window.workspace.editor)
        self.window.workspace.editor.setParent(page)
        self.flow_splitter = QSplitter(Qt.Orientation.Vertical)
        self.flow_splitter.setChildrenCollapsible(False)
        self.flow_splitter.setHandleWidth(4)
        self.flow_splitter.addWidget(self.window.workspace.editor)
        self.flow_log_panel = QFrame()
        self.flow_log_panel.setObjectName("workspacePanel")
        log_layout = QVBoxLayout(self.flow_log_panel)
        log_layout.setContentsMargins(6, 4, 6, 4)
        heading = QLabel("运行日志")
        heading.setObjectName("sectionTitle")
        log_layout.addWidget(heading)
        self.flow_log = QTextEdit()
        self.flow_log.setReadOnly(True)
        self.flow_log.setDocument(self.window.textEdit.document())
        self.flow_log.document().contentsChanged.connect(
            lambda: self.flow_log.verticalScrollBar().setValue(self.flow_log.verticalScrollBar().maximum()))
        log_layout.addWidget(self.flow_log)
        self.flow_splitter.addWidget(self.flow_log_panel)
        self.flow_splitter.setStretchFactor(0, 4)
        self.flow_splitter.setStretchFactor(1, 1)
        self.flow_log_panel.hide()
        layout.addWidget(self.flow_splitter, 1)
        return page

    def begin_runtime_view(self):
        self._runtime_view_serial = getattr(self, '_runtime_view_serial', 0) + 1
        self._runtime_fit_pending = True
        self._runtime_view_active = True
        self.refresh_table()
        view = self.window.workspace.editor.view
        self._flow_view_before_run = (view.transform(), view.horizontalScrollBar().value(),
                                     view.verticalScrollBar().value())
        self.flow_log_panel.show()
        height = max(300, self.flow_splitter.height())
        self.flow_splitter.setSizes([int(height * .75), int(height * .25)])
        self._schedule_runtime_fit()

    def _schedule_runtime_fit(self):
        if not getattr(self, '_runtime_view_active', False) or not getattr(self, '_runtime_fit_pending', False):
            return
        serial = self._runtime_view_serial
        def fit_after_layout():
            if serial != self._runtime_view_serial or not self._runtime_view_active:
                return
            if self.tabs.currentIndex() != FLOW_VIEW or not self.flow_log_panel.isVisible():
                return
            self.editor_page.layout().activate()
            self.window.workspace.editor.view.fit_graph()
            self._runtime_fit_pending = False
            self.window.workspace.editor.view.viewport().update()
        QTimer.singleShot(0, fit_after_layout)

    def end_runtime_view(self):
        self._runtime_view_serial = getattr(self, '_runtime_view_serial', 0) + 1
        serial = self._runtime_view_serial
        self._runtime_fit_pending = False
        self._runtime_view_active = False
        self.flow_log_panel.hide()
        for node in self.window.workspace.editor.scene.nodes_by_id.values():
            node.runtime_active = False
            node.update()
        self.window.workspace.editor.view.viewport().update()
        saved = getattr(self, '_flow_view_before_run', None)
        if saved is not None:
            view = self.window.workspace.editor.view
            view.setTransform(saved[0])
            view._zoom = saved[0].m11()
            view.zoomChanged.emit(view._zoom * 100)
            def restore_scroll():
                if serial != self._runtime_view_serial or self._runtime_view_active:
                    return
                view.horizontalScrollBar().setValue(saved[1])
                view.verticalScrollBar().setValue(saved[2])
            QTimer.singleShot(0, restore_scroll)


    def _build_code_view(self) -> QWidget:
        return self.code_workspace_controller._build_code_view()

    def _build_navigation(self) -> None:
        return self.navigation_controller._build_navigation()

    def toggle_primary(self) -> None:
        return self.navigation_controller.toggle_primary()

    def _show_workspace(self, index):
        return self.navigation_controller._show_workspace(index)

    def show_main(self):
        return self.navigation_controller.show_main()
    def show_table(self):
        return self.navigation_controller.show_table()
    def show_flow(self):
        return self.navigation_controller.show_flow()
    def show_code(self):
        return self.navigation_controller.show_code()
    def show_navigation(self):
        return self.navigation_controller.show_navigation()
    def show_recording(self):
        return self.navigation_controller.show_recording()

    def show_web_recording(self):
        return self.navigation_controller.show_web_recording()

    def show_agent(self):
        return self.navigation_controller.show_agent()

    # Backward-compatible aliases for integrations that used the earlier names.
    def show_beginner(self):
        return self.navigation_controller.show_beginner()
    def show_editor(self):
        return self.navigation_controller.show_editor()

    def toggle_palette_side(self) -> None:
        self.palette_side = "right" if self.palette_side == "left" else "left"
        if hasattr(self, 'docking'): self.docking.move_palette_side(self.palette_side)
        self._place_palette()

    def toggle_palette(self) -> None:
        self.palette_collapsed = not self.palette_collapsed
        self._place_palette()

    def toggle_theme(self) -> None:
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.window.db.set_setting_value(THEME_SETTING, self.theme_mode)
        self._apply_theme()
        self.refresh_table()
        self._update_view_actions()

    def show_donation(self) -> None:
        """Show the bundled donation QR code without opening a web page."""
        image_path = os.path.join(RESOURCE_FOLDER, "resources", "images", "windows", "donation_qr.png")
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(self.window, "捐赠", "捐赠二维码加载失败，请检查程序资源。")
            return

        dialog = QDialog(self.window)
        dialog.setObjectName("donationDialog")
        dialog.setWindowTitle("捐赠")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(12)
        image = QLabel(dialog)
        image.setObjectName("donationQrCode")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setPixmap(
            pixmap.scaled(
                QSize(435, 381),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        close_button = QPushButton("关闭", dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(image)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignCenter)
        dialog.exec()

    def _place_palette(self) -> None:
        if hasattr(self, 'docking'):
            self.docking.sync_visibility()
            self._update_view_actions()
            return
        if getattr(getattr(self, 'compact', None), 'active', False):
            return
        grid = self.window.gridLayout_4
        if not hasattr(self, 'controls_scroll'):
            controls = self.window.groupBox_3
            grid.removeWidget(controls)
            self.controls_scroll = QScrollArea()
            self.controls_scroll.setObjectName('controlsScroll')
            self.controls_scroll.viewport().setObjectName('controlsScrollViewport')
            self.controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
            self.controls_scroll.setWidgetResizable(True)
            controls.setMinimumWidth(280)
            for label in controls.findChildren(QLabel):
                label.setWordWrap(True)
                label.setMinimumWidth(0)
            self.controls_scroll.setMinimumSize(300, 0)
            self.controls_scroll.setWidget(controls)
        palette, center, controls = self.window.instructionPaletteHost, self.tabs, self.controls_scroll
        if not hasattr(self, 'workspace_splitter'):
            self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.workspace_splitter.setObjectName('workspaceSplitter')
            self.workspace_splitter.setChildrenCollapsible(False)
            self.workspace_splitter.setHandleWidth(8)
            for widget in (palette, center, controls):
                grid.removeWidget(widget)
                self.workspace_splitter.addWidget(widget)
            grid.addWidget(self.workspace_splitter, 0, 0, 1, 3)
            self._panel_sizes = {'palette':240, 'center':800, 'controls':300}
            try:
                saved = json.loads(self.window.db.get_setting_value('工作区面板宽度') or '{}')
                if isinstance(saved, dict):
                    self._panel_sizes.update({k:v for k,v in saved.items() if k in self._panel_sizes and isinstance(v,int) and 80<=v<=10000})
            except (TypeError, ValueError): pass
            self.workspace_splitter.splitterMoved.connect(self._save_panel_sizes)
        order = ((palette, 'palette'), (center, 'center'), (controls, 'controls')) if self.palette_side == 'left' else ((center, 'center'), (palette, 'palette'), (controls, 'controls'))
        for index, (widget, key) in enumerate(order):
            if self.workspace_splitter.widget(index) is not widget:
                self.workspace_splitter.insertWidget(index, widget)
            self.workspace_splitter.setStretchFactor(index, int(widget is center))
        self.workspace_splitter.setSizes([self._panel_sizes[key] for widget,key in order])
        palette.setVisible(
            self.tabs.currentIndex() in (TABLE_VIEW, FLOW_VIEW)
            and not self.palette_collapsed
        )
        controls.setVisible(not self.controls_collapsed)
        self._update_view_actions()

    def set_controls_visible(self, visible):
        self.controls_collapsed = not visible
        self.window.db.set_setting_value('控制与操作收起', str(self.controls_collapsed))
        if hasattr(self, 'controls_scroll') and not self.compact.active:
            self.controls_scroll.setVisible(visible)
        if hasattr(self, 'docking'): self.docking.sync_visibility()
        self._update_view_actions()

    def _save_panel_sizes(self, *_):
        if getattr(getattr(self, 'compact', None), 'active', False): return
        splitter = self.workspace_splitter
        for widget,key in ((self.window.instructionPaletteHost,'palette'),(self.tabs,'center'),(self.controls_scroll,'controls')):
            size = splitter.sizes()[splitter.indexOf(widget)]
            if size > 0: self._panel_sizes[key] = size
        self.window.db.set_setting_value('工作区面板宽度', json.dumps(self._panel_sizes))

    def _update_view_actions(self) -> None:
        self.primary_action.setText(
            {FLOW_VIEW: "打开表格图", TABLE_VIEW: "打开多功能"}.get(
                self.tabs.currentIndex(), "打开流程图")
        )
        self.palette_side_action.setText(
            "指令栏移到左侧" if self.palette_side == "right" else "指令栏移到右侧"
        )
        self.palette_collapse_action.setText(
            "展开指令栏" if self.palette_collapsed else "收起指令栏"
        )
        self.controls_action.setText('展开控制栏' if self.controls_collapsed else '收起控制栏')
        self.controls_action.setToolTip(self.controls_action.text())
        self.theme_action.setText("切换深色" if self.theme_mode == "light" else "切换浅色")

    def _remembered_pages(self):
        return {
            'main': self.main_page,
            'table': self.table_page,
            'flow': self.editor_page,
            'code': self.code_page,
            'recording': self.recording_page,
            'web_recording': self.web_recording_page,
            'agent': self.agent_page,
        }

    def restore_last_view(self):
        # A missing or obsolete preference starts at the main page.
        key = str(self.window.db.get_setting_value('上次关闭界面') or 'main')
        keys = list(self._remembered_pages())
        self._show_workspace(keys.index(key) if key in keys else MAIN_VIEW)

    def save_last_view(self):
        if hasattr(self, 'docking'): self.docking.save()
        keys = list(self._remembered_pages())
        index = self.tabs.currentIndex()
        key = keys[index] if 0 <= index < len(keys) else 'main'
        self.window.db.set_setting_value('上次关闭界面', key)

    def _view_changed(self, index: int) -> None:
        # Navigation chooses the useful default; explicit layout presets retain
        # their saved visibility until the user next changes pages.
        if not getattr(getattr(self, 'docking', None), 'restoring', False):
            if index == MAIN_VIEW:
                self.palette_collapsed = True
            elif index in (TABLE_VIEW, FLOW_VIEW):
                self.palette_collapsed = False
        self._place_palette()
        if index == MAIN_VIEW: self.refresh_summary()
        elif index == TABLE_VIEW: self.refresh_table()
        elif index == FLOW_VIEW:
            self.highlight_running_command(self.running_command_id)
            self._schedule_runtime_fit()
        elif index == CODE_VIEW: self._load_code()

    def refresh_all(self) -> None:
        checkbox = getattr(self.window, 'run_unconnected_checkbox', None)
        if checkbox is not None:
            with QSignalBlocker(checkbox):
                checkbox.setChecked(self.window.db.get_setting_value('运行未连接模块') != 'False')
        self._sync_code_if_needed()
        self.refresh_summary()
        self.refresh_table()

    def refresh_summary(self) -> None:
        try:
            snapshot = self.window.workspace.repository.snapshot()
            code_lines = len(self.code_editor.toPlainText().splitlines())
            summary = (
                f"可执行指令  {len(snapshot.commands)} 条    ·    流程节点  {len(snapshot.nodes)} 个    ·    "
                f"多功能代码  {code_lines} 行"
            )
            self.main_stats.setText(summary)
            self.main_page.refresh_projects()
        except Exception as error:
            summary = f"任务状态暂不可用：{error}"
            self.main_stats.setText(summary)

    def refresh_table(self) -> None:
        return self.instruction_table_controller.refresh_table()

    def _apply_comment_row_colors(self, snapshot):
        return self.instruction_table_controller._apply_comment_row_colors(snapshot)

    def highlight_running_command(self, command_id, *, ensure_visible=True) -> None:
        """Follow stable command IDs without changing the editing selection."""
        try:
            self.running_command_id = int(command_id) if command_id is not None else None
        except (TypeError, ValueError):
            self.running_command_id = None
        editor = self.window.workspace.editor
        active = editor.scene.nodes_by_command_id.get(self.running_command_id)
        for node in editor.scene.nodes_by_id.values():
            marked = node is active and getattr(self, '_runtime_view_active', False)
            if getattr(node, 'runtime_active', False) != marked:
                node.runtime_active = marked
                node.update()
        if active is not None and getattr(self, '_runtime_view_active', False) and ensure_visible and self.tabs.currentIndex() == FLOW_VIEW:
            editor.view.ensureVisible(active, 32, 32)
        editor.view.viewport().update()
        table = self.command_table
        table.runtime_row = self._table_command_rows.get(self.running_command_id, -1)
        if table.runtime_row >= 0 and table.isRowHidden(table.runtime_row):
            for header in table.collapsed_loops | table.collapsed_comments:
                members = table.loop_ranges.get(header, set()) | set(table.comment_ranges.get(header, ()))
                row = self._table_command_rows.get(header, -1)
                if self.running_command_id in members and row >= 0 and not table.isRowHidden(row):
                    table.runtime_row = row
                    break
        if ensure_visible and table.runtime_row >= 0 and self.tabs.currentIndex() == TABLE_VIEW:
            table.scrollToItem(table.item(table.runtime_row, 0), QAbstractItemView.ScrollHint.EnsureVisible)
        table.viewport().update()

    def _add_table_command(self, type_id: str) -> None:
        return self.instruction_table_controller._add_table_command(type_id)

    def _graph_finalized(self, complete: bool) -> None:
        self._sync_code_if_needed(force=True)
        self.refresh_summary()
        self.refresh_table()
        self.code_status.setText("流程、表格与多功能已同步" if complete else "已同步流程草稿，可按连线优先、其余按添加顺序运行")

    def _edit_table_command(self, row: int, _column: int) -> None:
        return self.instruction_table_controller._edit_table_command(row, _column)

    def _table_mutation_allowed(self):
        return self.instruction_table_controller._table_mutation_allowed()

    def delete_table_commands(self):
        return self.instruction_table_controller.delete_table_commands()

    def copy_table_commands(self):
        return self.instruction_table_controller.copy_table_commands()

    def paste_table_commands(self):
        return self.instruction_table_controller.paste_table_commands()

    def _select_table_ids(self, ids):
        return self.instruction_table_controller._select_table_ids(ids)

    def move_table_commands(self, ids, destination):
        return self.instruction_table_controller.move_table_commands(ids, destination)

    def _save_task_name(self) -> None:
        name = self.task_name.text().strip() or "默认任务"
        self.task_name.setText(name)
        self.window.db.set_setting_value(TASK_NAME_SETTING, name)
        self.window.statusBar.showMessage(f"任务名称已保存：{name}", 3000)

    def _save_window_binding(self) -> None:
        self.window.db.set_setting_value(WINDOW_TITLE_SETTING, self.window_title.text().strip())
        self.window.statusBar.showMessage("窗口绑定已保存。", 3000)

    def _load_code(self) -> None:
        return self.code_workspace_controller._load_code()

    def write_code_to_flow(self) -> None:
        return self.code_workspace_controller.write_code_to_flow()

    def regenerate_code(self) -> None:
        return self.code_workspace_controller.regenerate_code()

    def _current_graph_state(self):
        return self.code_workspace_controller._current_graph_state()

    @staticmethod
    def _graph_signature(snapshot) -> str:
        return CodeWorkspace._graph_signature(snapshot)

    def _sync_code_if_needed(self, *, force: bool=False) -> bool:
        return self.code_workspace_controller._sync_code_if_needed(force=force)

    def _generated_code(self, snapshot=None, validation_error=None) -> str:
        return self.code_workspace_controller._generated_code(snapshot, validation_error)

    def _insert_command_hint(self, item: QListWidgetItem) -> None:
        return self.code_workspace_controller._insert_command_hint(item)

    def _schedule_code_save(self) -> None:
        return self.code_workspace_controller._schedule_code_save()

    def _save_code(self) -> None:
        return self.code_workspace_controller._save_code()

    def _align_search_row(self):
        palette = self.window.workspace.palette
        palette.search_edit.ensurePolished()
        height = palette.search_edit.fontMetrics().height() + 4
        palette.search_edit.setFixedHeight(height)
        palette.search_row.setFixedHeight(max(height + 2, self.tabs.tabBar().sizeHint().height()))

    def _apply_theme(self):
        apply_theme(self)
