"""Linked Clicker workspaces and the light/dark desktop themes."""
from __future__ import annotations
import weakref
import json
from anclicker.platform.qt_compat.QtCore import QSignalBlocker, Signal, Qt, QMimeData, QItemSelectionModel
from anclicker.platform.qt_compat.QtGui import QColor, QKeySequence, QPalette, QDrag, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import QAbstractItemView, QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QMenu, QMessageBox, QSplitter, QSizePolicy, QTableWidget, QStyledItemDelegate, QStyle, QTableWidgetItem, QVBoxLayout
from anclicker.ui.node_editor.palette import INSTRUCTION_MIME_TYPE

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'connected_fold_ranges': ('from', 'anclicker.domain.flow_comments', ('connected_fold_ranges',), 0),
    'loop_groups': ('from', 'anclicker.domain.flow_loop_table', ('loop_groups',), 0),
    'style_context_menu': ('from', 'anclicker.ui.context_menu_style', ('style_context_menu',), 0),
    'snapshot_disabled_ids': ('from', 'anclicker.domain.flow_comments', ('snapshot_disabled_ids',), 0),
    'asdict': ('from', 'dataclasses', ('asdict',), 0),
    'InstructionDraft': ('from', 'anclicker.domain.instructions', ('InstructionDraft',), 0),
    'QTableWidgetSelectionRange': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QTableWidgetSelectionRange',), 0),
})


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
        self.loop_ranges = {}
        self.collapsed_loops = set()
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
        return [int(self.item(row, 0).data(Qt.ItemDataRole.UserRole)) for row in rows if self.item(row, 0) is not None]

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
        connected_fold_ranges = _module_imports.load('connected_fold_ranges')
        self.comment_ranges = connected_fold_ranges(snapshot)
        loop_groups = _module_imports.load('loop_groups')
        self.loop_ranges = loop_groups(snapshot)
        self.collapsed_loops.intersection_update(self.loop_ranges)
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

    def set_loop_collapsed(self, command_id, collapsed):
        if command_id not in self.loop_ranges:
            return
        if collapsed:
            self.collapsed_loops.add(command_id)
        else:
            self.collapsed_loops.discard(command_id)
        self.apply_comment_folds()

    def apply_comment_folds(self):
        hidden = set()
        for command_id in self.collapsed_comments:
            hidden.update(self.comment_ranges.get(command_id, ()))
        for command_id in self.collapsed_loops:
            hidden.update(self.loop_ranges.get(command_id, ()))
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            label = self.item(row, 2)
            if item is not None and label is not None:
                command_id = item.data(Qt.ItemDataRole.UserRole)
                base = label.toolTip()
                depth = sum((command_id in members for members in self.loop_ranges.values()))
                prefix = '\u3000' * min(depth, 8)
                if command_id in self.loop_ranges:
                    arrow = '▸' if command_id in self.collapsed_loops else '▾'
                    label.setText(f'{prefix}{arrow} {base}（{len(self.loop_ranges[command_id])} 条）')
                elif label.text() != prefix + base:
                    label.setText(prefix + base)
            self.setRowHidden(row, item is not None and item.data(Qt.ItemDataRole.UserRole) in hidden)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and (not self.selectionModel().isSelected(index)):
            self.clearSelection()
            self.setCurrentCell(index.row(), index.column())
        menu = QMenu(self)
        style_context_menu = _module_imports.load('style_context_menu')
        style_context_menu(menu, self)
        item = self.item(index.row(), 0) if index.isValid() else None
        command_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if command_id in self.loop_ranges:
            expand_loop = menu.addAction('展开循环内容', lambda : self.set_loop_collapsed(command_id, False))
            collapse_loop = menu.addAction('收起循环内容', lambda : self.set_loop_collapsed(command_id, True))
            expand_loop.setEnabled(command_id in self.collapsed_loops)
            collapse_loop.setEnabled(command_id not in self.collapsed_loops)
            menu.addSeparator()
        if command_id in self.comment_ranges:
            expand = menu.addAction('展开下部指令', lambda : self.set_comment_collapsed(command_id, False))
            collapse = menu.addAction('收缩下部指令', lambda : self.set_comment_collapsed(command_id, True))
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
        if event.button() == Qt.MouseButton.LeftButton and index.isValid() and (index.column() == 0):
            self.selectRow(index.row())
            self._row_press = (event.position().toPoint(), self.item(index.row(), 0).data(Qt.ItemDataRole.UserRole))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._row_press is not None and event.buttons() & Qt.MouseButton.LeftButton:
            (origin, command_id) = self._row_press
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
            return bytes(event_.mimeData().data(INSTRUCTION_MIME_TYPE)).decode('utf-8')
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
            y = self.rowViewportPosition(row) if row < self.rowCount() else self.rowViewportPosition(row - 1) + self.rowHeight(row - 1) if row else 0
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

