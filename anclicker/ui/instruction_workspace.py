"""Main-window integration for the instruction palette and node canvas."""

from __future__ import annotations
from anclicker.ui.instruction_clipboard import set_command_mime

import json
import math
import weakref
from pathlib import Path
from dataclasses import asdict
from anclicker.platform.image_paths import store_image_reference
from typing import Optional

from anclicker.platform.qt_compat.QtCore import QObject, Signal, QTimer, Qt, QMimeData
from anclicker.platform.qt_compat.QtWidgets import QDialog, QInputDialog, QMessageBox, QApplication

from anclicker.storage.graph_repository import END_NODE_ID, GraphRepository
from anclicker.domain.instructions import CommandRecord, ExecutionContext, InstructionDraft
from anclicker.execution.services import EditorContext
from anclicker.app.state import application_state
from anclicker.instructions.registry import INSTRUCTION_SPECS, get_instruction_spec
from anclicker.ui.node_editor import InstructionPalette, NodeEditorWidget
from anclicker.ui.drag_feedback import visual_only, feedback_call
from anclicker.domain.step_folding import folding_groups, hidden_steps, group_title, copy_group_drafts, locked_move_ids

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'OCR_TYPES': ('from', 'anclicker.ui.instruction_editors.local_ocr_instruction', ('OCR_TYPES',), 0),
    'snapshot_disabled_ids': ('from', 'anclicker.domain.flow_comments', ('snapshot_disabled_ids',), 0),
    'QGraphicsColorizeEffect': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QGraphicsColorizeEffect',), 0),
    'QColor': ('from', 'anclicker.platform.qt_compat.QtGui', ('QColor',), 0),
    'SmartCaptureDialog_capture_path': ('from', 'anclicker.ui.smart_capture', ('SmartCaptureDialog', 'capture_path'), 0),
    'IMAGES_FOLDER': ('from', 'anclicker.app.paths', ('IMAGES_FOLDER',), 0),
    'SmartCaptureDialog': ('from', 'anclicker.ui.smart_capture', ('SmartCaptureDialog',), 0),
    'QInputDialog': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QInputDialog',), 0),
    'InstructionDraft': ('from', 'anclicker.domain.instructions', ('InstructionDraft',), 0),
    'CATALOG': ('from', 'anclicker.ui.instruction_editors.rpa_instruction', ('CATALOG',), 0),
    'ParameterPinFilter_PIN_RESULT': ('from', 'anclicker.ui.dock_workspace', ('ParameterPinFilter', 'PIN_RESULT'), 0),
    'AdaptivePanelSizer': ('from', 'anclicker.ui.adaptive_panels', ('AdaptivePanelSizer',), 0),
    'start_preload': ('from', 'anclicker.platform.background_preload', ('start_preload',), 0),
    'previous_binding': ('from', 'anclicker.platform.background_capture_context', ('previous_binding',), 0),
    'condition_hint': ('from', 'anclicker.domain.flow_condition_context', ('condition_hint',), 0),
    'run_cancellable_test': ('from', 'anclicker.ui.instruction_editors.test_runner', ('run_cancellable_test',), 0),
})



def _weak_callback(method, default=None):
    """Do not let view callback attributes keep their Qt owner alive in a cycle."""
    reference = weakref.WeakMethod(method)

    def call(*args, **kwargs):
        callback = reference()
        return callback(*args, **kwargs) if callback is not None else default

    return call


