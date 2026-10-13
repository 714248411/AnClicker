"""Linked Clicker workspaces and the light/dark desktop themes."""

from __future__ import annotations

import hashlib
import json
import os

from qt_compat.QtCore import QObject, QEvent, QSize, QSignalBlocker, Signal, Qt, QTimer, QMimeData, QItemSelectionModel
from qt_compat.QtGui import QAction, QColor, QGuiApplication, QKeySequence, QPalette, QPixmap, QDrag, QPainter, QPen
from qt_compat.QtWidgets import (
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

from instructions.registry import iter_instruction_specs
from node_editor.palette import INSTRUCTION_MIME_TYPE
from functions import RESOURCE_FOLDER
from recording_view import RecordingView
from web_recording_view import WebRecordingView


MAIN_VIEW = 0
TABLE_VIEW = 1
FLOW_VIEW = 2
CODE_VIEW = 3
RECORDING_VIEW = 4
WEB_RECORDING_VIEW = 5
CODE_SETTING = "多功能代码"
CODE_GRAPH_SIGNATURE_SETTING = "多功能流程签名"
TASK_NAME_SETTING = "任务名称"
WINDOW_TITLE_SETTING = "绑定窗口标题"
THEME_SETTING = "界面主题"


class CommentRowDelegate(QStyledItemDelegate):
    """Paint comment cells explicitly: stylesheet item backgrounds override roles."""

    def paint(self, painter, option, index):
        background = index.data(Qt.ItemDataRole.BackgroundRole)
        if background is None or option.state & QStyle.State_Selected:
            return super().paint(painter, option, index)
        painter.save()
        painter.setClipRect(option.rect)
        painter.fillRect(option.rect, background)
        painter.setFont(option.font)
        foreground = index.data(Qt.ItemDataRole.ForegroundRole)
        painter.setPen(foreground if foreground is not None else option.palette.color(QPalette.Text))
        rect = option.rect.adjusted(5, 0, -5, 0)
        text = option.fontMetrics.elidedText(str(index.data() or ''), Qt.ElideRight, max(0, rect.width()))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()


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
        self.setItemDelegate(CommentRowDelegate(self))
        self._row_press = None
        self.runtime_row = -1
        self.comment_ranges = {}
        self.collapsed_comments = set()
        self._drop_line = QFrame(self.viewport())
        self._drop_line.setStyleSheet('background: #5b6fdc;')
        self._drop_line.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._drop_line.hide()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not 0 <= self.runtime_row < self.rowCount():
            return
        rect = self.visualRect(self.model().index(self.runtime_row, 0))
        rect.setLeft(0)
        rect.setRight(self.viewport().width() - 1)
        if not rect.intersects(self.viewport().rect()):
            return
        painter = QPainter(self.viewport())
        accent = self.palette().color(QPalette.ColorRole.Highlight)
        tint = QColor(accent)
        tint.setAlpha(32)
        painter.fillRect(rect, tint)
        painter.setPen(QPen(accent, 2))
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.fillRect(rect.left(), rect.top(), 4, rect.height(), accent)
        painter.end()

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

    def update_comment_ranges(self, snapshot):
        from flow_comments import connected_fold_ranges
        self.comment_ranges = connected_fold_ranges(snapshot)
        self.collapsed_comments.intersection_update(self.comment_ranges)
        self.apply_comment_folds()

    def set_comment_collapsed(self, command_id, collapsed):
        if command_id not in self.comment_ranges:
            return
        if collapsed:
            self.collapsed_comments.add(command_id)
        else:
            self.collapsed_comments.discard(command_id)
        self.apply_comment_folds()

    def apply_comment_folds(self):
        hidden = set()
        for command_id in self.collapsed_comments:
            hidden.update(self.comment_ranges.get(command_id, ()))
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            self.setRowHidden(row, item is not None and item.data(Qt.ItemDataRole.UserRole) in hidden)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and not self.selectionModel().isSelected(index):
            self.clearSelection()
            self.setCurrentCell(index.row(), index.column())
        menu = QMenu(self)
        from context_menu_style import style_context_menu
        style_context_menu(menu, self)
        item = self.item(index.row(), 0) if index.isValid() else None
        command_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if command_id in self.comment_ranges:
            expand = menu.addAction('展开下部指令', lambda: self.set_comment_collapsed(command_id, False))
            collapse = menu.addAction('收缩下部指令', lambda: self.set_comment_collapsed(command_id, True))
            expand.setEnabled(command_id in self.collapsed_comments)
            collapse.setEnabled(command_id not in self.collapsed_comments and bool(self.comment_ranges[command_id]))
            menu.addSeparator()
        count = len(self.selected_command_ids())
        copy = menu.addAction(f'复制选中指令（{count} 行）', self.copyRequested.emit)
        copy.setEnabled(count > 0)
        menu.addAction('粘贴指令到表格末尾', self.pasteRequested.emit)
        menu.addSeparator()
        delete = menu.addAction(f'删除选中指令（{count} 行）', self.deleteRequested.emit)
        delete.setEnabled(count > 0)
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()

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


class _ToolbarDockOnDoubleClick(QObject):
    """Return a floating toolbar to its last dock area from empty-space double clicks."""

    def __init__(self, window, toolbar):
        super().__init__(toolbar)
        self.window = window
        self.toolbar = toolbar
        area = window.toolBarArea(toolbar)
        self.area = area if area != Qt.ToolBarArea.NoToolBarArea else Qt.ToolBarArea.TopToolBarArea
        toolbar.installEventFilter(self)
        toolbar.topLevelChanged.connect(self._remember_area)

    def _remember_area(self, floating=False):
        if not floating and not self.toolbar.isFloating():
            area = self.window.toolBarArea(self.toolbar)
            if area != Qt.ToolBarArea.NoToolBarArea:
                self.area = area

    def eventFilter(self, watched, event):
        if watched is self.toolbar:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Show):
                self._remember_area()
            elif (event.type() == QEvent.Type.MouseButtonDblClick
                  and event.button() == Qt.MouseButton.LeftButton
                  and self.toolbar.isFloating()):
                point = event.position().toPoint()
                action = self.toolbar.actionAt(point)
                # Buttons, embedded controls and the overflow button retain their own behavior.
                if action is not None and not action.isSeparator():
                    return False
                if self.toolbar.childAt(point) is not None:
                    return False
                event.accept()
                QTimer.singleShot(0, self._dock)
                return True
        return super().eventFilter(watched, event)

    def _dock(self):
        if not self.toolbar.isFloating():
            return
        area = self.area
        if not (self.toolbar.allowedAreas() & area):
            area = next((candidate for candidate in (
                Qt.ToolBarArea.TopToolBarArea, Qt.ToolBarArea.BottomToolBarArea,
                Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea)
                if self.toolbar.allowedAreas() & candidate), None)
        if area is None:
            return
        self.window.removeToolBar(self.toolbar)
        self.toolbar.setParent(self.window, Qt.WindowType.Widget)
        self.window.addToolBar(area, self.toolbar)
        self.toolbar.show()


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
        from dock_workspace import DockWorkspace
        self.docking = DockWorkspace(self)
        self.docking.sync_visibility()
        from interface_scale import InterfaceScale
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
        self.window.gridLayout_4.setContentsMargins(4, 2, 4, 8)
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
        self.tabs.addTab(self.main_page, "主界面")
        self.tabs.addTab(self.table_page, "表格")
        self.tabs.addTab(self.editor_page, "流程图")
        self.tabs.addTab(self.code_page, "多功能")
        self.tabs.addTab(self.recording_page, "录制")
        separator = QFrame(self.tabs.tabBar())
        separator.setObjectName("workspaceTabSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedSize(10, 20)
        separator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.tabs.tabBar().setTabButton(RECORDING_VIEW, QTabBar.ButtonPosition.LeftSide, separator)
        self.web_recording_page = WebRecordingView(self.window)
        self.tabs.addTab(self.web_recording_page, "网页录制")

    def _build_main_view(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mainWorkspacePage")
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
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(48)
        for column, width in enumerate((64, 72, 140, 360, 64, 160, 180)):
            header.resizeSection(column, width)
        self.command_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
        table_layout.setContentsMargins(6, 4, 6, 4)
        table_layout.setSpacing(4)
        table_title = QLabel("指令表格")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        self.table_state = QLabel()
        self.table_state.setWordWrap(True)
        self.table_state.setObjectName("mutedText")
        table_layout.addWidget(self.table_state)
        table_layout.addWidget(self.command_table, 1)

        log_panel = QFrame()
        log_panel.setObjectName("workspacePanel")
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(6, 4, 6, 4)
        log_layout.setSpacing(4)
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
        self.command_table.setMinimumHeight(0)
        self.command_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.table_splitter.addWidget(table_panel)
        self.table_splitter.addWidget(log_panel)
        self.table_splitter.setStretchFactor(0, 3)
        self.table_splitter.setStretchFactor(1, 2)
        self.table_splitter.setHandleWidth(8)
        sizes = [520,260]
        try:
            saved = json.loads(self.window.db.get_setting_value('表格日志面板高度') or 'null')
            if isinstance(saved,list) and len(saved)==2 and all(isinstance(v,int) and v>0 for v in saved): sizes=saved
        except (TypeError, ValueError): pass
        self.table_splitter.setSizes(sizes)
        self.table_splitter.splitterMoved.connect(lambda *_: self.window.db.set_setting_value('表格日志面板高度',json.dumps(self.table_splitter.sizes())))
        self.window.horizontalLayout.setContentsMargins(2, 2, 2, 2)
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
        self.write_code_button = QPushButton("写入表格与流程图")
        self.write_code_button.setToolTip("按代码更新当前流程；遗漏参数填入默认值，写入后可在表格中修改。")
        self.write_code_button.clicked.connect(self.write_code_to_flow)
        header.addWidget(self.write_code_button)
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
        from guided_code_editor import GuidedCodeEditor
        self.code_editor = GuidedCodeEditor()
        palette = self.window.workspace.palette
        self.code_editor.set_guidance_enabled(palette.guidance_enabled)
        palette.guidanceEnabledChanged.connect(self.code_editor.set_guidance_enabled)
        hint = QLabel("中文输入提示：↑↓选择，Tab / 回车插入，Esc关闭；Ctrl+空格查看下一步。模板参数可继续修改。")
        hint.setWordWrap(True)
        hint.setVisible(palette.guidance_enabled)
        palette.guidanceEnabledChanged.connect(hint.setVisible)
        layout.addWidget(hint)
        self.code_editor.textChanged.connect(self._schedule_code_save)
        splitter.addWidget(self.command_list)
        splitter.addWidget(self.code_editor)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)
        return page

    def _build_navigation(self) -> None:
        self._toolbar_dock_filter = _ToolbarDockOnDoubleClick(self.window, self.window.toolBar)
        self.window.toolBar.setWindowTitle('显示工具栏')
        self.window.toolBar.toggleViewAction().setText('显示工具栏')
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
        self.controls_action = QAction('展开控制与操作' if self.controls_collapsed else '收起控制与操作', self.window)
        self.controls_action.setCheckable(True)
        self.controls_action.setChecked(not self.controls_collapsed)
        self.controls_action.toggled.connect(self.set_controls_visible)
        self.donation_action = QAction("捐赠", self.window)
        self.donation_action.triggered.connect(self.show_donation)
        self.window.toolBar.addSeparator()
        self.window.toolBar.addAction(self.primary_action)
        self.window.toolBar.addAction(self.code_action)
        self.window.toolBar.addSeparator()
        self.window.toolBar.addAction(self.palette_side_action)
        self.window.toolBar.addAction(self.palette_collapse_action)
        self.window.toolBar.addAction(self.controls_action)
        self.window.menubar.addAction(self.donation_action)
        from window_chrome import install_title_bar
        self.title_bar = install_title_bar(self.window, self.theme_action)
        self.title_bar.apply_theme(self.theme_mode, self.THEMES[self.theme_mode])
        from compact_workspace import CompactWorkspace
        self.compact = CompactWorkspace(self)
        menu = QMenu("视图", self.window)
        self.view_menu = menu
        view_actions = {}
        for label, shortcut, callback in (
            ("主界面", "Ctrl+1", self.show_main),
            ("表格", "Ctrl+2", self.show_table),
            ("流程图", "Ctrl+3", self.show_flow),
            ("多功能", "Ctrl+4", self.show_code),
            ("录制", "Ctrl+6", self.show_recording),
            ("网页录制", "Ctrl+7", self.show_web_recording),
            ("设置变量", "Ctrl+Shift+V", self.show_variables),
        ):
            action = QAction(label, self.window)
            action.setShortcut(QKeySequence(shortcut))
            view_actions[label] = action
            action.triggered.connect(callback)
            menu.addAction(action)
        self.window.menubar.insertMenu(self.window.menu_4.menuAction(), menu)
        self.font_size_menu = QMenu('界面字号', self.window)
        self.window.menubar.insertMenu(self.window.menu_4.menuAction(), self.font_size_menu)
        for label, amount in [('字号+', 1), ('字号-', -1), ('字号恢复默认', None)]:
            action = self.font_size_menu.addAction(label)
            action.triggered.connect(lambda checked=False, step=amount: self.interface_scale.change(step))
        menu.addSeparator()
        self.window.menu_3.removeAction(self.window.actiong)
        self.window.actiong.setText('显示工具栏')
        menu.addAction(self.window.actiong)
        menu.addAction(self.controls_action)
        self.restore_view_action = QAction('恢复默认界面', self.window)
        self.restore_view_action.triggered.connect(lambda: self.layout_presets.reset())
        self.layout_menu = QMenu('界面方案', self.window)
        self.window.menubar.insertMenu(menu.menuAction(), self.layout_menu)
        from layout_presets import LayoutPresets
        self.layout_presets = LayoutPresets(self, self.layout_menu)
        self.editable_view_action = menu.addAction('可编辑视图')
        self.editable_view_action.setCheckable(True)
        self.editable_view_action.setChecked(self.window.db.get_setting_value('可编辑视图') != 'False')
        self.editable_view_action.setToolTip('勾选可拖拽布局；取消后只能通过右键菜单内嵌面板')
        self.editable_view_action.toggled.connect(lambda enabled: self.docking.set_editable(enabled))
        view_actions['显示工具栏'] = self.window.actiong
        guidance_action = QAction('中文编程提示', self.window)
        guidance_action.setCheckable(True)
        palette = self.window.workspace.palette
        guidance_action.setChecked(palette.guidance_enabled)
        guidance_action.toggled.connect(palette.set_guidance_enabled)
        palette.guidanceEnabledChanged.connect(guidance_action.setChecked)
        self.window.menu_4.addAction(guidance_action)
        view_actions['中文编程提示'] = guidance_action
        menu.addSeparator()
        from view_shortcuts import install_view_shortcuts
        install_view_shortcuts(self.window, self.window.menu_4, view_actions)
        self.window.menubar.removeAction(self.window.menu_3.menuAction())
        from context_menu_style import install_menu_styling
        install_menu_styling(self.window)

    def toggle_primary(self) -> None:
        self.show_main() if self.tabs.currentIndex() == FLOW_VIEW else self.show_flow()

    def _show_workspace(self, index):
        self.tabs.setCurrentIndex(index)
        if hasattr(self, 'docking'): self.docking.sync_visibility()

    def show_main(self): self._show_workspace(MAIN_VIEW)
    def show_table(self): self._show_workspace(TABLE_VIEW)
    def show_flow(self): self._show_workspace(FLOW_VIEW)
    def show_code(self):
        self._load_code()
        self._show_workspace(CODE_VIEW)
    def show_navigation(self): self.show_main()
    def show_recording(self): self._show_workspace(RECORDING_VIEW)

    def show_web_recording(self): self._show_workspace(WEB_RECORDING_VIEW)

    # Backward-compatible aliases for integrations that used the earlier names.
    def show_beginner(self): self.show_navigation()
    def show_editor(self): self.show_flow()

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
            "返回主界面" if self.tabs.currentIndex() == FLOW_VIEW else "打开流程图"
        )
        self.palette_side_action.setText(
            "指令栏移到左侧" if self.palette_side == "right" else "指令栏移到右侧"
        )
        self.palette_collapse_action.setText(
            "展开指令栏" if self.palette_collapsed else "收起指令栏"
        )
        self.controls_action.setText('展开控制与操作' if self.controls_collapsed else '收起控制与操作')
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
                f"流程节点  {len(snapshot.nodes)}\n可执行指令  {len(snapshot.commands)}\n"
                f"多功能代码  {code_lines} 行"
            )
            self.main_stats.setText(summary)
        except Exception as error:
            summary = f"任务状态暂不可用：{error}"
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
        rows = []
        for row, command in enumerate(commands):
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            parameters_text = json.dumps(
                command.parameters, ensure_ascii=False, sort_keys=True, separators=(", ", ": ")
            )
            rows.append((command.id, (
                str(row + 1), f"#{command.id}", display_name, parameters_text,
                str(command.repeat_count), command.error_policy, command.note,
            )))
        table = self.command_table
        previous_rows = getattr(self, "_table_rows", [])
        if rows == previous_rows:
            if hasattr(table, 'update_comment_ranges'):
                table.update_comment_ranges(snapshot)
            self._apply_comment_row_colors(snapshot)
            return
        order_changed = [r[0] for r in rows] != [r[0] for r in previous_rows]
        selected = [(table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole), index.column())
                    for index in table.selectedIndexes()]
        current = table.currentItem()
        current_cell = (current.data(Qt.ItemDataRole.UserRole), table.currentColumn()) if current else None
        scroll_x, scroll_y = table.horizontalScrollBar().value(), table.verticalScrollBar().value()
        updates_enabled = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            with QSignalBlocker(table):
                if order_changed:
                    table.clearSelection()
                table.setRowCount(len(rows))
                for row, (command_id, values) in enumerate(rows):
                    if row < len(previous_rows) and rows[row] == previous_rows[row]:
                        continue
                    for column, value in enumerate(values):
                        item = table.item(row, column)
                        if item is None:
                            item = QTableWidgetItem(value)
                            table.setItem(row, column, item)
                        elif item.text() != value:
                            item.setText(value)
                        if item.data(Qt.ItemDataRole.UserRole) != command_id:
                            item.setData(Qt.ItemDataRole.UserRole, command_id)
                        if item.toolTip() != value:
                            item.setToolTip(value)
                if hasattr(table, 'update_comment_ranges'):
                    table.update_comment_ranges(snapshot)
                self._apply_comment_row_colors(snapshot)
                self._table_rows = rows
                self._table_command_rows = {command_id: row for row, (command_id, _) in enumerate(rows)}
                if order_changed:
                    if current_cell and current_cell[0] in self._table_command_rows:
                        table.setCurrentCell(self._table_command_rows[current_cell[0]], current_cell[1], QItemSelectionModel.NoUpdate)
                    else:
                        table.setCurrentCell(-1, -1, QItemSelectionModel.NoUpdate)
                    for command_id, column in selected:
                        row = self._table_command_rows.get(command_id)
                        if row is not None:
                            table.selectionModel().select(table.model().index(row, column), QItemSelectionModel.Select)
                self.highlight_running_command(self.running_command_id, ensure_visible=False)
                table.horizontalScrollBar().setValue(scroll_x)
                table.verticalScrollBar().setValue(scroll_y)
        finally:
            table.setUpdatesEnabled(updates_enabled)

    def _apply_comment_row_colors(self, snapshot):
        from flow_comments import snapshot_disabled_ids
        disabled = snapshot_disabled_ids(snapshot)
        dark = getattr(self, 'theme_mode', 'light') == 'dark'
        background = QColor('#3c3c40' if dark else '#dedee3')
        foreground = QColor('#d4d4d8' if dark else '#53535c')
        table = self.command_table
        appearance = (dark, tuple((table.item(row, 0).data(Qt.ItemDataRole.UserRole) if table.item(row, 0) else None)
                                  for row in range(table.rowCount())), frozenset(disabled))
        if appearance == getattr(self, '_table_comment_appearance', None):
            return
        self._table_comment_appearance = appearance
        for row in range(table.rowCount()):
            first = table.item(row, 0)
            inactive = first is not None and first.data(Qt.ItemDataRole.UserRole) in disabled
            for column in range(table.columnCount()):
                item = table.item(row, column)
                if item is not None:
                    item.setData(Qt.ItemDataRole.BackgroundRole, background if inactive else None)
                    item.setData(Qt.ItemDataRole.ForegroundRole, foreground if inactive else None)

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
        if ensure_visible and table.runtime_row >= 0 and self.tabs.currentIndex() == TABLE_VIEW:
            table.scrollToItem(table.item(table.runtime_row, 0), QAbstractItemView.ScrollHint.EnsureVisible)
        table.viewport().update()

    def _add_table_command(self, type_id: str) -> None:
        self.window.workspace.add_palette_command(type_id)
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
        if (thread is not None and thread.isRunning()) or self.recording_page.busy or self.web_recording_page.busy:
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
        from qt_compat.QtWidgets import QTableWidgetSelectionRange
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
        if self.code_editor.toPlainText() != text:
            with QSignalBlocker(self.code_editor): self.code_editor.setPlainText(text)
        self._loading_code = False
        self.code_status.setText(
            "修改会自动保存在当前任务中"
            if validation_error is None
            else "已同步流程草稿，可按连线优先、其余按添加顺序运行"
        )

    def write_code_to_flow(self) -> None:
        window = self.window
        if (window.command_thread.isRunning() or self.recording_page.busy
                or self.web_recording_page.busy
                or getattr(window.workspace, '_instruction_test_active', False)
                or getattr(window, '_update_preparing', False)):
            window.statusBar.showMessage('请先停止任务、录制或指令测试。', 4000)
            return
        try:
            from instruction_code import prepare_instruction_conversion
            from instruction_conversion_dialog import InstructionConversionDialog
            plan = prepare_instruction_conversion(self.code_editor.toPlainText())
            dialog = InstructionConversionDialog(plan, window)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            ids = window.workspace.repository.write_instruction_code(plan.entries)
        except Exception as error:
            QMessageBox.warning(window, '写入失败，原流程未改变', str(error))
            return
        self._code_dirty = False
        window.workspace.clear_connection_history()
        window.workspace.reload_graph()
        window.workspace.graphFinalized.emit(False)
        self._sync_code_if_needed(force=True)
        self.refresh_all()
        self.code_status.setText(f'已写入 {len(ids)} 条指令；可在表格中修改参数')
        window.statusBar.showMessage('表格与流程图已同步；缺省参数已补齐，可双击表格修改。', 5000)

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
            kind_names = {0: "下一步", 1: "是", 2: "否", 3: "循环体", 4: "完成",
                          5: "报错", 6: "异常跳转", 7: "比较是跳转", 8: "比较否跳转"}
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
        self.code_editor.insert_command(type_id)
        self.code_editor.setFocus()

    def _schedule_code_save(self) -> None:
        if self._loading_code: return
        self._code_dirty = True
        self.code_status.setText("正在保存……")
        self._code_save_timer.start()

    def _save_code(self) -> None:
        self._code_save_timer.stop()
        if not self._code_dirty: return
        self.window.db.set_setting_value(CODE_SETTING, self.code_editor.toPlainText())
        self._code_dirty = False
        self.code_status.setText("已自动保存")

    def _align_search_row(self):
        palette = self.window.workspace.palette
        palette.search_edit.ensurePolished()
        height = palette.search_edit.fontMetrics().height() + 4
        palette.search_edit.setFixedHeight(height)
        palette.search_row.setFixedHeight(max(height + 2, self.tabs.tabBar().sizeHint().height()))

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
            QDockWidget {{ color: {c['text']}; font-size: 12px; border: none; }}
            QLabel#dockPanelTitle {{ background: {c['surface2']}; color: {c['text']}; font-size: 12px; border: none; border-radius: 5px; }}
            QDockWidget::title {{ background: {c['surface2']}; padding: 5px; border-radius: 5px; }}
            QMainWindow::separator {{ background: {c['bg']}; width: 5px; height: 5px; }}
            QMainWindow, QWidget#centralwidget {{ background: {c['bg']}; color: {c['text']}; }}
            QWidget {{ font-family: 'Microsoft YaHei UI'; font-size: 13px; }}
            QLabel {{ color: {c['text']}; }}
            QWidget#instructionEditorBody {{ background: {c['bg']}; color: {c['text']}; }}
            QDockWidget[instructionParameter="true"], QScrollArea#parameterScroll,
            QWidget#parameterViewport {{ background: {c['bg']}; color: {c['text']}; border: none; }}
            QWidget#tab, QWidget#editorView, QWidget#multifunctionView,
            QWidget#beginnerView, QStackedWidget {{ background: {c['bg']}; color: {c['text']}; }}
            QMenuBar, QMenu, QToolBar {{ background: {c['nav']}; color: {c['text']}; border-color: {c['line']}; spacing: 4px; }}
            QMenu {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 10px; padding: 4px; font-size: 12px; }}
            QMenu::item {{ padding: 3px 18px 3px 20px; margin: 0; border: none; border-radius: 5px; font-size: 12px; }}
            QMenu::item:disabled {{ color: {c['dim']}; background: transparent; }}
            QMenu::separator {{ height: 1px; background: {c['line']}; margin: 3px 7px; }}
            QMenuBar::item:selected, QMenu::item:selected {{ background: {c['surface3']}; color: {c['accent']}; }}
            QToolBar {{ border-bottom: 1px solid {c['line']}; padding: 0px 2px; spacing: 2px; font-size: 11px; }}
            QToolBar QToolButton {{ padding: 2px 5px; border-radius: 4px; font-size: 11px; }}
            QToolBar QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; }}
            QTabWidget::pane {{ border: none; background: {c['bg']}; top: 0px; }}
            QTabBar::tab {{ background: {c['surface']}; color: {c['dim']}; padding: 4px 12px; border: 1px solid {c['line']}; border-radius: 8px; margin: 2px; }}
            QTabBar::tab:selected {{ background: {c['accent']}; color: {c['accent_text']}; font-weight: 700; }}
            QTabBar::tab:hover:!selected {{ background: {c['surface3']}; color: {c['accent']}; }}
            QWidget#instructionPaletteHost, QGroupBox#groupBox_3 {{ background: {c['surface']}; color: {c['text']}; border: none; border-radius: 12px; }}
            QWidget#instructionTreeSurface {{ background: {c['surface2']}; border: none; border-radius: 12px; }}
            QTreeWidget#instructionTree {{ border: none; background: transparent; }}
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
            QFrame#workspacePanel {{ background: {c['surface']}; border: none; border-radius: 12px; }}
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
            QLineEdit#instructionSearchEdit {{ padding: 1px 6px; min-height: 0px; border-radius: 4px; }}
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
            QTableWidget#commandTable {{ background-color: {c['surface']}; alternate-background-color: {c['surface2']}; border: none; }}
            QTableWidget#commandTable::item {{ border: none; padding: 5px; }}
            QTableWidget#commandTable::item:hover:!selected {{ border-bottom: 1px solid {c['accent']}; }}
            QTextEdit#textEdit {{ background: {c['nav']}; color: {c['text']}; border: none; border-radius: 10px; padding: 8px; }}
            QTableWidget#commandTable::item:selected, QTableWidget#commandTable::item:selected:alternate {{ background-color: {c['accent2']}; color: white; }}
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
            QFrame#recordingOptionSeparator {{ background: {c['line']}; border: none; }}
            QFrame#workspaceTabSeparator {{ background: transparent; border: none; border-left: 1px solid {c['line']}; margin-left: 4px; }}
            QSplitter::handle {{ background: transparent; }}
            QSplitter::handle:horizontal {{ border: none; background: transparent; margin: 0px; }}
            QSplitter::handle:vertical {{ border: none; background: transparent; margin: 0px; }}
            QSplitter::handle:horizontal:hover {{ border: none; background: transparent; }}
            QSplitter::handle:vertical:hover {{ border: none; background: transparent; }}

            QWidget#mainWorkspacePage {{ background: {c['bg']}; border: none; }}
            QScrollArea#controlsScroll, QWidget#controlsScrollViewport {{ background: {c['bg']}; border: none; }}
            QStatusBar {{ background: {c['bg']}; color: {c['dim']}; border: none; padding: 0px 6px; }}
            QStatusBar::item {{ border: none; }}
            QStatusBar QSizeGrip {{ background: transparent; }}
            QGroupBox {{ color: {c['accent']}; background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 10px; margin-top: 10px; padding-top: 10px; font-weight: 700; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        """)
        QTimer.singleShot(0, self._align_search_row)