class InstructionTableController:

    def __init__(self, workspace):
        self.workspace = weakref.proxy(workspace)

    def _build_table_view(self) -> None:
        workspace = self.workspace
        workspace.command_table = InstructionTableWidget(0, 7)
        workspace.command_table.setObjectName('commandTable')
        workspace.command_table.setMouseTracking(True)
        workspace.command_table.setHorizontalHeaderLabels(['序号', '编号', '指令', '参数', '重复', '异常处理', '备注'])
        workspace.command_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        workspace.command_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        workspace.command_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        workspace.command_table.setAlternatingRowColors(True)
        workspace.command_table.setShowGrid(False)
        workspace.command_table.setWordWrap(False)
        workspace.command_table.verticalHeader().setVisible(False)
        workspace.command_table.verticalHeader().setDefaultSectionSize(38)
        header = workspace.command_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(48)
        for (column, width) in enumerate((64, 72, 140, 360, 64, 160, 180)):
            header.resizeSection(column, width)
        workspace.command_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        workspace.command_table.cellDoubleClicked.connect(workspace._edit_table_command)
        workspace.command_table.instructionDropped.connect(workspace._add_table_command)
        workspace.command_table.deleteRequested.connect(workspace.delete_table_commands)
        workspace.command_table.copyRequested.connect(workspace.copy_table_commands)
        workspace.command_table.pasteRequested.connect(workspace.paste_table_commands)
        workspace.command_table.rowsMoved.connect(workspace.move_table_commands)
        workspace.command_table.setToolTip('拖动序号上下排序；其他单元格拖动框选，Ctrl+C / Ctrl+V 复制粘贴，Delete 删除选中行')
        workspace.window.horizontalLayout.removeWidget(workspace.window.textEdit)
        workspace.window.horizontalLayout.removeItem(workspace.window.verticalLayout)
        for button in (workspace.window.toolButton_8, workspace.window.toolButton_7):
            workspace.window.verticalLayout.removeWidget(button)
        table_panel = QFrame()
        table_panel.setObjectName('workspacePanel')
        table_panel.setProperty('attachedToNavigation', True)
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(6, 6, 6, 4)
        table_layout.setSpacing(4)
        table_title = QLabel('指令表格')
        table_title.setObjectName('sectionTitle')
        table_layout.addWidget(table_title)
        workspace.table_state = QLabel()
        workspace.table_state.setWordWrap(True)
        workspace.table_state.setObjectName('mutedText')
        table_layout.addWidget(workspace.table_state)
        table_layout.addWidget(workspace.command_table, 1)
        log_panel = QFrame()
        log_panel.setObjectName('workspacePanel')
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(6, 4, 6, 4)
        log_layout.setSpacing(4)
        log_header = QHBoxLayout()
        log_title = QLabel('运行日志')
        log_title.setObjectName('sectionTitle')
        log_header.addWidget(log_title)
        log_header.addStretch(1)
        workspace.window.toolButton_8.setText('导出日志')
        workspace.window.toolButton_7.setText('清空日志')
        log_header.addWidget(workspace.window.toolButton_8)
        log_header.addWidget(workspace.window.toolButton_7)
        log_layout.addLayout(log_header)
        log_layout.addWidget(workspace.window.textEdit, 1)
        workspace.table_splitter = QSplitter(Qt.Orientation.Vertical)
        workspace.table_splitter.setObjectName('tableLogSplitter')
        workspace.table_splitter.setChildrenCollapsible(False)
        workspace.command_table.setMinimumHeight(0)
        workspace.command_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        workspace.table_splitter.addWidget(table_panel)
        workspace.table_splitter.addWidget(log_panel)
        workspace.table_splitter.setStretchFactor(0, 3)
        workspace.table_splitter.setStretchFactor(1, 2)
        workspace.table_splitter.setHandleWidth(8)
        sizes = [520, 260]
        try:
            saved = json.loads(workspace.window.db.get_setting_value('表格日志面板高度') or 'null')
            if isinstance(saved, list) and len(saved) == 2 and all((isinstance(v, int) and v > 0 for v in saved)):
                sizes = saved
        except (TypeError, ValueError):
            pass
        workspace.table_splitter.setSizes(sizes)
        workspace.table_splitter.splitterMoved.connect(lambda *_: workspace.window.db.set_setting_value('表格日志面板高度', json.dumps(workspace.table_splitter.sizes())))
        workspace.window.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        workspace.window.horizontalLayout.addWidget(workspace.table_splitter, 1)

    def refresh_table(self) -> None:
        workspace = self.workspace
        (snapshot, validation_error) = workspace._current_graph_state()
        commands = list(snapshot.commands)
        if validation_error is None:
            workspace.table_state.setText(f'流程、表格与多功能已同步，共 {len(commands)} 条指令')
        else:
            workspace.table_state.setText(f'流程草稿，共 {len(commands)} 条指令；{validation_error}')
        nodes_by_command = {node.command_id: node for node in snapshot.nodes if node.command_id is not None}
        rows = []
        for (row, command) in enumerate(commands):
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            parameters_text = json.dumps(command.parameters, ensure_ascii=False, sort_keys=True, separators=(', ', ': '))
            rows.append((command.id, (str(row + 1), f'#{command.id}', display_name, parameters_text, str(command.repeat_count), command.error_policy, command.note)))
        table = workspace.command_table
        previous_rows = getattr(workspace, '_table_rows', [])
        if rows == previous_rows:
            if hasattr(table, 'update_comment_ranges'):
                table.update_comment_ranges(snapshot)
            workspace._apply_comment_row_colors(snapshot)
            return
        order_changed = [r[0] for r in rows] != [r[0] for r in previous_rows]
        selected = [(table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole), index.column()) for index in table.selectedIndexes()]
        current = table.currentItem()
        current_cell = (current.data(Qt.ItemDataRole.UserRole), table.currentColumn()) if current else None
        (scroll_x, scroll_y) = (table.horizontalScrollBar().value(), table.verticalScrollBar().value())
        updates_enabled = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            with QSignalBlocker(table):
                if order_changed:
                    table.clearSelection()
                table.setRowCount(len(rows))
                for (row, (command_id, values)) in enumerate(rows):
                    if row < len(previous_rows) and rows[row] == previous_rows[row]:
                        continue
                    for (column, value) in enumerate(values):
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
                workspace._apply_comment_row_colors(snapshot)
                workspace._table_rows = rows
                workspace._table_command_rows = {command_id: row for (row, (command_id, _)) in enumerate(rows)}
                if order_changed:
                    if current_cell and current_cell[0] in workspace._table_command_rows:
                        table.setCurrentCell(workspace._table_command_rows[current_cell[0]], current_cell[1], QItemSelectionModel.NoUpdate)
                    else:
                        table.setCurrentCell(-1, -1, QItemSelectionModel.NoUpdate)
                    for (command_id, column) in selected:
                        row = workspace._table_command_rows.get(command_id)
                        if row is not None:
                            table.selectionModel().select(table.model().index(row, column), QItemSelectionModel.Select)
                workspace.highlight_running_command(workspace.running_command_id, ensure_visible=False)
                table.horizontalScrollBar().setValue(scroll_x)
                table.verticalScrollBar().setValue(scroll_y)
        finally:
            table.setUpdatesEnabled(updates_enabled)

    def _apply_comment_row_colors(self, snapshot):
        workspace = self.workspace
        snapshot_disabled_ids = _module_imports.load('snapshot_disabled_ids')
        disabled = snapshot_disabled_ids(snapshot)
        dark = getattr(workspace, 'theme_mode', 'light') == 'dark'
        background = QColor('#3c3c40' if dark else '#dedee3')
        foreground = QColor('#d4d4d8' if dark else '#53535c')
        table = workspace.command_table
        appearance = (dark, tuple((table.item(row, 0).data(Qt.ItemDataRole.UserRole) if table.item(row, 0) else None for row in range(table.rowCount()))), frozenset(disabled))
        if appearance == getattr(workspace, '_table_comment_appearance', None):
            return
        workspace._table_comment_appearance = appearance
        for row in range(table.rowCount()):
            first = table.item(row, 0)
            inactive = first is not None and first.data(Qt.ItemDataRole.UserRole) in disabled
            for column in range(table.columnCount()):
                item = table.item(row, column)
                if item is not None:
                    item.setData(Qt.ItemDataRole.BackgroundRole, background if inactive else None)
                    item.setData(Qt.ItemDataRole.ForegroundRole, foreground if inactive else None)

    def _add_table_command(self, type_id: str) -> None:
        workspace = self.workspace
        workspace.window.workspace.add_palette_command(type_id)
        workspace.refresh_table()
        workspace.window.statusBar.showMessage(f'已从指令栏添加：{type_id}', 2500)

    def _edit_table_command(self, row: int, _column: int) -> None:
        workspace = self.workspace
        if _column == 0 or not workspace._table_mutation_allowed():
            return
        item = workspace.command_table.item(row, 0)
        if item is not None:
            workspace.window.workspace.edit_command(item.data(Qt.ItemDataRole.UserRole))
            workspace.refresh_all()

    def _table_mutation_allowed(self):
        workspace = self.workspace
        thread = getattr(workspace.window, 'command_thread', None)
        if thread is not None and thread.isRunning() or workspace.recording_page.busy or workspace.web_recording_page.busy:
            workspace.window.statusBar.showMessage('请先停止运行或录制，再修改表格。', 3000)
            return False
        return True

    def delete_table_commands(self):
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return 0
        ids = workspace.command_table.selected_command_ids()
        if not ids:
            return 0
        return workspace.window.workspace.remove_commands(ids)

    def copy_table_commands(self):
        workspace = self.workspace
        asdict = _module_imports.load('asdict')
        ids = set(workspace.command_table.selected_command_ids())
        commands = [c for c in workspace.window.workspace.repository.list_commands() if c.id in ids]
        if not commands:
            return
        mime = QMimeData()
        payload = json.dumps([asdict(c.to_draft()) for c in commands], ensure_ascii=False)
        mime.setData('application/x-anclicker-commands', payload.encode('utf-8'))
        mime.setText('\n'.join((f'{c.type_id}\t{json.dumps(c.parameters, ensure_ascii=False)}\t{c.repeat_count}\t{c.note}' for c in commands)))
        QApplication.clipboard().setMimeData(mime)
        workspace.window.statusBar.showMessage(f'已复制 {len(commands)} 条指令', 2500)

    def paste_table_commands(self):
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return
        mime = QApplication.clipboard().mimeData()
        if mime is None or not mime.hasFormat('application/x-anclicker-commands'):
            workspace.window.statusBar.showMessage('请先在指令表格中复制指令。', 2500)
            return
        try:
            InstructionDraft = _module_imports.load('InstructionDraft')
            raw = bytes(mime.data('application/x-anclicker-commands'))
            if len(raw) > 10000000:
                raise ValueError('复制内容过大，请分批粘贴')
            data = json.loads(raw)
            if not isinstance(data, list) or not 0 < len(data) <= 10000 or (not all((isinstance(x, dict) for x in data))):
                raise ValueError('剪贴板不是有效的指令列表')
            drafts = [InstructionDraft.from_mapping(item) for item in data]
            ids = workspace.window.workspace.repository.append_recording(drafts, connect=False)
            workspace.window.workspace.reload_graph(ids[0])
            workspace.window.workspace.graphFinalized.emit(False)
            workspace._select_table_ids(ids)
            workspace.window.statusBar.showMessage(f'已粘贴 {len(ids)} 条指令，表格与流程图已同步', 3000)
        except Exception as error:
            QMessageBox.warning(workspace.window, '粘贴失败', str(error))

    def _select_table_ids(self, ids):
        workspace = self.workspace
        QTableWidgetSelectionRange = _module_imports.load('QTableWidgetSelectionRange')
        workspace.command_table.clearSelection()
        for row in range(workspace.command_table.rowCount()):
            if workspace.command_table.item(row, 0).data(Qt.ItemDataRole.UserRole) in ids:
                workspace.command_table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, workspace.command_table.columnCount() - 1), True)

    def move_table_commands(self, ids, destination):
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return
        repo = workspace.window.workspace.repository
        current = [c.id for c in repo.list_commands()]
        moved = [item for item in current if item in ids]
        remaining = [item for item in current if item not in ids]
        destination = max(0, min(destination, len(current)))
        index = destination - sum((item in ids for item in current[:destination]))
        ordered = remaining[:index] + moved + remaining[index:]
        if ordered == current:
            return
        try:
            rewired = repo.reorder_table_commands(ordered)
            workspace.window.workspace.reload_graph(moved[0])
            workspace.window.workspace.graphFinalized.emit(False)
            workspace._select_table_ids(moved)
            workspace.window.statusBar.showMessage('已同步表格排序和流程图' + ('；顺序连线已调整' if rewired else '；现有分支连线保持不变'), 4000)
        except Exception as error:
            QMessageBox.warning(workspace.window, '移动失败', str(error))