class InstructionWorkspace(QObject):
    """Coordinate UI-only widgets with the transactional graph repository.

    The palette and node editor deliberately know nothing about SQLite.  This
    controller is the only main-window layer that opens instruction editors and
    turns their signals into repository transactions.
    """

    statusMessage = Signal(str)
    runSingleRequested = Signal(int)
    runFromRequested = Signal(int)
    graphFinalized = Signal(bool)

    EDGE_HIT_DISTANCE = 72.0

    def __init__(self, db_path: str, parent=None) -> None:
        super().__init__(parent)
        self.parent_window = parent
        self._instruction_test_active = False
        self._instruction_test_context = None
        self.repository = GraphRepository(db_path)
        self.palette = InstructionPalette(INSTRUCTION_SPECS, parent_=parent)
        self.editor = NodeEditorWidget(parent_=parent)
        self._connection_history = []
        self._connection_redo = []
        self._connection_expected = None
        self._connect_signals()
        self.reload_graph()
        from anclicker.ui.node_editor.arrangement import CanvasArrangement
        self.arrangement = CanvasArrangement(self)
        self.editor.view.arrangement_menu = self.arrangement.add_menu

    def open_glyph_tool(self):
        from anclicker.ui.instruction_editors.vision_tools import open_glyph_tool
        open_glyph_tool(self.parent_window, self._editor_context())

    def _connect_signals(self) -> None:
        self.palette.glyphToolRequested.connect(self.open_glyph_tool, Qt.QueuedConnection)
        self.palette.quickCaptureRequested.connect(self.quick_capture)
        self.palette.quickOcrCaptureRequested.connect(self.quick_ocr_capture)
        self.palette.instructionActivated.connect(self.add_palette_command)
        self.editor.instructionDropped.connect(self.add_palette_command)
        self.editor.instructionCreateRequested.connect(self.add_command)
        self.editor.commandActivated.connect(self.edit_command)
        self.editor.scene.stepFoldRequested.connect(self.toggle_step_fold)
        self.editor.view.hoverExpandRequested.connect(self.expand_step_for_drag)
        self.editor.view.cutRequested.connect(self.cut_commands)
        self.editor.view.dissolveThreadRequested.connect(self.dissolve_thread)
        self.editor.scene.threadNestedRequested.connect(self.set_thread_nested)
        self.editor.scene.stepLocksRequested.connect(self.set_step_locks)
        self.editor.copyRequested.connect(self.copy_commands)
        self.editor.deleteRequested.connect(self.remove_commands)
        self.editor.runSingleRequested.connect(self.run_from_command_single)
        self.editor.runFromRequested.connect(self.run_from_command)
        self.editor.graphCommitted.connect(self._commit_graph_change)
        self.editor.positionCommitted.connect(self._commit_position)
        self.editor.positionsCommitted.connect(self._commit_positions)
        self.editor.sizeCommitted.connect(self._commit_size)
        self.editor.connectionRequested.connect(self._connect_nodes)
        self.editor.branchConnectionRequested.connect(self._connect_nodes)
        # Reload only after the port mouse-release handler has finished.
        self.editor.errorNodeRequested.connect(self._add_error_node, Qt.QueuedConnection)
        self.editor.deleteConnectionsRequested.connect(self._delete_connections)
        self.editor.noteChanged.connect(self._update_note)
        self.editor.saveTemplateRequested.connect(self._save_template)
        self.editor.insertTemplateRequested.connect(self._insert_template)
        self.editor.manageTemplatesRequested.connect(self._manage_templates)
        self.editor.view.template_names_provider = _weak_callback(self._template_names, ())
        self.editor.view.deleteEdgeRequested.connect(self._delete_edge)
        self.editor.view.deleteEdgesRequested.connect(self._delete_edges)
        self.editor.view.can_cut_connections = _weak_callback(self._connection_edit_allowed, False)
        self.editor.view.undoConnectionsRequested.connect(self.undo_connections)
        self.editor.view.redoConnectionsRequested.connect(self.redo_connections)
        self.editor.view.connection_undo_count = _weak_callback(self._connection_undo_count, 0)
        self.editor.view.connection_redo_count = _weak_callback(self._connection_redo_count, 0)

    def _connection_undo_count(self):
        return len(self._connection_history)

    def _connection_redo_count(self):
        return len(self._connection_redo)

    # Public node-workspace interface used by the main window.
    def selected_command_ids(self) -> list[int]:
        return [int(command_id_) for command_id_ in self.editor.selected_command_ids()]

    def focus_command(self, command_id: int) -> bool:
        return self.editor.focus_command(int(command_id))

    def reload_graph(self, focus_command_id: Optional[int] = None, *, reset_view: bool = False, positioned_ids=()) -> None:
        view = self.editor.view
        scene = self.editor.scene
        arrangement = getattr(self, 'arrangement', None)
        layout_viewport = arrangement._bounds() if arrangement is not None else None
        existing_ids = set(scene.nodes_by_command_id) | set(positioned_ids)
        preserve_view = bool(scene.nodes_by_id) and not reset_view
        transform = view.transform()
        center = view.mapToScene(view.viewport().rect().center())
        scroll_position = (view.horizontalScrollBar().value(), view.verticalScrollBar().value())
        scene_rect = scene.sceneRect()
        selected_ids = self.selected_command_ids() if preserve_view else []
        self.repository.sync_thread_groups()
        self.repository.migrate_dynamic_folds()
        self.repository.align_comment_marker_orders()
        snapshot_ = self.repository.snapshot()
        if self.repository.align_loop_orders(snapshot_):
            snapshot_ = self.repository.snapshot()
        pool = getattr(self.parent_window, 'ocr_pool', None)
        if pool is not None:
            OCR_TYPES = _module_imports.load('OCR_TYPES')
            for command in snapshot_.commands:
                if command.type_id in OCR_TYPES and command.type_id != 'OCR粘贴':
                    pool.prewarm(command.parameters.get('引擎', 'RapidOCR'), command.parameters)
        state = self._connection_state(snapshot_)
        if self._connection_expected is not None and state != self._connection_expected:
            self._connection_history.clear()
            self._connection_redo.clear()
        self._connection_expected = state
        if any(command.type_id == '绑定选择窗口' or
               (command.type_id.startswith('窗口') and command.parameters.get('模式') == '后台')
               for command in snapshot_.commands):
            _module_imports.load('start_preload')()
        db = getattr(self.parent_window, 'db', None)
        self.editor.scene.thumbnail_context = (
            str(db.get_setting_value('当前文件路径') or ''),
            tuple(db.extract_resource_folder_path() or ()),
        ) if db is not None else ('', ())
        self.editor.load_graph(
            snapshot_.nodes, snapshot_.edges, INSTRUCTION_SPECS,
            allow_incomplete=True,
        )
        snapshot_disabled_ids = _module_imports.load('snapshot_disabled_ids')
        QGraphicsColorizeEffect = _module_imports.load('QGraphicsColorizeEffect')
        QColor = _module_imports.load('QColor')
        disabled = snapshot_disabled_ids(snapshot_)
        scene = self.editor.scene
        for node in scene.nodes_by_id.values():
            node.comment_disabled = node.command_id in disabled
            if node.comment_disabled:
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor('#929292'))
                effect.setStrength(1.0)
                node.setGraphicsEffect(effect)
                node.setToolTip('已注释：不参与运行（按流程连线方向）')
        for edge in scene.edges:
            edge.comment_disabled = (edge.source_node.command_id in disabled
                                     and edge.target_node.command_id in disabled)
            if edge.source_node.node_id == 'start' and edge.target_node.command_id in disabled and edge.target_node.type_id != '暂不运行以下指令':
                edge.comment_disabled = True
            if edge.target_node.node_id == 'end' and edge.source_node.command_id in disabled and edge.source_node.type_id != '暂不运行以上指令':
                edge.comment_disabled = True
            if edge.comment_disabled:
                effect = QGraphicsColorizeEffect()
                effect.setColor(QColor('#929292'))
                effect.setStrength(1.0)
                edge.setGraphicsEffect(effect)
        self._apply_step_folds(snapshot_)
        arrangement = getattr(self, 'arrangement', None)
        if arrangement is not None:
            if reset_view:
                arrangement.bounds = None
            else:
                arranged = arrangement.place_new(snapshot_, existing_ids, layout_viewport)
                if arranged is not snapshot_:
                    snapshot_ = arranged
                    self._apply_step_folds(snapshot_)
        if preserve_view:
            # Reloading items must not fit or recenter the canvas after an edit.
            scene.setSceneRect(scene.sceneRect().united(scene_rect))
            view.setTransform(transform)
            view._zoom = transform.m11()
            view._expand_canvas(center, view._zoom)
            view.centerOn(center)
            # centerOn rounds half-pixels on Qt 5; restoring the saved scroll
            # offsets avoids cumulative camera drift across repeated edits.
            view.horizontalScrollBar().setValue(scroll_position[0])
            view.verticalScrollBar().setValue(scroll_position[1])
            view.zoomChanged.emit(view._zoom * 100)
            for command_id in selected_ids:
                node = scene.nodes_by_command_id.get(command_id)
                if node is not None:
                    node.setSelected(True)
        else:
            view.fit_graph()
        if focus_command_id is not None:
            command_id = int(focus_command_id)
            if preserve_view and command_id in existing_ids:
                node = scene.nodes_by_command_id.get(command_id)
                if node is not None:
                    node.setSelected(True)
            else:
                self.editor.focus_command(command_id)

    def _apply_step_folds(self, snapshot):
        from anclicker.domain.step_folding import folding_groups, hidden_steps, group_title, locked_move_ids
        from anclicker.platform.qt_compat.QtCore import QPointF
        groups = folding_groups(snapshot.commands)
        hidden = hidden_steps({owner: group for owner, group in groups.items() if not group['locked']})
        scene = self.editor.scene
        scene.locked_groups = {}
        scene.locked_source_positions = {node.node_id: QPointF(node.x, node.y) for node in snapshot.nodes}
        visited = set()
        updating = scene._updating_graph
        scene._updating_graph = True
        try:
            for node in scene.nodes_by_id.values():
                node.setPos(scene.locked_source_positions[node.node_id])
                node.setZValue(1.0)
            for command in snapshot.commands:
                if command.id in visited or command.id not in groups or not groups[command.id]['locked']:
                    continue
                members = locked_move_ids(snapshot.commands, [command.id])
                ordered = [scene.nodes_by_command_id[c.id] for c in snapshot.commands
                           if c.id in members and c.id in scene.nodes_by_command_id]
                if not ordered:
                    continue
                anchor = QPointF(ordered[0].pos())
                node_ids = frozenset(node.node_id for node in ordered)
                for index, node in enumerate(ordered):
                    if index == 0:
                        node.setPos(anchor)
                    else:
                        previous = ordered[index - 1]
                        # Overlap only the empty corners, leaving titles and
                        # side/top ports exposed. Notes extend below the card.
                        rise = node.height + (22 if node.note else -8)
                        node.setPos(previous.pos() + QPointF(previous.width - 8, -rise))
                    node.setZValue(10 + (index + 1) / (len(ordered) + 1))
                    scene.locked_groups[node.node_id] = node_ids
                visited.update(members)
        finally:
            scene._updating_graph = updating
        scene.reroute_edges()
        InstructionWorkspace._refresh_fold_visibility(self, snapshot)

    def _refresh_fold_visibility(self, snapshot):
        groups = folding_groups(snapshot.commands)
        hidden = hidden_steps({owner: group for owner, group in groups.items() if not group['locked']})
        scene = self.editor.scene
        scene.step_groups = groups
        for node in scene.nodes_by_id.values():
            node.setVisible(node.command_id not in hidden)
            if node.command_id in groups:
                group = groups[node.command_id]
                node.title = group_title(group)
                node.step_collapsed = group['collapsed']
                node.subtitle = '已加锁 · 拖动整组 / 右键解锁' if group['locked'] else '右键折叠 / 展开；双击设置'
                description = ('连线步骤自动分组；嵌套线程跟随父线程运行。' if node.type_id == '多线程启动'
                               else '按表格序号折叠，仅影响显示，不影响运行。')
                node.setToolTip(node.title + '\n' + description + '\n右键折叠 / 展开；双击设置')
                node.update()
        for edge in scene.edges:
            internal = edge.target_node.node_id in scene.locked_groups.get(edge.source_node.node_id, ())
            edge.setVisible(not internal and edge.source_node.isVisible() and edge.target_node.isVisible())
        scene.update()

    @visual_only
    def expand_step_for_drag(self, command_id):
        """Persist only the display state; keep the live drag item and camera intact."""
        if not application_state(self.parent_window).can_edit_project():
            return False
        command = self.repository.get_command(int(command_id))
        if command is None or command.type_id not in ('折叠步骤', '多线程启动'):
            return False
        if not command.parameters.get('已折叠', True):
            return False
        self.repository.set_step_collapsed(command.id, False)
        self._refresh_fold_visibility(self.repository.snapshot())
        view = getattr(self.parent_window, 'view_workspace', None)
        if view is not None:
            view.refresh_table()
        return True

    @visual_only
    def expand_drop_targets(self, ids):
        # Expansion is a display operation, independent of animation eligibility.
        groups = folding_groups(self.repository.list_commands())
        selected = set(ids)
        for owner, group in groups.items():
            if owner not in selected and selected & group['members'] and group['collapsed']:
                if self.expand_step_for_drag(owner):
                    self._show_expanded_group({owner} | group['members'])

    @visual_only
    def _show_expanded_group(self, ids):
        self.editor.view.pulse_group(ids)
        table = getattr(getattr(self.parent_window, 'view_workspace', None), 'command_table', None)
        if table is not None:
            table._pulse_group(ids)

    @visual_only
    def edit_feedback(self, kind, ids, marker=None):
        self.editor.view.show_edit_feedback(kind, ids)
        table = getattr(getattr(self.parent_window, 'view_workspace', None), 'command_table', None)
        if table is not None:
            table.show_edit_feedback(kind, ids, marker)

    @visual_only
    def capture_removal_feedback(self, ids):
        views = [self.editor.view]
        table = getattr(getattr(self.parent_window, 'view_workspace', None), 'command_table', None)
        if table is not None:
            views.append(table)
        return [(view, view.feedback.capture(view.feedback_rects(ids), len(ids))) for view in views
                if view.feedback.allowed(len(ids), preview=True)]

    @visual_only
    def removal_feedback(self, captured, count):
        for view, snapshots in captured or ():
            view.feedback.play('delete', snapshots=snapshots, count=count, committed=True)

    def set_thread_nested(self, command_id, enabled):
        try:
            self._check_parameter_save_allowed()
            self.repository.set_thread_nested(command_id, enabled)
            self.reload_graph(command_id)
            self.graphFinalized.emit(False)
            self.statusMessage.emit('已打开嵌套多线程' if enabled else '已取消嵌套多线程，与上方线程并列运行')
        except Exception as error:
            self._show_error('修改多线程嵌套失败', error)

    def toggle_step_fold(self, command_id):
        try:
            self._check_parameter_save_allowed()
            command = self.repository.get_command(int(command_id))
            if command is None or command.type_id not in ('折叠步骤', '多线程启动'):
                return
            self.repository.set_step_collapsed(command.id, not command.parameters.get('已折叠', True))
            self.reload_graph(command.id)
            self.graphFinalized.emit(False)
        except Exception as error:
            self._show_error('折叠步骤失败', error)

    def set_step_locks(self, command_ids, locked):
        from anclicker.domain.step_folding import folding_groups, locked_move_ids
        try:
            self._check_parameter_save_allowed()
            commands = self.repository.list_commands()
            groups = folding_groups(commands)
            selected = set(command_ids) & {c.id for c in commands}
            if not selected:
                return
            owners = set(groups) & selected
            if not locked:
                owners = {owner for owner, group in groups.items()
                          if group['locked'] and selected & ({owner} | group['members'])}
            elif not owners or not selected <= set().union(*({owner} | groups[owner]['members'] for owner in owners)):
                selected = locked_move_ids(commands, selected)
                before = next(c.id for c in commands if c.id in selected)
                positions = [str(index + 2) for index, c in enumerate(commands) if c.id in selected]
                draft = InstructionDraft('折叠步骤', {'整体锁定': True, '已折叠': False,
                    '按条数': False, '按范围': True, '动态范围': True, '终止步骤': max(map(int, positions))})
                created = self.repository.insert_table_commands([draft], before_command_id=before)
                self.reload_graph(created[0])
                self.graphFinalized.emit(False)
                return
            if owners:
                self.repository.set_step_locks(owners, locked)
                self.reload_graph()
                self.graphFinalized.emit(False)
        except Exception as error:
            self._show_error('修改分组锁定失败', error)

    def toggle_step_lock(self, command_id):
        try:
            self._check_parameter_save_allowed()
            command = self.repository.get_command(int(command_id))
            if command is None or command.type_id not in ('折叠步骤', '多线程启动'):
                return
            draft = command.to_draft()
            draft.parameters['整体锁定'] = not draft.parameters.get('整体锁定', command.type_id == '多线程启动')
            self.repository.update_command(command.id, draft)
            self.reload_graph(command.id)
            self.graphFinalized.emit(False)
        except Exception as error:
            self._show_error('切换整体移动锁定失败', error)

    def remember_capture(self, path):
        self._recent_capture = store_image_reference(path)
        self.palette.show_recent_capture(self._recent_capture)

    def quick_capture(self):
        if not self._connection_edit_allowed():
            return
        SmartCaptureDialog, capture_path = _module_imports.load('SmartCaptureDialog_capture_path')
        IMAGES_FOLDER = _module_imports.load('IMAGES_FOLDER')
        owner = self.parent_window
        visible = owner is not None and owner.isVisible()
        if visible:
            owner.hide()
        def choose():
            dialog = None
            try:
                dialog = SmartCaptureDialog()
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    path = capture_path(IMAGES_FOLDER)
                    dialog.save_selection(path)
                    self.remember_capture(str(path))
                    self.statusMessage.emit('截图已准备：拖入“点击快捷截图”或“图像点击”，自动组合为一个图像点击指令。')
            except Exception as error:
                self._show_error('快捷截图失败', error)
            finally:
                if dialog is not None:
                    dialog.deleteLater()
                if visible:
                    owner.show()
                    owner.activateWindow()
        QTimer.singleShot(180, choose)

    def quick_ocr_capture(self):
        if not self._connection_edit_allowed():
            return
        SmartCaptureDialog = _module_imports.load('SmartCaptureDialog')
        QInputDialog = _module_imports.load('QInputDialog')
        InstructionDraft = _module_imports.load('InstructionDraft')
        owner = self.parent_window
        visible = owner is not None and owner.isVisible()
        if visible:
            owner.hide()
        def choose():
            dialog = None
            region = None
            try:
                dialog = SmartCaptureDialog()
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    region = dialog.selected_region()
            except Exception as error:
                self._show_error('快捷OCR框选失败', error)
            finally:
                if dialog is not None:
                    dialog.deleteLater()
                if visible:
                    owner.show()
                    owner.activateWindow()
            if region is None or not self._connection_edit_allowed():
                return
            self._recent_ocr_region = tuple(region)
            self.palette.show_recent_ocr(region)
            self.statusMessage.emit('框选已完成：在快捷截图（OCR）下方选择下一步操作。')
        QTimer.singleShot(180, choose)

    def add_selected_instruction(self) -> None:
        type_id_ = self.palette.selected_type_id()
        if type_id_ is None:
            QMessageBox.information(
                self.parent_window,
                "提示",
                "请先在左侧选择一条指令。",
                QMessageBox.StandardButton.Ok,
            )
            return
        self.add_command(type_id_)

    def add_palette_command(self, type_id, x=None, y=None, *, before_command_id=None):
        """Use identical insertion and follow-up guidance for double-click and drag/drop."""
        if type_id == '打开网页':
            CATALOG = _module_imports.load('CATALOG')
            defaults = {p['key']: p.get('default', '') for p in CATALOG['openUrl']['params']}
            defaults.update(self.palette.quick_parameters(type_id) or {})
            return self.add_command(type_id, x=x, y=y, initial_draft=InstructionDraft(type_id, defaults), configure=False, before_command_id=before_command_id)
        return self.add_command(type_id, x=x, y=y, before_command_id=before_command_id)

    def _run_parameter_editor(self, editor, callback, key):
        docking = getattr(getattr(self.parent_window, 'view_workspace', None), 'docking', None)
        if docking is not None and isinstance(editor, QDialog):
            ParameterPinFilter, PIN_RESULT = _module_imports.load('ParameterPinFilter_PIN_RESULT')
            editor._pin_filter = ParameterPinFilter(editor)
            AdaptivePanelSizer = _module_imports.load('AdaptivePanelSizer')
            editor.setMinimumSize(260, 180)
            editor._panel_scaler = AdaptivePanelSizer(editor, editor, 600, reference_height=420, base_pixels=13)
            docking.pin_editor(editor, callback, key, floating=True)
            return None
        else:
            result = editor.exec()
        if result == QDialog.DialogCode.Accepted:
            return callback(editor.get_draft())
        return None

    def _check_parameter_save_allowed(self):
        window = self.parent_window
        thread = getattr(window, 'command_thread', None)
        view = getattr(window, 'view_workspace', None)
        if not application_state(window).can_edit_project():
            raise RuntimeError('请先停止运行、录制或指令测试，再保存参数。')

    def add_command(self, type_id, x=None, y=None, *, initial_draft=None, configure=True, before_command_id=None):
        table = getattr(getattr(self.parent_window, 'view_workspace', None), 'command_table', None)
        marker = table.take_drop_feedback() if table is not None and before_command_id is not None else None
        unlocked = (feedback_call(table, 'take_drop_unlocks') or set()) if before_command_id is not None else set()
        member_targets = feedback_call(table, 'take_drop_member_targets') if before_command_id is not None else None
        try:
            spec_ = get_instruction_spec(str(type_id))
            if str(type_id) == "绑定选择窗口" or spec_.category == "窗口键鼠":
                start_preload = _module_imports.load('start_preload')
                start_preload()
            if initial_draft is None:
                quick = self.palette.quick_parameters(str(type_id))
                if quick is not None: initial_draft = InstructionDraft(str(type_id), quick)
            def commit(draft):
                self._check_parameter_save_allowed()
                if before_command_id is None:
                    command = self.repository.add_command(draft, x=x, y=y, unconnected=True)
                else:
                    ids = self.repository.insert_table_commands([draft], before_command_id=before_command_id,
                        **({'temporary_unlocks': unlocked} if unlocked else {}),
                        **({'member_targets': member_targets} if member_targets is not None else {}))
                    command = self.repository.get_command(ids[0])
                if before_command_id is None and x is not None and y is not None:
                    self.reload_graph(command.id, positioned_ids={command.id})
                else:
                    self.reload_graph(command.id)
                self.graphFinalized.emit(False)
                self.statusMessage.emit(f'已插入指令：{spec_.display_name}' +
                    ('，已按表格高亮位置插入' if before_command_id is not None else '，请在流程图中完成连线'))
                feedback_call(self, 'expand_drop_targets', [command.id])
                feedback_call(self, 'edit_feedback', 'create', [command.id], marker)
                QTimer.singleShot(0, lambda: self.palette.command_added(draft.type_id, draft.parameters))
                return command.id
            if not configure:
                return commit(initial_draft or InstructionDraft(str(type_id)))
            editor = spec_.create_editor(parent=self.parent_window, context=self._editor_context(),
                **({'draft':initial_draft} if initial_draft is not None else {}))
            self._connect_editor_test(editor, spec_)
            return self._run_parameter_editor(editor, commit, 'parameters_new_' + str(id(editor)))
        except Exception as error:
            self._show_error('添加指令失败', error)
            return None

    def edit_command(self, command_id) -> bool:
        try:
            docking = getattr(getattr(self.parent_window, 'view_workspace', None), 'docking', None)
            key = 'parameters_' + str(int(command_id))
            if docking is not None and key in docking.parameters:
                docking.docks[key].show(); docking.docks[key].raise_()
                return False
            command = self.repository.get_command(int(command_id))
            if command is None: raise KeyError(f'指令不存在：{command_id}')
            spec = get_instruction_spec(command.type_id)
            editor = spec.create_editor(parent=self.parent_window, draft=command.to_draft(),
                                        context=self._editor_context(command.id))
            self._connect_editor_test(editor, spec)
            def commit(draft):
                self._check_parameter_save_allowed()
                current = self.repository.get_command(command.id)
                if current is None:
                    raise RuntimeError('原指令已删除，请取消该设置后重新添加指令。')
                if current.type_id == '多线程启动':
                    for key in ('嵌套层级', '已折叠', '整体锁定', '线程分组成员'):
                        if key in current.parameters:
                            draft.parameters[key] = current.parameters[key]
                if current.type_id == '折叠步骤':
                    draft.parameters['整体锁定'] = bool(current.parameters.get('整体锁定', False))
                self.repository.update_command(command.id, draft)
                self.reload_graph(command.id)
                try: self.repository.validate_graph()
                except Exception: self.graphFinalized.emit(False)
                else: self.graphFinalized.emit(True)
                self.statusMessage.emit(f'已修改指令：{spec.display_name}')
                return True
            return bool(self._run_parameter_editor(editor, commit, key))
        except Exception as error:
            self._show_error('修改指令失败', error)
            return False

    def copy_commands(self, command_ids=None) -> list[int]:
        command_ids_ = command_ids or self.selected_command_ids()
        copied_ids_: list[int] = []
        try:
            from anclicker.domain.step_folding import copy_group_drafts
            drafts = copy_group_drafts(self.repository.list_commands(), command_ids_, self.repository.snapshot())
            copied_ids_ = self.repository.append_recording(drafts, connect=False)
            self.reload_graph(copied_ids_[-1] if copied_ids_ else None)
            if copied_ids_:
                self.editor.view.register_copied_group(copied_ids_)
                self.graphFinalized.emit(False)
                self.statusMessage.emit(f"已复制 {len(copied_ids_)} 条指令")
                feedback_call(self, 'expand_drop_targets', copied_ids_)
                feedback_call(self, 'edit_feedback', 'copy', copied_ids_)
        except Exception as error_:
            self._show_error("复制指令失败", error_)
        return copied_ids_

    def cut_commands(self, command_ids=None):
        try:
            self._check_parameter_save_allowed()
            commands = self.repository.list_commands()
            ids = locked_move_ids(commands, command_ids or self.selected_command_ids())
            drafts = copy_group_drafts(commands, ids, self.repository.snapshot())
            if not drafts:
                return 0
            mime = QMimeData()
            mime.setData('application/x-anclicker-commands', json.dumps([asdict(c) for c in drafts], ensure_ascii=False).encode('utf-8'))
            mime.setText('\n'.join(c.type_id for c in drafts))
            set_command_mime(mime)
            deleted = self.remove_commands(ids, confirm=False)
            if deleted:
                self.statusMessage.emit(f'已剪切 {deleted} 条指令，可在表格中粘贴')
            return deleted
        except Exception as error:
            self._show_error('剪切指令失败', error)
            return 0

    def dissolve_thread(self, command_id, *, confirm=True):
        try:
            self._check_parameter_save_allowed()
            command = self.repository.get_command(int(command_id))
            if command is None or command.type_id != '多线程启动':
                return False
            if confirm and QMessageBox.question(self.parent_window, '解散线程(保留步骤)',
                    '仅移除该多线程启动指令，保留步骤和步骤之间的连线。嵌套子线程提升一级。入口需按需要重新连线。',
                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel) != QMessageBox.Ok:
                return False
            captured = feedback_call(self, 'capture_removal_feedback', [command.id])
            self.repository.dissolve_thread(command.id)
            self.reload_graph()
            self.graphFinalized.emit(False)
            feedback_call(self, 'removal_feedback', captured, 1)
            self.statusMessage.emit('已解散线程并保留步骤，请按需要重新连接入口')
            return True
        except Exception as error:
            self._show_error('解散线程失败', error)
            return False

    def remove_commands(self, command_ids=None, *, confirm: bool = True) -> int:
        command_ids_ = command_ids or self.selected_command_ids()
        if not command_ids_:
            return 0
        from anclicker.domain.step_folding import folding_groups, locked_move_ids
        commands = self.repository.list_commands()
        groups = folding_groups(commands)
        selected = set(map(int, command_ids_))
        # Deleting a locked header includes its descendants, without pulling
        # in an enclosing group unless the user explicitly chooses whole-group.
        changed = True
        while changed:
            before = set(selected)
            for owner, group in groups.items():
                if group['locked'] and owner in selected:
                    selected.update(group['members'])
            changed = before != selected
        member_only = any(group['locked'] and owner not in selected
                          and selected & group['members'] for owner, group in groups.items())
        if confirm and member_only:
            dialog = QMessageBox(self.parent_window)
            dialog.setWindowTitle('删除锁定组内指令')
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText('所选指令属于锁定组，请选择删除方式。')
            single = dialog.addButton('单行删除', QMessageBox.AcceptRole)
            whole = dialog.addButton('整体删除', QMessageBox.DestructiveRole)
            cancel = dialog.addButton('取消', QMessageBox.RejectRole)
            dialog.setDefaultButton(single)
            dialog.setEscapeButton(cancel)
            single.setFocus()
            dialog.exec()
            clicked = dialog.clickedButton()
            if clicked is whole:
                selected = locked_move_ids(commands, selected)
            elif clicked is not single:
                return 0
        command_ids_ = [c.id for c in commands if c.id in selected]
        if confirm and not member_only:
            dialog = QMessageBox(self.parent_window)
            dialog.setWindowTitle('删除指令')
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText(f'确认删除选中的 {len(command_ids_)} 条指令吗？')
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            confirm_button = dialog.button(QMessageBox.StandardButton.Ok)
            confirm_button.setText('确认')
            dialog.button(QMessageBox.StandardButton.Cancel).setText('取消')
            dialog.setDefaultButton(QMessageBox.StandardButton.Ok)
            dialog.setEscapeButton(QMessageBox.StandardButton.Cancel)
            confirm_button.setFocus()
            if dialog.exec() != QMessageBox.StandardButton.Ok:
                return 0
        captured = feedback_call(self, 'capture_removal_feedback', command_ids_)
        try:
            deleted_ = self.repository.delete_commands(
                command_ids_, preserve_flow=self.repository.is_plain_chain()
            )
            self.reload_graph()
            try:
                self.repository.validate_graph()
            except Exception:
                self.graphFinalized.emit(False)
            else:
                self.graphFinalized.emit(True)
            self.statusMessage.emit(f"已删除 {deleted_} 条指令")
            feedback_call(self, 'removal_feedback', captured, deleted_)
            return deleted_
        except Exception as error_:
            self._show_error("删除指令失败", error_)
            return 0

    def clear(self, *, confirm: bool = True) -> bool:
        if confirm and QMessageBox.question(
            self.parent_window,
            "清空画布",
            "确认清除全部指令吗？画布将只保留“开始→结束”。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return False
        try:
            self.repository.clear()
            self.reload_graph()
            self.graphFinalized.emit(True)
            self.statusMessage.emit("已清空全部指令")
            return True
        except Exception as error_:
            self._show_error("清空画布失败", error_)
            return False

    def run_from_command_single(self, command_id) -> None:
        self.runSingleRequested.emit(int(command_id))

    def run_from_command(self, command_id=None) -> None:
        command_id_ = command_id
        if command_id_ is None:
            selected_ = self.selected_command_ids()
            command_id_ = selected_[0] if selected_ else None
        if command_id_ is not None:
            self.runFromRequested.emit(int(command_id_))

    def _commit_graph_change(
        self, command_ids, node_id, x: float, y: float
    ) -> None:
        try:
            focused_ = self.selected_command_ids()
            self.repository.reorder_chain_and_save_positions(
                [int(item_) for item_ in command_ids],
                {str(node_id): (float(x), float(y))},
            )
            self.reload_graph(focused_[0] if focused_ else None)
            self.graphFinalized.emit(True)
            self.statusMessage.emit("已保存节点位置和顺序")
            node = self.editor.scene.nodes_by_id.get(str(node_id))
            if node is not None:
                feedback_call(self, 'expand_drop_targets', [node.command_id])
                feedback_call(self, 'edit_feedback', 'move', [node.command_id])
        except Exception as error_:
            self.reload_graph()
            self._show_error("保存节点位置和顺序失败", error_)

    def _commit_positions(self, positions) -> None:
        try:
            self.repository.save_node_positions(positions)
            feedback_call(self, 'edit_feedback', 'move', [node.command_id for key in positions
                if (node := self.editor.scene.nodes_by_id.get(str(key))) is not None])
        except Exception as error_:
            self.reload_graph()
            self._show_error("保存整组节点位置失败", error_)

    def _commit_position(self, node_id, x: float, y: float) -> None:
        try:
            self.repository.save_node_position(str(node_id), float(x), float(y))
            node = self.editor.scene.nodes_by_id.get(str(node_id))
            if node is not None:
                feedback_call(self, 'edit_feedback', 'move', [node.command_id])
        except Exception as error_:
            self.reload_graph()
            self._show_error("保存节点位置失败", error_)

    def _commit_size(self, node_id, width: float, height: float) -> None:
        try:
            self.repository.save_node_size(
                str(node_id), float(width), float(height)
            )
        except Exception as error_:
            self.reload_graph()
            self._show_error("保存节点大小失败", error_)

    @staticmethod
    def _connection_state(snapshot):
        return (tuple(sorted((n.node_id, n.command_id, n.type_id) for n in snapshot.nodes)),
                tuple(c.id for c in snapshot.commands), tuple(snapshot.edges))

    def _connection_edit_allowed(self):
        thread = getattr(self.parent_window, 'command_thread', None)
        recording = getattr(getattr(self.parent_window, 'view_workspace', None), 'recording_page', None)
        if (thread is not None and thread.isRunning()) or (recording is not None and recording.busy):
            self.statusMessage.emit('请先停止运行或录制，再修改连线')
            return False
        return True

    def clear_connection_history(self):
        """A project import is a history boundary even if its graph is identical."""
        self._connection_history.clear()
        self._connection_redo.clear()
        self._connection_expected = self._connection_state(self.repository.snapshot())

    def _remember_connections(self, before):
        after = self._connection_state(self.repository.snapshot())
        if self._connection_expected != before:
            self._connection_history.clear()
            self._connection_redo.clear()
        if before != after:
            self._connection_redo.clear()
            self._connection_history.append(before)
            self._connection_history = self._connection_history[-20:]
        self._connection_expected = after

    def _delete_edge(self, source, target):
        self._delete_edges([(source, target)])

    def _delete_edges(self, pairs):
        if not self._connection_edit_allowed():
            return
        before = self._connection_state(self.repository.snapshot())
        try:
            targets = {(str(source), str(target)) for source, target in pairs}
            remaining = tuple(edge for edge in before[2] if (edge.source, edge.target) not in targets)
            count = len(before[2]) - len(remaining)
            if count:
                self.repository.restore_connections(remaining, before[1])
            self._remember_connections(before)
            self.reload_graph()
            self.graphFinalized.emit(False)
            self.statusMessage.emit(f'已删除 {count} 根连线，可右键撤销')
        except Exception as error:
            self._show_error('删除连线失败', error)

    def undo_connections(self):
        if not self._connection_edit_allowed():
            return
        current = self._connection_state(self.repository.snapshot())
        if current != self._connection_expected:
            self._connection_history.clear()
            self._connection_redo.clear()
            self._connection_expected = current
        if not self._connection_history:
            self.statusMessage.emit('没有可撤销的连线操作')
            return
        previous = self._connection_history[-1]
        try:
            self.repository.restore_connections(previous[2], previous[1])
            self._connection_history.pop()
            self._connection_redo.append(current)
            self._connection_redo = self._connection_redo[-20:]
            self._connection_expected = previous
            self.reload_graph()
            self.graphFinalized.emit(False)
            self.statusMessage.emit(f'已撤销连线操作，剩余 {len(self._connection_history)} 步')
        except Exception as error:
            self._show_error('撤销连线失败', error)

    def redo_connections(self):
        if not self._connection_edit_allowed():
            return
        current = self._connection_state(self.repository.snapshot())
        if current != self._connection_expected:
            self._connection_history.clear()
            self._connection_redo.clear()
            self._connection_expected = current
        if not self._connection_redo:
            self.statusMessage.emit('没有可回退（重做）的连线操作')
            return
        following = self._connection_redo[-1]
        try:
            self.repository.restore_connections(following[2], following[1])
            self._connection_redo.pop()
            self._connection_history.append(current)
            self._connection_history = self._connection_history[-20:]
            self._connection_expected = following
            self.reload_graph()
            self.graphFinalized.emit(False)
            self.statusMessage.emit(f'已重做连线操作，剩余 {len(self._connection_redo)} 步')
        except Exception as error:
            self._show_error('重做连线失败', error)

    def _add_error_node(self, source_id, x: float, y: float) -> None:
        if not self._connection_edit_allowed():
            return
        try:
            self._check_parameter_save_allowed()
            source_id = str(source_id)
            snapshot = self.repository.snapshot()
            if any(edge.source == source_id and edge.kind == 5 for edge in snapshot.edges):
                self.statusMessage.emit('此指令已连接报错模块，请先删除原报错连线。')
                return
            if not any(node.node_id == source_id and node.command_id is not None
                       and node.type_id != '报错跳转' for node in snapshot.nodes):
                return
            box = QMessageBox(self.parent_window)
            box.setIcon(QMessageBox.Question)
            box.setWindowTitle('添加报错模块')
            box.setText('是否在此处添加报错模块，并连接当前指令的报错线？')
            box.setInformativeText('回车确认添加，Esc 取消。添加后可连接跳转目标，或双击模块设置。')
            add = box.addButton('添加报错模块', QMessageBox.AcceptRole)
            cancel = box.addButton('取消', QMessageBox.RejectRole)
            box.setDefaultButton(add)
            box.setEscapeButton(cancel)
            try:
                box.exec()
                confirmed = box.clickedButton() is add
            finally:
                box.deleteLater()
            if not confirmed:
                return
            self._check_parameter_save_allowed()
            view = self.editor.view
            transform = view.transform()
            center = view.mapToScene(view.viewport().rect().center())
            command = self.repository.add_error_handler(source_id, x, y)
            self.reload_graph(command.id)
            view.setTransform(transform)
            view._zoom = transform.m11()
            view.centerOn(center)
            view.zoomChanged.emit(view._zoom * 100)
            self.graphFinalized.emit(False)
            self.statusMessage.emit('已添加并连接报错模块，请连接跳转目标或双击设置。')
        except Exception as error:
            self._show_error('添加报错模块失败', error)

    def _connect_nodes(self, source_id, target_id, kind=None) -> None:
        if not self._connection_edit_allowed():
            return
        before = self._connection_state(self.repository.snapshot())
        try:
            complete_ = self.repository.connect_nodes(str(source_id), str(target_id), kind)
            self._remember_connections(before)
            self.reload_graph()
            self.graphFinalized.emit(complete_)
            target = self.editor.scene.nodes_by_id.get(str(target_id))
            if target is not None:
                feedback_call(self, 'expand_drop_targets', [target.command_id])
                feedback_call(self, 'edit_feedback', 'link', [target.command_id])
            self.statusMessage.emit(
                "流程已完整，表格与多功能内容已生成"
                if complete_ else "流程连接已保存，请继续连接未接入的指令"
            )
        except Exception as error_:
            self.reload_graph()
            self._show_error("连接流程失败", error_)

    def _delete_connections(self, node_id, mode: str) -> None:
        if not self._connection_edit_allowed():
            return
        before = self._connection_state(self.repository.snapshot())
        try:
            deleted_ = self.repository.delete_node_connections(str(node_id), mode)
            self._remember_connections(before)
            self.reload_graph()
            self.graphFinalized.emit(False)
            self.statusMessage.emit(f"已删除 {deleted_} 条流程连接线")
        except Exception as error_:
            self.reload_graph()
            self._show_error("删除流程连接线失败", error_)

    def _update_note(self, command_id, note: str) -> None:
        try:
            self.repository.update_command_note(int(command_id), str(note))
            self.reload_graph(int(command_id))
            try:
                self.repository.validate_graph()
            except Exception:
                self.graphFinalized.emit(False)
            else:
                self.graphFinalized.emit(True)
            self.statusMessage.emit("节点备注已保存")
        except Exception as error_:
            self._show_error("保存节点备注失败", error_)

    @property
    def _template_directory(self) -> Path:
        directory_ = Path(self.repository.db_path).resolve().parent / "templates"
        directory_.mkdir(parents=True, exist_ok=True)
        return directory_

    @staticmethod
    def _safe_template_name(name_: str) -> str:
        cleaned_ = "".join(
            "_" if character_ in '<>:"/\\|?*' else character_
            for character_ in str(name_).strip()
        ).rstrip(". ")
        if not cleaned_:
            raise ValueError("模板名称不能为空")
        return cleaned_

    def _template_names(self):
        return tuple(path_.stem for path_ in sorted(self._template_directory.glob("*.json")))

    def _manage_templates(self) -> None:
        names_ = self._template_names()
        if not names_:
            QMessageBox.information(self.parent_window, "模板管理", "当前没有已保存的流程模板。")
            return
        name_, accepted_ = QInputDialog.getItem(
            self.parent_window, "模板管理", "选择要删除的模板：", names_, 0, False
        )
        if not accepted_ or not name_:
            return
        answer_ = QMessageBox.question(
            self.parent_window,
            "删除模板",
            f"确定删除流程模板“{name_}”吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer_ == QMessageBox.StandardButton.Yes:
            path_ = self._template_directory / f"{self._safe_template_name(name_)}.json"
            path_.unlink(missing_ok=True)
            self.statusMessage.emit(f"已删除流程模板：{name_}")

    def _save_template(self, command_ids, name: str) -> None:
        try:
            selected_ = {int(command_id_) for command_id_ in command_ids}
            snapshot_ = self.repository.snapshot()
            commands_ = [command_ for command_ in snapshot_.commands if command_.id in selected_]
            nodes_ = {
                int(node_.command_id): node_ for node_ in snapshot_.nodes
                if node_.command_id is not None and int(node_.command_id) in selected_
            }
            if not commands_:
                raise ValueError("请先选择至少一个指令节点")
            min_x_ = min(nodes_[int(command_.id)].x for command_ in commands_)
            min_y_ = min(nodes_[int(command_.id)].y for command_ in commands_)
            local_id_ = {int(command_.id): index_ + 1 for index_, command_ in enumerate(commands_)}
            command_by_node_ = {node_.node_id: int(node_.command_id) for node_ in nodes_.values()}
            payload_ = {
                "version": 1,
                "nodes": [
                    {
                        "id": local_id_[int(command_.id)],
                        "type_id": command_.type_id,
                        "parameters": command_.parameters,
                        "repeat_count": command_.repeat_count,
                        "error_policy": command_.error_policy,
                        "note": command_.note,
                        "x": nodes_[int(command_.id)].x - min_x_,
                        "y": nodes_[int(command_.id)].y - min_y_,
                        "width": nodes_[int(command_.id)].width,
                        "height": nodes_[int(command_.id)].height,
                    }
                    for command_ in commands_
                ],
                "edges": [
                    [local_id_[command_by_node_[edge_.source]], local_id_[command_by_node_[edge_.target]], edge_.kind]
                    for edge_ in snapshot_.edges
                    if edge_.source in command_by_node_ and edge_.target in command_by_node_
                ],
            }
            path_ = self._template_directory / f"{self._safe_template_name(name)}.json"
            path_.write_text(json.dumps(payload_, ensure_ascii=False, indent=2), encoding="utf-8")
            self.statusMessage.emit(f"模板已保存：{path_.stem}")
        except Exception as error_:
            self._show_error("保存流程模板失败", error_)

    def _insert_template(self, name: str, x: float, y: float) -> None:
        try:
            path_ = self._template_directory / f"{self._safe_template_name(name)}.json"
            payload_ = json.loads(path_.read_text(encoding="utf-8"))
            records_ = list(payload_.get("nodes", ()))
            command_by_local_: dict[int, int] = {}
            for record_ in records_:
                command_ = self.repository.add_command(
                    {
                        "type_id": record_["type_id"],
                        "parameters": record_.get("parameters", {}),
                        "repeat_count": int(record_.get("repeat_count", 1)),
                        "error_policy": record_.get("error_policy", "提示异常并暂停"),
                        "note": record_.get("note", ""),
                    },
                    x=float(x) + float(record_.get("x", 0)),
                    y=float(y) + float(record_.get("y", 0)),
                    unconnected=True,
                )
                command_by_local_[int(record_["id"])] = int(command_.id)
            snapshot_ = self.repository.snapshot()
            node_by_command_ = {
                int(node_.command_id): node_.node_id for node_ in snapshot_.nodes
                if node_.command_id is not None
            }
            for edge_record_ in payload_.get("edges", ()):
                source_local_, target_local_ = edge_record_[:2]
                kind_ = int(edge_record_[2]) if len(edge_record_) > 2 else None
                self.repository.connect_nodes(
                    node_by_command_[command_by_local_[int(source_local_)]],
                    node_by_command_[command_by_local_[int(target_local_)]],
                    kind_,
                )
            for record_ in records_:
                if record_.get("width") and record_.get("height"):
                    self.repository.save_node_size(
                        node_by_command_[command_by_local_[int(record_["id"])]],
                        float(record_["width"]), float(record_["height"]),
                    )
            self.reload_graph()
            self.graphFinalized.emit(False)
            self.statusMessage.emit(f"已插入流程模板：{name}")
        except Exception as error_:
            self._show_error("插入流程模板失败", error_)

    def _nearest_edge(self, x: float, y: float):
        snapshot_ = self.repository.snapshot()
        nodes_ = {node_.node_id: node_ for node_ in snapshot_.nodes}
        nearest_ = None
        nearest_distance_ = math.inf
        for edge_ in snapshot_.edges:
            source_ = nodes_[edge_.source]
            target_ = nodes_[edge_.target]
            distance_ = self._point_segment_distance(
                float(x), float(y), source_.x, source_.y, target_.x, target_.y
            )
            if distance_ < nearest_distance_:
                nearest_, nearest_distance_ = edge_, distance_
        return nearest_ if nearest_distance_ <= self.EDGE_HIT_DISTANCE else None

    @staticmethod
    def _point_segment_distance(px_, py_, ax_, ay_, bx_, by_) -> float:
        dx_, dy_ = bx_ - ax_, by_ - ay_
        length_squared_ = dx_ * dx_ + dy_ * dy_
        if length_squared_ == 0:
            return math.hypot(px_ - ax_, py_ - ay_)
        ratio_ = max(
            0.0,
            min(1.0, ((px_ - ax_) * dx_ + (py_ - ay_) * dy_) / length_squared_),
        )
        return math.hypot(px_ - (ax_ + ratio_ * dx_), py_ - (ay_ + ratio_ * dy_))

    def _previous_web_command(self, command_id=None):
        snapshot = self.repository.snapshot()
        commands = {command.id: command for command in snapshot.commands}
        nodes = {node.node_id: node for node in snapshot.nodes}
        current = next((node for node in snapshot.nodes if node.command_id == command_id), None) if command_id is not None else None
        incoming = {}
        for edge in snapshot.edges:
            incoming.setdefault(edge.target, []).append(edge.source)
        if current is not None and incoming.get(current.node_id):
            visited = {current.node_id}
            frontier = incoming[current.node_id]
            while frontier:
                layer = [node_id for node_id in dict.fromkeys(frontier) if node_id not in visited]
                visited.update(layer)
                matches = [commands[nodes[node_id].command_id] for node_id in layer
                           if node_id in nodes and nodes[node_id].command_id in commands
                           and commands[nodes[node_id].command_id].type_id == '打开网页']
                if len(matches) > 1:
                    raise ValueError('上方多个分支都有打开网页，请明确连接到要定位的网页流程后再拾取元素。')
                if matches: return dict(matches[0].parameters)
                frontier = [parent for node_id in layer for parent in incoming.get(node_id, [])]
        else:
            previous = []
            for command in sorted(snapshot.commands, key=lambda item: item.order):
                if command.id == command_id: break
                if command.type_id == '打开网页': previous.append(command)
            if previous: return dict(previous[-1].parameters)
        raise ValueError('这条指令上方没有“打开网页”。请先添加网页地址，再拾取元素。')

    def _previous_background_binding(self, command_id=None):
        previous_binding = _module_imports.load('previous_binding')
        return previous_binding(self.repository.snapshot(), command_id)

    def _condition_hint(self, command_id=None):
        condition_hint = _module_imports.load('condition_hint')
        return condition_hint(self.repository.snapshot(), command_id)

    def _editor_context(self, command_id=None) -> EditorContext:
        return EditorContext(
            owner=self.parent_window,
            variables=self._load_variables(),
            output=self.statusMessage.emit,
            metadata={"database": getattr(self.parent_window, "db", None),
                      "condition_hint": lambda: self._condition_hint(command_id),
                      "previous_web_command": lambda: self._previous_web_command(command_id),
                      "previous_background_binding": lambda: self._previous_background_binding(command_id),
                      "recent_capture": getattr(self, '_recent_capture', ''),
                      "remember_capture": self.remember_capture},
        )

    def _load_variables(self) -> dict:
        database_ = getattr(self.parent_window, "db", None)
        if database_ is None:
            return {}
        try:
            return dict(database_.get_variable_info("dict"))
        except Exception:
            return {}

    def _connect_editor_test(self, editor_, spec_) -> None:
        signal_ = getattr(editor_, "test_requested", None)
        if signal_ is None:
            return

        def execute_test_(draft_: InstructionDraft) -> None:
            window = getattr(self, 'parent_window', None)
            view = getattr(window, 'view_workspace', None)
            thread = getattr(window, 'command_thread', None)
            if not application_state(window).can_start_execution():
                self.statusMessage.emit('请先结束当前任务、录制、Agent 或指令测试。')
                return
            self._instruction_test_active = True
            try:
                command_ = CommandRecord(
                    id=None,
                    type_id=draft_.type_id,
                    parameters=draft_.parameters,
                    repeat_count=1,
                    error_policy=draft_.error_policy,
                    note=draft_.note,
                    order=0,
                )
                context_ = self._editor_context()
                if isinstance(context_, EditorContext):
                    context_ = context_.for_execution()
                self._instruction_test_context = context_
                if spec_.type_id in {'图像等待', '窗口焦点等待', '时间等待', '按键等待'} or spec_.category in {'窗口键鼠', '键鼠', '本地OCR', 'Excel', '白话指令', '网页自动化', '网页后台操作', '数据抓取', '后台功能'}:
                    run_cancellable_test = _module_imports.load('run_cancellable_test')
                    run_cancellable_test(spec_, command_, context_, editor_)
                    if context_.stop_requested:
                        self.statusMessage.emit(f'{spec_.display_name}测试已取消')
                        return
                else:
                    spec_.create_executor().execute(context_, command_)
                database_ = context_.metadata.get('database')
                if database_ is not None:
                    database_.persist_global_variables(context_.variables)
                self.statusMessage.emit(f"测试完成：{spec_.display_name}")
            except Exception as error_:
                if getattr(getattr(self, "_instruction_test_context", None), "stop_requested", False):
                    self.statusMessage.emit(f"{spec_.display_name}测试已取消")
                else:
                    self._show_error("测试指令失败", error_)
            finally:
                self._instruction_test_active = False
                self._instruction_test_context = None

        signal_.connect(execute_test_)

    def _show_error(self, title_: str, error_: Exception) -> None:
        self.statusMessage.emit(f"{title_}：{error_}")
        QMessageBox.warning(
            self.parent_window,
            title_,
            str(error_),
            QMessageBox.StandardButton.Ok,
        )
