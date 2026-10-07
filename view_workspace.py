"""Linked Clicker workspaces and the light/dark desktop themes."""

from __future__ import annotations

import hashlib
import json
import os

from PySide6.QtCore import QSize, QSignalBlocker, Signal, Qt, QTimer, QMimeData
from PySide6.QtGui import QAction, QColor, QGuiApplication, QKeySequence, QPalette, QPixmap, QDrag
from PySide6.QtWidgets import (
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
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from instructions.registry import iter_instruction_specs
from node_editor.palette import INSTRUCTION_MIME_TYPE
from functions import RESOURCE_FOLDER
from recording_view import RecordingView


MAIN_VIEW = 0
TABLE_VIEW = 1
FLOW_VIEW = 2
CODE_VIEW = 3
NAVIGATION_VIEW = 4
RECORDING_VIEW = 5
CODE_SETTING = "多功能代码"
CODE_GRAPH_SIGNATURE_SETTING = "多功能流程签名"
TASK_NAME_SETTING = "任务名称"
WINDOW_TITLE_SETTING = "绑定窗口标题"
THEME_SETTING = "界面主题"


class InstructionTableWidget(QTableWidget):
    """Command table that accepts instruction MIME drops from the palette."""

    instructionDropped = Signal(str)
    deleteRequested = Signal()
    copyRequested = Signal()
    pasteRequested = Signal()
    rowsMoved = Signal(object, int)
    ROW_MIME = 'application/x-anclicker-table-row'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self._row_press = None
        self._drop_line = QFrame(self.viewport())
        self._drop_line.setStyleSheet('background: #5b6fdc;')
        self._drop_line.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._drop_line.hide()

    def selected_command_ids(self):
        rows = sorted({index.row() for index in self.selectedIndexes()})
        return [int(self.item(row, 0).data(Qt.ItemDataRole.UserRole)) for row in rows
                if self.item(row, 0) is not None]

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copyRequested.emit()
        elif event.matches(QKeySequence.StandardKey.Paste):
            self.pasteRequested.emit()
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and not self.selectionModel().isSelected(index):
            self.clearSelection()
            self.setCurrentCell(index.row(), index.column())
        menu = QMenu(self)
        count = len(self.selected_command_ids())
        copy = menu.addAction(f'复制选中指令（{count} 行）', self.copyRequested.emit)
        copy.setEnabled(count > 0)
        menu.addAction('粘贴指令到表格末尾', self.pasteRequested.emit)
        menu.addSeparator()
        delete = menu.addAction(f'删除选中指令（{count} 行）', self.deleteRequested.emit)
        delete.setEnabled(count > 0)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        self._row_press = None
        index = self.indexAt(event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and index.isValid() and index.column() == 0:
            self.selectRow(index.row())
            self._row_press = (event.position().toPoint(), self.item(index.row(), 0).data(Qt.ItemDataRole.UserRole))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._row_press is not None and event.buttons() & Qt.MouseButton.LeftButton:
            origin, command_id = self._row_press
            if (event.position().toPoint() - origin).manhattanLength() >= QApplication.startDragDistance():
                self._row_press = None
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(self.ROW_MIME, str(command_id).encode('ascii'))
                drag.setMimeData(mime)
                drag.exec(Qt.DropAction.MoveAction)
                self._drop_line.hide()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._row_press = None
        super().mouseReleaseEvent(event)

    def _drop_row(self, event):
        point = event.position().toPoint()
        index = self.indexAt(point)
        if not index.isValid():
            return self.rowCount()
        row = index.row()
        return row + int(point.y() > self.visualRect(index).center().y())

    @staticmethod
    def _type_id(event_):
        if not event_.mimeData().hasFormat(INSTRUCTION_MIME_TYPE):
            return None
        try:
            return bytes(event_.mimeData().data(INSTRUCTION_MIME_TYPE)).decode("utf-8")
        except UnicodeDecodeError:
            return None

    def dragEnterEvent(self, event_):
        if event_.source() is self and event_.mimeData().hasFormat(self.ROW_MIME):
            event_.acceptProposedAction()
        elif self._type_id(event_):
            event_.acceptProposedAction()
        else:
            super().dragEnterEvent(event_)

    def dragMoveEvent(self, event_):
        if event_.source() is self and event_.mimeData().hasFormat(self.ROW_MIME):
            row = self._drop_row(event_)
            y = self.rowViewportPosition(row) if row < self.rowCount() else (
                self.rowViewportPosition(row - 1) + self.rowHeight(row - 1) if row else 0)
            self._drop_line.setGeometry(0, max(0, y - 1), self.viewport().width(), 2)
            self._drop_line.show()
            scroll = self.verticalScrollBar()
            if event_.position().y() < 20:
                scroll.setValue(scroll.value() - 1)
            elif event_.position().y() > self.viewport().height() - 20:
                scroll.setValue(scroll.value() + 1)
            event_.acceptProposedAction()
        elif self._type_id(event_):
            event_.acceptProposedAction()
        else:
            super().dragMoveEvent(event_)

    def dropEvent(self, event_):
        self._drop_line.hide()
        if event_.source() is self and event_.mimeData().hasFormat(self.ROW_MIME):
            command_id = int(bytes(event_.mimeData().data(self.ROW_MIME)).decode('ascii'))
            self.rowsMoved.emit([command_id], self._drop_row(event_))
            event_.acceptProposedAction()
            return
        type_id_ = self._type_id(event_)
        if type_id_:
            self.instructionDropped.emit(type_id_)
            event_.acceptProposedAction()
        else:
            super().dropEvent(event_)

    def dragLeaveEvent(self, event):
        self._drop_line.hide()
        super().dragLeaveEvent(event)


class ViewWorkspace:
    """Coordinate six workspaces, palette layout and application theme."""

    THEMES = {
        "dark": {
            "bg": "#09090b", "nav": "#080809", "surface": "#18181b",
            "surface2": "#222225", "surface3": "#2c2c30", "line": "#2b2b30",
            "text": "#f1f1f3", "dim": "#a1a1aa", "accent": "#0088ff",
            "accent2": "#0965b5", "accent_text": "#ffffff", "danger": "#dc3545",
        },
        "light": {
            "bg": "#f7f7f8", "nav": "#ececf1", "surface": "#ffffff",
            "surface2": "#f1f1f3", "surface3": "#e6e6e9", "line": "#d9d9e0",
            "text": "#2f2f2f", "dim": "#6b6b75", "accent": "#5b6fdc",
            "accent2": "#495bbd", "accent_text": "#ffffff", "danger": "#d94b4b",
        },
    }

    def __init__(self, window):
        self.window = window
        self.tabs = window.tabWidget
        self._loading_code = False
        self._code_dirty = False
        self.theme_mode = str(window.db.get_setting_value(THEME_SETTING) or "light")
        if self.theme_mode not in self.THEMES:
            self.theme_mode = "light"
        self.palette_side = "left"
        self.palette_collapsed = False
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

    def _assemble_views(self) -> None:
        self.table_page = self.window.tab
        self._build_table_view()
        self.navigation_page = self._build_beginner_view()
        self.main_page = self._build_main_view()
        self.editor_page = self._build_editor_view()
        self.code_page = self._build_code_view()
        self.recording_page = RecordingView(self.window)
        self.tabs.clear()
        self.tabs.addTab(self.main_page, "主界面")
        self.tabs.addTab(self.table_page, "表格")
        self.tabs.addTab(self.editor_page, "流程图")
        self.tabs.addTab(self.code_page, "多功能")
        self.tabs.addTab(self.navigation_page, "导航")
        self.tabs.addTab(self.recording_page, "录制")

    def _build_main_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        hero, hero_layout = self._card(
            "An Clicker 自动化工作台",
            "从表格快速维护指令，在流程图中编排连线，或使用多功能代码完成高级操作。",
        )
        self.main_stats = QLabel()
        self.main_stats.setObjectName("taskStats")
        self.main_stats.setWordWrap(True)
        hero_layout.addWidget(self.main_stats)
        buttons = QHBoxLayout()
        for label, callback, primary in (
            ("打开表格", self.show_table, False),
            ("打开流程图", self.show_flow, True),
            ("打开多功能", self.show_code, False),
            ("功能导航", self.show_navigation, False),
            ("键鼠录制", self.show_recording, False),
        ):
            button = QPushButton(label)
            if primary:
                button.setObjectName("accentButton")
            button.clicked.connect(callback)
            buttons.addWidget(button)
        hero_layout.addLayout(buttons)
        layout.addWidget(hero)
        layout.addStretch(1)
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
        from WindowControl.变量池窗口 import VariablePool_Win
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
        table_button = QPushButton("打开表格")
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
        self.command_table = InstructionTableWidget(0, 7)
        self.command_table.setObjectName("commandTable")
        self.command_table.setMouseTracking(True)
        self.command_table.setHorizontalHeaderLabels(
            ["序号", "编号", "指令", "参数", "重复", "异常处理", "备注"]
        )
        self.command_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.command_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.command_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.command_table.setAlternatingRowColors(True)
        self.command_table.setShowGrid(False)
        self.command_table.setWordWrap(False)
        self.command_table.verticalHeader().setVisible(False)
        self.command_table.verticalHeader().setDefaultSectionSize(38)
        header = self.command_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.command_table.cellDoubleClicked.connect(self._edit_table_command)
        self.command_table.instructionDropped.connect(self._add_table_command)
        self.command_table.deleteRequested.connect(self.delete_table_commands)
        self.command_table.copyRequested.connect(self.copy_table_commands)
        self.command_table.pasteRequested.connect(self.paste_table_commands)
        self.command_table.rowsMoved.connect(self.move_table_commands)
        self.command_table.setToolTip('拖动序号上下排序；其他单元格拖动框选，Ctrl+C / Ctrl+V 复制粘贴，Delete 删除选中行')

        # Replace the legacy left/right log layout with a clear vertical stack:
        # commands on top and the continuously updating run log below.
        self.window.horizontalLayout.removeWidget(self.window.textEdit)
        self.window.horizontalLayout.removeItem(self.window.verticalLayout)
        for button in (self.window.toolButton_8, self.window.toolButton_7):
            self.window.verticalLayout.removeWidget(button)

        table_panel = QFrame()
        table_panel.setObjectName("workspacePanel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_title = QLabel("指令表格")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        self.table_state = QLabel()
        self.table_state.setObjectName("mutedText")
        table_layout.addWidget(self.table_state)
        table_layout.addWidget(self.command_table, 1)

        log_panel = QFrame()
        log_panel.setObjectName("workspacePanel")
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(12, 10, 12, 12)
        log_header = QHBoxLayout()
        log_title = QLabel("运行日志")
        log_title.setObjectName("sectionTitle")
        log_header.addWidget(log_title)
        log_header.addStretch(1)
        self.window.toolButton_8.setText("导出日志")
        self.window.toolButton_7.setText("清空日志")
        log_header.addWidget(self.window.toolButton_8)
        log_header.addWidget(self.window.toolButton_7)
        log_layout.addLayout(log_header)
        log_layout.addWidget(self.window.textEdit, 1)

        self.table_splitter = QSplitter(Qt.Orientation.Vertical)
        self.table_splitter.setObjectName("tableLogSplitter")
        self.table_splitter.setChildrenCollapsible(False)
        self.table_splitter.addWidget(table_panel)
        self.table_splitter.addWidget(log_panel)
        self.table_splitter.setStretchFactor(0, 3)
        self.table_splitter.setStretchFactor(1, 2)
        self.table_splitter.setSizes([520, 260])
        self.window.horizontalLayout.setContentsMargins(8, 8, 8, 8)
        self.window.horizontalLayout.addWidget(self.table_splitter, 1)

    def _build_editor_view(self) -> QWidget:
        page = QWidget()
        page.setObjectName("editorView")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        tip = QLabel(
            "先拖入指令，再从节点左右两侧拉线；条件节点上方为“是”、下方为“否”"
        )
        tip.setObjectName("editorTip")
        layout.addWidget(tip)
        self.window.nodeEditorLayout.removeWidget(self.window.workspace.editor)
        self.window.workspace.editor.setParent(page)
        layout.addWidget(self.window.workspace.editor, 1)
        return page

    def _build_code_view(self) -> QWidget:
        page = QWidget()
        page.setObjectName("multifunctionView")
        layout = QVBoxLayout(page)
        header = QHBoxLayout()
        title = QLabel("多功能代码")
        title.setObjectName("pageTitle")
        self.code_status = QLabel("修改会自动保存在当前任务中")
        self.code_status.setObjectName("mutedText")
        regenerate = QPushButton("按当前流程重新生成")
        regenerate.clicked.connect(self.regenerate_code)
        header.addWidget(title)
        header.addWidget(self.code_status)
        header.addStretch(1)
        header.addWidget(regenerate)
        layout.addLayout(header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.command_list = QListWidget()
        self.command_list.setMinimumWidth(190)
        self.command_list.setMaximumWidth(290)
        for spec in iter_instruction_specs():
            item = QListWidgetItem(f"{spec.category}  /  {spec.display_name}")
            item.setData(Qt.ItemDataRole.UserRole, spec.type_id)
            self.command_list.addItem(item)
        self.command_list.itemDoubleClicked.connect(self._insert_command_hint)
        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("在这里维护当前任务的多功能代码……")
        self.code_editor.textChanged.connect(self._schedule_code_save)
        splitter.addWidget(self.command_list)
        splitter.addWidget(self.code_editor)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        return page

    def _build_navigation(self) -> None:
        self.window.toolBar.setIconSize(QSize(16, 16))
        toolbar_font = self.window.toolBar.font()
        base_size = toolbar_font.pointSize()
        toolbar_font.setPointSize(max(8, base_size - 2 if base_size > 0 else 9))
        self.window.toolBar.setFont(toolbar_font)
        self.primary_action = QAction("打开流程图", self.window)
        self.primary_action.triggered.connect(self.toggle_primary)
        self.code_action = QAction("多功能", self.window)
        self.code_action.triggered.connect(self.show_code)
        self.palette_side_action = QAction("指令栏移到右侧", self.window)
        self.palette_side_action.triggered.connect(self.toggle_palette_side)
        self.palette_collapse_action = QAction("收起指令栏", self.window)
        self.palette_collapse_action.triggered.connect(self.toggle_palette)
        self.theme_action = QAction("切换浅色", self.window)
        self.theme_action.triggered.connect(self.toggle_theme)
        self.donation_action = QAction("捐赠", self.window)
        self.donation_action.triggered.connect(self.show_donation)
        self.window.toolBar.addSeparator()
        self.window.toolBar.addAction(self.primary_action)
        self.window.toolBar.addAction(self.code_action)
        self.window.toolBar.addSeparator()
        self.window.toolBar.addAction(self.palette_side_action)
        self.window.toolBar.addAction(self.palette_collapse_action)
        self.window.toolBar.addAction(self.donation_action)
        from window_chrome import install_title_bar
        self.title_bar = install_title_bar(self.window, self.theme_action)
        self.title_bar.apply_theme(self.theme_mode, self.THEMES[self.theme_mode])
        from compact_workspace import CompactWorkspace
        self.compact = CompactWorkspace(self)
        menu = QMenu("视图", self.window)
        for label, shortcut, callback in (
            ("主界面", "Ctrl+1", self.show_main),
            ("表格", "Ctrl+2", self.show_table),
            ("流程图", "Ctrl+3", self.show_flow),
            ("多功能", "Ctrl+4", self.show_code),
            ("导航", "Ctrl+5", self.show_navigation),
            ("录制", "Ctrl+6", self.show_recording),
            ("设置变量", "Ctrl+Shift+V", self.show_variables),
        ):
            action = QAction(label, self.window)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            menu.addAction(action)
        self.window.menubar.insertMenu(self.window.menu_4.menuAction(), menu)
        menu.addSeparator()
        self.window.menu_3.removeAction(self.window.actiong)
        self.window.actiong.setText('显示工具栏')
        menu.addAction(self.window.actiong)
        self.window.menubar.removeAction(self.window.menu_3.menuAction())

    def toggle_primary(self) -> None:
        self.show_main() if self.tabs.currentIndex() == FLOW_VIEW else self.show_flow()

    def show_main(self): self.tabs.setCurrentIndex(MAIN_VIEW)
    def show_table(self): self.tabs.setCurrentIndex(TABLE_VIEW)
    def show_flow(self): self.tabs.setCurrentIndex(FLOW_VIEW)
    def show_code(self):
        self._load_code()
        self.tabs.setCurrentIndex(CODE_VIEW)
    def show_navigation(self): self.tabs.setCurrentIndex(NAVIGATION_VIEW)
    def show_recording(self): self.tabs.setCurrentIndex(RECORDING_VIEW)

    # Backward-compatible aliases for integrations that used the earlier names.
    def show_beginner(self): self.show_navigation()
    def show_editor(self): self.show_flow()

    def toggle_palette_side(self) -> None:
        self.palette_side = "right" if self.palette_side == "left" else "left"
        self._place_palette()

    def toggle_palette(self) -> None:
        self.palette_collapsed = not self.palette_collapsed
        self._place_palette()

    def toggle_theme(self) -> None:
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.window.db.set_setting_value(THEME_SETTING, self.theme_mode)
        self._apply_theme()
        self._update_view_actions()

    def show_donation(self) -> None:
        """Show the bundled donation QR code without opening a web page."""
        image_path = os.path.join(RESOURCE_FOLDER, "Window", "res", "donation_qr.png")
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
        if getattr(getattr(self, 'compact', None), 'active', False):
            return
        grid = self.window.gridLayout_4
        palette = self.window.instructionPaletteHost
        center = self.tabs
        controls = self.window.groupBox_3
        for widget in (palette, center, controls):
            grid.removeWidget(widget)
        if self.palette_side == "left":
            grid.addWidget(palette, 0, 0, 1, 1)
            grid.addWidget(center, 0, 1, 1, 1)
            grid.addWidget(controls, 0, 2, 1, 1)
            stretches = (0, 4, 1)
        else:
            grid.addWidget(center, 0, 0, 1, 1)
            grid.addWidget(palette, 0, 1, 1, 1)
            grid.addWidget(controls, 0, 2, 1, 1)
            stretches = (4, 0, 1)
        for column, stretch in enumerate(stretches):
            grid.setColumnStretch(column, stretch)
        palette.setVisible(
            self.tabs.currentIndex() in (TABLE_VIEW, FLOW_VIEW)
            and not self.palette_collapsed
        )
        self._update_view_actions()

    def _update_view_actions(self) -> None:
        self.primary_action.setText(
            "返回主界面" if self.tabs.currentIndex() == FLOW_VIEW else "打开流程图"
        )
        self.palette_side_action.setText(
            "指令栏移到左侧" if self.palette_side == "right" else "指令栏移到右侧"
        )
        self.palette_collapse_action.setText(
            "展开指令栏" if self.palette_collapsed else "收起指令栏"
        )
        self.theme_action.setText("切换深色" if self.theme_mode == "light" else "切换浅色")

    def _view_changed(self, index: int) -> None:
        self._place_palette()
        if index in (MAIN_VIEW, NAVIGATION_VIEW): self.refresh_summary()
        elif index == TABLE_VIEW: self.refresh_table()
        elif index == CODE_VIEW: self._load_code()

    def refresh_all(self) -> None:
        self._sync_code_if_needed()
        self.refresh_summary()
        self.refresh_table()

    def refresh_summary(self) -> None:
        try:
            snapshot = self.window.workspace.repository.snapshot()
            code_lines = len(self.code_editor.toPlainText().splitlines())
            summary = (
                f"流程节点  {len(snapshot.nodes)}\n可执行指令  {len(snapshot.commands)}\n"
                f"多功能代码  {code_lines} 行"
            )
            self.stats.setText(summary)
            self.main_stats.setText(summary)
        except Exception as error:
            summary = f"任务状态暂不可用：{error}"
            self.stats.setText(summary)
            self.main_stats.setText(summary)

    def refresh_table(self) -> None:
        snapshot, validation_error = self._current_graph_state()
        commands = list(snapshot.commands)
        if validation_error is None:
            self.table_state.setText(f"流程、表格与多功能已同步，共 {len(commands)} 条指令")
        else:
            self.table_state.setText(
                f"流程草稿，共 {len(commands)} 条指令；{validation_error}"
            )
        nodes_by_command = {
            node.command_id: node
            for node in snapshot.nodes
            if node.command_id is not None
        }
        self.command_table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            parameters_text = json.dumps(
                command.parameters, ensure_ascii=False, sort_keys=True, separators=(", ", ": ")
            )
            values = (
                str(row + 1),
                f"#{command.id}",
                display_name,
                parameters_text,
                str(command.repeat_count),
                command.error_policy,
                command.note,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, command.id)
                item.setToolTip(value)
                self.command_table.setItem(row, column, item)

    def _add_table_command(self, type_id: str) -> None:
        self.window.workspace.add_command(type_id)
        self.refresh_table()
        self.window.statusBar.showMessage(f"已从指令栏添加：{type_id}", 2500)

    def _graph_finalized(self, complete: bool) -> None:
        self._sync_code_if_needed(force=True)
        self.refresh_summary()
        self.refresh_table()
        self.code_status.setText("流程、表格与多功能已同步" if complete else "已同步流程草稿，可按连线优先、其余按添加顺序运行")

    def _edit_table_command(self, row: int, _column: int) -> None:
        if _column == 0 or not self._table_mutation_allowed():
            return
        item = self.command_table.item(row, 0)
        if item is not None:
            self.window.workspace.edit_command(item.data(Qt.ItemDataRole.UserRole))
            self.refresh_all()

    def _table_mutation_allowed(self):
        thread = getattr(self.window, 'command_thread', None)
        if (thread is not None and thread.isRunning()) or self.recording_page.busy:
            self.window.statusBar.showMessage('请先停止运行或录制，再修改表格。', 3000)
            return False
        return True

    def delete_table_commands(self):
        if not self._table_mutation_allowed():
            return 0
        ids = self.command_table.selected_command_ids()
        if not ids:
            return 0
        return self.window.workspace.remove_commands(ids)

    def copy_table_commands(self):
        from dataclasses import asdict
        ids = set(self.command_table.selected_command_ids())
        commands = [c for c in self.window.workspace.repository.list_commands() if c.id in ids]
        if not commands:
            return
        mime = QMimeData()
        payload = json.dumps([asdict(c.to_draft()) for c in commands], ensure_ascii=False)
        mime.setData('application/x-anclicker-commands', payload.encode('utf-8'))
        mime.setText('\n'.join(f'{c.type_id}\t{json.dumps(c.parameters, ensure_ascii=False)}\t{c.repeat_count}\t{c.note}' for c in commands))
        QApplication.clipboard().setMimeData(mime)
        self.window.statusBar.showMessage(f'已复制 {len(commands)} 条指令', 2500)

    def paste_table_commands(self):
        if not self._table_mutation_allowed():
            return
        mime = QApplication.clipboard().mimeData()
        if mime is None or not mime.hasFormat('application/x-anclicker-commands'):
            self.window.statusBar.showMessage('请先在指令表格中复制指令。', 2500)
            return
        try:
            from instructions.models import InstructionDraft
            raw = bytes(mime.data('application/x-anclicker-commands'))
            if len(raw) > 10_000_000:
                raise ValueError('复制内容过大，请分批粘贴')
            data = json.loads(raw)
            if not isinstance(data, list) or not 0 < len(data) <= 10000 or not all(isinstance(x, dict) for x in data):
                raise ValueError('剪贴板不是有效的指令列表')
            drafts = [InstructionDraft.from_mapping(item) for item in data]
            ids = self.window.workspace.repository.append_recording(drafts, connect=False)
            self.window.workspace.reload_graph(ids[0])
            self.window.workspace.graphFinalized.emit(False)
            self._select_table_ids(ids)
            self.window.statusBar.showMessage(f'已粘贴 {len(ids)} 条指令，表格与流程图已同步', 3000)
        except Exception as error:
            QMessageBox.warning(self.window, '粘贴失败', str(error))

    def _select_table_ids(self, ids):
        from PySide6.QtWidgets import QTableWidgetSelectionRange
        self.command_table.clearSelection()
        for row in range(self.command_table.rowCount()):
            if self.command_table.item(row, 0).data(Qt.ItemDataRole.UserRole) in ids:
                self.command_table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, self.command_table.columnCount()-1), True)

    def move_table_commands(self, ids, destination):
        if not self._table_mutation_allowed():
            return
        repo = self.window.workspace.repository
        current = [c.id for c in repo.list_commands()]
        moved = [item for item in current if item in ids]
        remaining = [item for item in current if item not in ids]
        destination = max(0, min(destination, len(current)))
        index = destination - sum(item in ids for item in current[:destination])
        ordered = remaining[:index] + moved + remaining[index:]
        if ordered == current:
            return
        try:
            rewired = repo.reorder_table_commands(ordered)
            self.window.workspace.reload_graph(moved[0])
            self.window.workspace.graphFinalized.emit(False)
            self._select_table_ids(moved)
            self.window.statusBar.showMessage('已同步表格排序和流程图' + ('；顺序连线已调整' if rewired else '；现有分支连线保持不变'), 4000)
        except Exception as error:
            QMessageBox.warning(self.window, '移动失败', str(error))

    def _save_task_name(self) -> None:
        name = self.task_name.text().strip() or "默认任务"
        self.task_name.setText(name)
        self.window.db.set_setting_value(TASK_NAME_SETTING, name)
        self.window.statusBar.showMessage(f"任务名称已保存：{name}", 3000)

    def _save_window_binding(self) -> None:
        self.window.db.set_setting_value(WINDOW_TITLE_SETTING, self.window_title.text().strip())
        self.window.statusBar.showMessage("窗口绑定已保存。", 3000)

    def _load_code(self) -> None:
        if self._code_dirty: return
        snapshot, validation_error = self._current_graph_state()
        signature = self._graph_signature(snapshot)
        saved_signature = str(
            self.window.db.get_setting_value(CODE_GRAPH_SIGNATURE_SETTING) or ""
        )
        text = str(self.window.db.get_setting_value(CODE_SETTING) or "")
        if not text or saved_signature != signature:
            text = self._generated_code(snapshot, validation_error)
            self.window.db.set_setting_value(CODE_SETTING, text)
            self.window.db.set_setting_value(CODE_GRAPH_SIGNATURE_SETTING, signature)
        self._loading_code = True
        with QSignalBlocker(self.code_editor): self.code_editor.setPlainText(text)
        self._loading_code = False
        self.code_status.setText(
            "修改会自动保存在当前任务中"
            if validation_error is None
            else "已同步流程草稿，可按连线优先、其余按添加顺序运行"
        )

    def regenerate_code(self) -> None:
        self._sync_code_if_needed(force=True)
        self.refresh_summary()
        self.window.statusBar.showMessage("已根据当前流程重新生成多功能代码。", 3000)

    def _current_graph_state(self):
        try:
            snapshot = self.window.workspace.repository.validate_graph()
            return snapshot, None
        except Exception as error:
            try:
                snapshot = self.window.workspace.repository.execution_snapshot()
                return snapshot, "可执行：连线优先，其余按添加顺序运行"
            except Exception as execution_error:
                return self.window.workspace.repository.snapshot(), f"无法执行：{execution_error}"

    @staticmethod
    def _graph_signature(snapshot) -> str:
        payload = {
            "commands": [
                {
                    "id": command.id,
                    "type": command.type_id,
                    "parameters": command.parameters,
                    "repeat": command.repeat_count,
                    "error": command.error_policy,
                    "note": command.note,
                    "order": command.order,
                }
                for command in snapshot.commands
            ],
            "edges": [
                {"source": edge.source, "target": edge.target, "kind": edge.kind}
                for edge in snapshot.edges
            ],
        }
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _sync_code_if_needed(self, *, force: bool = False) -> bool:
        snapshot, validation_error = self._current_graph_state()
        signature = self._graph_signature(snapshot)
        saved_signature = str(
            self.window.db.get_setting_value(CODE_GRAPH_SIGNATURE_SETTING) or ""
        )
        saved_code = str(self.window.db.get_setting_value(CODE_SETTING) or "")
        if not force and saved_signature == signature and saved_code:
            return False
        text = self._generated_code(snapshot, validation_error)
        self._loading_code = True
        with QSignalBlocker(self.code_editor):
            self.code_editor.setPlainText(text)
        self._loading_code = False
        self._code_dirty = False
        self.window.db.set_setting_value(CODE_SETTING, text)
        self.window.db.set_setting_value(CODE_GRAPH_SIGNATURE_SETTING, signature)
        self.code_status.setText(
            "流程、表格与多功能已同步"
            if validation_error is None
            else "已同步流程草稿，可按连线优先、其余按添加顺序运行"
        )
        return True

    def _generated_code(self, snapshot=None, validation_error=None) -> str:
        if snapshot is None:
            snapshot, validation_error = self._current_graph_state()
        commands = list(snapshot.commands)
        lines = [
            "# Clicker 多功能代码（由流程图同步）",
            (
                "# 状态：流程完整，可执行"
                if validation_error is None
                else f"# 状态：流程草稿，{validation_error}"
            ),
            f"# 流程签名：{self._graph_signature(snapshot)[:16]}",
            "# 在流程不变时可继续编辑；流程改变后会按最新内容重新同步。",
            "",
        ]
        nodes_by_command = {
            node.command_id: node
            for node in snapshot.nodes
            if node.command_id is not None
        }
        for sequence, command in enumerate(commands, start=1):
            params = json.dumps(command.parameters, ensure_ascii=False, sort_keys=True)
            note = f"  # {command.note}" if command.note else ""
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            lines.append(f"# [{sequence}] #{command.id} {display_name}")
            lines.append(f"{command.type_id}({params}, 重复次数={command.repeat_count}, 异常处理={command.error_policy!r}){note}")
        if snapshot.edges:
            nodes = {node.node_id: node for node in snapshot.nodes}
            kind_names = {0: "下一步", 1: "是", 2: "否", 3: "循环体", 4: "完成"}
            lines.extend(["", "# 流程连线（由流程图自动同步）"])
            for edge in snapshot.edges:
                source = nodes[edge.source]
                target = nodes[edge.target]
                source_name = "开始" if source.command_id is None else f"#{source.command_id} {source.display_name}"
                target_name = "结束" if target.command_id is None else f"#{target.command_id} {target.display_name}"
                lines.append(
                    f"# {source_name} --{kind_names.get(edge.kind, '下一步')}--> {target_name}"
                )
        if not commands: lines.append("# 当前流程还没有指令，请先到流程图或表格视图添加。")
        return "\n".join(lines) + "\n"

    def _insert_command_hint(self, item: QListWidgetItem) -> None:
        type_id = item.data(Qt.ItemDataRole.UserRole)
        self.code_editor.insertPlainText(f'{type_id}({{}}, 重复次数=1, 异常处理="提示异常并暂停")\n')
        self.code_editor.setFocus()

    def _schedule_code_save(self) -> None:
        if self._loading_code: return
        self._code_dirty = True
        self.code_status.setText("正在保存……")
        QTimer.singleShot(350, self._save_code)

    def _save_code(self) -> None:
        if not self._code_dirty: return
        self.window.db.set_setting_value(CODE_SETTING, self.code_editor.toPlainText())
        self._code_dirty = False
        self.code_status.setText("已自动保存")

    def _apply_theme(self) -> None:
        c = self.THEMES[self.theme_mode]
        down_arrow = os.path.join(RESOURCE_FOLDER, 'flat', 'chevron-down.svg').replace('\\', '/')
        up_arrow = os.path.join(RESOURCE_FOLDER, 'flat', 'chevron-up.svg').replace('\\', '/')
        try:
            scheme = (
                Qt.ColorScheme.Dark
                if self.theme_mode == "dark"
                else Qt.ColorScheme.Light
            )
            QGuiApplication.styleHints().setColorScheme(scheme)
        except AttributeError:
            pass
        if hasattr(self, "command_table"):
            table_palette = self.command_table.palette()
            for role, color in (
                (QPalette.ColorRole.Window, c["surface"]),
                (QPalette.ColorRole.Base, c["surface"]),
                (QPalette.ColorRole.AlternateBase, c["surface2"]),
                (QPalette.ColorRole.Text, c["text"]),
                (QPalette.ColorRole.WindowText, c["text"]),
                (QPalette.ColorRole.Button, c["surface2"]),
                (QPalette.ColorRole.Highlight, c["accent2"]),
                (QPalette.ColorRole.HighlightedText, c["accent_text"]),
            ):
                table_palette.setColor(role, QColor(color))
            self.command_table.setPalette(table_palette)
            self.command_table.viewport().setPalette(table_palette)
            self.command_table.viewport().setAutoFillBackground(True)
        self.window.workspace.editor.set_theme(self.theme_mode)
        controls_palette = self.window.groupBox_3.palette()
        controls_palette.setColor(QPalette.ColorRole.WindowText, QColor(c['text']))
        self.window.groupBox_3.setPalette(controls_palette)
        if hasattr(self, "title_bar"):
            self.title_bar.apply_theme(self.theme_mode, c)
        self.window.setStyleSheet(f"""
            QMainWindow, QWidget#centralwidget {{ background: {c['bg']}; color: {c['text']}; }}
            QWidget {{ font-family: 'Microsoft YaHei UI'; font-size: 13px; }}
            QLabel {{ color: {c['text']}; }}
            QWidget#instructionEditorBody {{ background: {c['bg']}; color: {c['text']}; }}
            QWidget#tab, QWidget#editorView, QWidget#multifunctionView,
            QWidget#beginnerView, QStackedWidget {{ background: {c['bg']}; color: {c['text']}; }}
            QMenuBar, QMenu, QToolBar {{ background: {c['nav']}; color: {c['text']}; border-color: {c['line']}; spacing: 4px; }}
            QMenuBar::item:selected, QMenu::item:selected {{ background: {c['surface3']}; color: {c['accent']}; }}
            QToolBar {{ border-bottom: 1px solid {c['line']}; padding: 2px 3px; spacing: 2px; font-size: 11px; }}
            QToolBar QToolButton {{ padding: 3px 6px; border-radius: 6px; font-size: 11px; }}
            QToolBar QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; }}
            QTabWidget::pane {{ border: 1px solid {c['line']}; border-radius: 12px; background: {c['bg']}; top: -1px; }}
            QTabBar::tab {{ background: {c['surface']}; color: {c['dim']}; padding: 9px 18px; border: 1px solid {c['line']}; border-radius: 8px; margin: 2px; }}
            QTabBar::tab:selected {{ background: {c['accent']}; color: {c['accent_text']}; font-weight: 700; }}
            QTabBar::tab:hover:!selected {{ background: {c['surface3']}; color: {c['accent']}; }}
            QWidget#instructionPaletteHost, QGroupBox#groupBox_3 {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 12px; }}
            QGroupBox#groupBox_3::title {{ color: {c['text']}; }}
            QWidget#instructionPaletteHost QTreeWidget, QWidget#instructionPaletteHost QLineEdit,
            QGroupBox#groupBox_3 QTextEdit {{ background: {c['surface2']}; color: {c['text']}; }}
            QTreeWidget#instructionTree::item {{ color: {c['text']}; padding: 5px; border: 1px solid transparent; border-radius: 5px; }}
            QTreeWidget#instructionTree::item:hover:!selected {{ background: {c['surface3']}; border-color: {c['accent']}; }}
            QTreeWidget#instructionTree::item:selected {{ background: {c['accent2']}; color: white; border-color: {c['accent']}; }}
            QFrame#viewNavigation {{ background: {c['nav']}; border: 1px solid {c['line']}; border-radius: 12px; min-width: 175px; max-width: 220px; }}
            QLabel#navTitle, QLabel#pageTitle {{ color: {c['text']}; font-size: 17px; font-weight: 700; padding: 8px; }}
            QListWidget#beginnerNavigation {{ background: transparent; border: none; outline: none; }}
            QListWidget#beginnerNavigation::item {{ color: {c['text']}; padding: 11px 14px; margin: 1px 0; }}
            QListWidget#beginnerNavigation::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; border-radius: 8px; }}
            QListWidget#beginnerNavigation::item:hover:!selected {{ background: {c['surface3']}; color: {c['accent']}; }}
            QFrame#contentCard {{ background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 12px; padding: 12px; }}
            QFrame#workspacePanel {{ background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 12px; }}
            QLabel#cardTitle {{ color: {c['text']}; font-size: 18px; font-weight: 700; padding: 4px; }}
            QLabel#sectionTitle {{ color: {c['text']}; font-size: 15px; font-weight: 700; padding: 2px 4px 7px 4px; }}
            QLabel#mutedText {{ color: {c['dim']}; padding: 3px; }}
            QLabel#taskStats {{ color: {c['text']}; background: {c['surface2']}; border-radius: 10px; padding: 14px; font-size: 15px; }}
            QLabel#editorTip {{ color: {c['accent']}; background: {c['surface2']}; border: 1px solid {c['line']}; border-radius: 8px; padding: 8px 12px; }}
            QPushButton, QToolButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 8px; padding: 7px 12px; }}
            QPushButton:hover, QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; border-color: {c['accent']}; }}
            QPushButton:pressed {{ background: {c['accent2']}; color: white; }}
            QPushButton:disabled, QToolButton:disabled {{ background: {c['surface']}; color: {c['dim']}; border-color: {c['line']}; }}
            QPushButton#accentButton {{ background: {c['accent']}; color: {c['accent_text']}; font-weight: 700; border-color: {c['accent']}; }}
            QSlider#imageConfidenceSlider::groove:horizontal {{ height: 5px; background: {c['surface3']}; border-radius: 2px; }}
            QSlider#imageConfidenceSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
            QSlider#imageConfidenceSlider::handle:horizontal {{ width: 14px; margin: -5px 0; border-radius: 7px; background: {c['accent']}; }}
            QPushButton#dangerButton {{ background: {c['danger']}; color: white; font-weight: 700; border-color: {c['danger']}; }}
            QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 8px; padding: 6px; selection-background-color: {c['accent2']}; }}
            QSpinBox, QDoubleSpinBox {{ min-height: 20px; padding: 6px 20px 6px 6px; }}
            QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {{ border: none; border-radius: 0; padding: 0; min-height: 0; background: transparent; }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 18px; height: 16px; border: none; }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 18px; height: 16px; border: none; }}
            QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {c['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox {{ padding-right: 28px; }}
            QComboBox::down-arrow, QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{down_arrow}"); width: 12px; height: 12px; }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{up_arrow}"); width: 12px; height: 12px; }}
            QCheckBox, QRadioButton {{ color: {c['text']}; spacing: 7px; padding: 3px; }}
            QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
            QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{ background: {c['surface2']}; border: 1px solid {c['line']}; border-radius: 5px; }}
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ background: {c['accent']}; border: 2px solid {c['surface2']}; border-radius: 5px; }}
            QAbstractScrollArea, QAbstractScrollArea QWidget#qt_scrollarea_viewport,
            QTableWidget, QListWidget {{ background: {c['surface']}; color: {c['text']}; alternate-background-color: {c['surface2']}; border: 1px solid {c['line']}; border-radius: 10px; gridline-color: {c['line']}; }}
            QTableWidget#commandTable {{ background-color: {c['surface']}; alternate-background-color: {c['surface2']}; }}
            QTableWidget#commandTable::item {{ background-color: transparent; color: {c['text']}; border: none; padding: 5px; }}
            QTableWidget#commandTable::item:alternate {{ background-color: {c['surface2']}; }}
            QTableWidget#commandTable::item:hover:!selected {{ background-color: {c['surface3']}; border-bottom: 1px solid {c['accent']}; }}
            QTextEdit#textEdit {{ background: {c['nav']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 10px; padding: 8px; }}
            QTableWidget::item:selected, QListWidget::item:selected {{ background: {c['accent2']}; color: white; }}
            QHeaderView {{ background: {c['surface2']}; color: {c['accent']}; }}
            QHeaderView::section {{ background: {c['surface2']}; color: {c['accent']}; border: none; border-right: 1px solid {c['line']}; padding: 7px; font-weight: 700; }}
            QTableCornerButton::section, QAbstractScrollArea::corner {{ background: {c['surface2']}; border: none; border-right: 1px solid {c['line']}; border-bottom: 1px solid {c['line']}; }}
            QToolTip {{ background: {c['surface3']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 6px; padding: 5px; }}
            QDialog {{ background: {c['bg']}; color: {c['text']}; }}
            QDialogButtonBox QPushButton {{ min-width: 76px; }}
            QScrollBar:vertical {{ background: {c['bg']}; width: 11px; }}
            QScrollBar::handle:vertical {{ background: {c['surface3']}; min-height: 24px; border-radius: 5px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['accent2']}; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: {c['bg']}; }}
            QScrollBar:horizontal {{ background: {c['bg']}; height: 11px; }}
            QScrollBar::handle:horizontal {{ background: {c['surface3']}; min-width: 24px; border-radius: 5px; }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: {c['bg']}; }}
            QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
            QSplitter::handle {{ background: {c['bg']}; }}
            QSplitter#tableLogSplitter::handle {{ background: {c['bg']}; height: 8px; }}
            QSplitter#tableLogSplitter::handle:hover {{ background: {c['accent']}; border-radius: 4px; }}
            QStatusBar {{ background: {c['nav']}; color: {c['dim']}; border-top: 1px solid {c['line']}; }}
            QGroupBox {{ color: {c['accent']}; background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 10px; margin-top: 10px; padding-top: 10px; font-weight: 700; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        """)
