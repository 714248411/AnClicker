"""Main-window integration for the instruction palette and node canvas."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox

from graph_repository import END_NODE_ID, GraphRepository
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.registry import INSTRUCTION_SPECS, get_instruction_spec
from node_editor import InstructionPalette, NodeEditorWidget


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
        self.repository = GraphRepository(db_path)
        self.palette = InstructionPalette(INSTRUCTION_SPECS, parent_=parent)
        self.editor = NodeEditorWidget(parent_=parent)
        self._connection_history = []
        self._connection_redo = []
        self._connection_expected = None
        self._connect_signals()
        self.reload_graph()

    def _connect_signals(self) -> None:
        self.palette.instructionActivated.connect(self.add_command)
        self.editor.instructionDropped.connect(self.add_command)
        self.editor.instructionCreateRequested.connect(self.add_command)
        self.editor.commandActivated.connect(self.edit_command)
        self.editor.copyRequested.connect(self.copy_commands)
        self.editor.deleteRequested.connect(self.remove_commands)
        self.editor.runSingleRequested.connect(self.run_from_command_single)
        self.editor.runFromRequested.connect(self.run_from_command)
        self.editor.graphCommitted.connect(self._commit_graph_change)
        self.editor.positionCommitted.connect(self._commit_position)
        self.editor.sizeCommitted.connect(self._commit_size)
        self.editor.connectionRequested.connect(self._connect_nodes)
        self.editor.branchConnectionRequested.connect(self._connect_nodes)
        self.editor.deleteConnectionsRequested.connect(self._delete_connections)
        self.editor.noteChanged.connect(self._update_note)
        self.editor.saveTemplateRequested.connect(self._save_template)
        self.editor.insertTemplateRequested.connect(self._insert_template)
        self.editor.manageTemplatesRequested.connect(self._manage_templates)
        self.editor.view.template_names_provider = self._template_names
        self.editor.view.deleteEdgeRequested.connect(self._delete_edge)
        self.editor.view.deleteEdgesRequested.connect(self._delete_edges)
        self.editor.view.can_cut_connections = self._connection_edit_allowed
        self.editor.view.undoConnectionsRequested.connect(self.undo_connections)
        self.editor.view.redoConnectionsRequested.connect(self.redo_connections)
        self.editor.view.connection_undo_count = lambda: len(self._connection_history)
        self.editor.view.connection_redo_count = lambda: len(self._connection_redo)

    # Public node-workspace interface used by the main window.
    def selected_command_ids(self) -> list[int]:
        return [int(command_id_) for command_id_ in self.editor.selected_command_ids()]

    def focus_command(self, command_id: int) -> bool:
        return self.editor.focus_command(int(command_id))

    def reload_graph(self, focus_command_id: Optional[int] = None) -> None:
        snapshot_ = self.repository.snapshot()
        state = self._connection_state(snapshot_)
        if self._connection_expected is not None and state != self._connection_expected:
            self._connection_history.clear()
            self._connection_redo.clear()
        self._connection_expected = state
        self.editor.load_graph(
            snapshot_.nodes, snapshot_.edges, INSTRUCTION_SPECS,
            allow_incomplete=True,
        )
        if focus_command_id is not None:
            self.editor.focus_command(int(focus_command_id))
        else:
            self.editor.view.fit_graph()

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

    def add_command(
        self,
        type_id: str,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> Optional[int]:
        """Open the independent editor and create only after confirmation."""
        try:
            spec_ = get_instruction_spec(str(type_id))
            editor_ = spec_.create_editor(
                parent=self.parent_window,
                context=self._editor_context(),
            )
            self._connect_editor_test(editor_, spec_)
            if editor_.exec() != QDialog.DialogCode.Accepted:
                return None
            draft_ = editor_.get_draft()
            command_ = self.repository.add_command(
                draft_,
                x=x,
                y=y,
                unconnected=True,
            )
            self.reload_graph(command_.id)
            self.graphFinalized.emit(False)
            self.statusMessage.emit(
                f"已插入指令：{spec_.display_name}，请在流程图中完成连线"
            )
            return command_.id
        except Exception as error_:
            self._show_error("添加指令失败", error_)
            return None

    def edit_command(self, command_id) -> bool:
        try:
            command_ = self.repository.get_command(int(command_id))
            if command_ is None:
                raise KeyError(f"指令不存在：{command_id}")
            spec_ = get_instruction_spec(command_.type_id)
            editor_ = spec_.create_editor(
                parent=self.parent_window,
                draft=command_.to_draft(),
                context=self._editor_context(),
            )
            self._connect_editor_test(editor_, spec_)
            if editor_.exec() != QDialog.DialogCode.Accepted:
                return False
            self.repository.update_command(command_.id, editor_.get_draft())
            self.reload_graph(command_.id)
            try:
                self.repository.validate_graph()
            except Exception:
                self.graphFinalized.emit(False)
            else:
                self.graphFinalized.emit(True)
            self.statusMessage.emit(f"已修改指令：{spec_.display_name}")
            return True
        except Exception as error_:
            self._show_error("修改指令失败", error_)
            return False

    def copy_commands(self, command_ids=None) -> list[int]:
        command_ids_ = command_ids or self.selected_command_ids()
        copied_ids_: list[int] = []
        try:
            for command_id_ in command_ids_:
                copied_ = self.repository.duplicate_command(
                    int(command_id_), unconnected=True
                )
                copied_ids_.append(int(copied_.id))
            self.reload_graph(copied_ids_[-1] if copied_ids_ else None)
            if copied_ids_:
                self.graphFinalized.emit(False)
                self.statusMessage.emit(f"已复制 {len(copied_ids_)} 条指令")
        except Exception as error_:
            self._show_error("复制指令失败", error_)
        return copied_ids_

    def remove_commands(self, command_ids=None, *, confirm: bool = True) -> int:
        command_ids_ = command_ids or self.selected_command_ids()
        if not command_ids_:
            return 0
        if confirm and QMessageBox.question(
            self.parent_window,
            "删除指令",
            f"确认删除选中的 {len(command_ids_)} 条指令吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return 0
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
        except Exception as error_:
            self.reload_graph()
            self._show_error("保存节点位置和顺序失败", error_)

    def _commit_position(self, node_id, x: float, y: float) -> None:
        try:
            self.repository.save_node_position(str(node_id), float(x), float(y))
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

    def _connect_nodes(self, source_id, target_id, kind=None) -> None:
        if not self._connection_edit_allowed():
            return
        before = self._connection_state(self.repository.snapshot())
        try:
            complete_ = self.repository.connect_nodes(str(source_id), str(target_id), kind)
            self._remember_connections(before)
            self.reload_graph()
            self.graphFinalized.emit(complete_)
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

    def _editor_context(self) -> ExecutionContext:
        return ExecutionContext(
            variables=self._load_variables(),
            output=self.statusMessage.emit,
            metadata={"database": getattr(self.parent_window, "db", None)},
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
                if spec_.type_id in {'中键激活', '时间等待'}:
                    from instructions.common.test_runner import run_cancellable_test
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
                self._show_error("测试指令失败", error_)

        signal_.connect(execute_test_)

    def _show_error(self, title_: str, error_: Exception) -> None:
        self.statusMessage.emit(f"{title_}：{error_}")
        QMessageBox.warning(
            self.parent_window,
            title_,
            str(error_),
            QMessageBox.StandardButton.Ok,
        )
