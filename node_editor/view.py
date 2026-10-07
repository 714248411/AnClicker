"""Graphics view with zoom, panning, palette drops and host-owned actions."""

from __future__ import annotations

from qt_compat.QtCore import QPoint, Signal, Qt
from qt_compat.QtGui import QKeySequence, QPainter
from qt_compat.QtWidgets import QGraphicsView, QInputDialog, QMenu

from node_editor.items import NodeItem, EdgeItem
from node_editor.palette import INSTRUCTION_MIME_TYPE
from node_editor.style import MAX_ZOOM, MIN_ZOOM


class NodeView(QGraphicsView):
    zoomChanged = Signal(int)
    instructionDropped = Signal(str, float, float)
    instructionCreateRequested = Signal(str, float, float)
    copyRequested = Signal(object)
    deleteRequested = Signal(object)
    runSingleRequested = Signal(object)
    runFromRequested = Signal(object)
    deleteConnectionsRequested = Signal(object, str)
    deleteEdgeRequested = Signal(object, object)
    deleteEdgesRequested = Signal(object)
    undoConnectionsRequested = Signal()
    redoConnectionsRequested = Signal()
    noteChanged = Signal(object, str)
    saveTemplateRequested = Signal(object, str)
    insertTemplateRequested = Signal(str, float, float)

    def __init__(self, scene_, parent_=None):
        super().__init__(scene_, parent_)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPoint()
        self._pan_moved = False
        self._instruction_types: set[str] = set()
        self._instruction_specs = {}
        self.template_names_provider = lambda: ()
        self.connection_undo_count = lambda: 0
        self.connection_redo_count = lambda: 0
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    def set_instruction_types(self, type_ids_) -> None:
        self._instruction_types = {str(type_id_) for type_id_ in type_ids_}
        self._instruction_specs = dict(type_ids_) if hasattr(type_ids_, "items") else {}

    def wheelEvent(self, event_):
        factor_ = 1.15 if event_.angleDelta().y() > 0 else 1.0 / 1.15
        new_zoom_ = max(MIN_ZOOM, min(self._zoom * factor_, MAX_ZOOM))
        if new_zoom_ != self._zoom:
            self.scale(new_zoom_ / self._zoom, new_zoom_ / self._zoom)
            self._zoom = new_zoom_
            self.zoomChanged.emit(round(self._zoom * 100))
        event_.accept()

    def mousePressEvent(self, event_):
        ctrl_pan_ = (
            event_.button() == Qt.MouseButton.LeftButton
            and bool(event_.modifiers() & Qt.KeyboardModifier.ControlModifier)
            and self.itemAt(event_.position().toPoint()) is None
        )
        if event_.button() == Qt.MouseButton.RightButton or ctrl_pan_:
            self._panning = True
            self._pan_moved = False
            self._pan_start = event_.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event_.accept()
            return
        super().mousePressEvent(event_)

    def mouseMoveEvent(self, event_):
        if self._panning:
            current_position_ = event_.position().toPoint()
            delta_ = current_position_ - self._pan_start
            if delta_.manhattanLength() > 2:
                self._pan_moved = True
            self._pan_start = current_position_
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta_.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta_.y()
            )
            event_.accept()
            return
        super().mouseMoveEvent(event_)

    def mouseReleaseEvent(self, event_):
        if self._panning and event_.button() in {
            Qt.MouseButton.RightButton, Qt.MouseButton.LeftButton
        }:
            self._panning = False
            self.unsetCursor()
            event_.accept()
            return
        super().mouseReleaseEvent(event_)

    def dragEnterEvent(self, event_):
        if self._drop_type(event_) is not None:
            event_.acceptProposedAction()
            return
        super().dragEnterEvent(event_)

    def dragMoveEvent(self, event_):
        if self._drop_type(event_) is not None:
            event_.acceptProposedAction()
            return
        super().dragMoveEvent(event_)

    def dropEvent(self, event_):
        type_id_ = self._drop_type(event_)
        if type_id_ is not None:
            scene_position_ = self.mapToScene(event_.position().toPoint())
            self.instructionDropped.emit(
                type_id_, float(scene_position_.x()), float(scene_position_.y())
            )
            event_.acceptProposedAction()
            return
        super().dropEvent(event_)

    def _drop_type(self, event_) -> str | None:
        if not event_.mimeData().hasFormat(INSTRUCTION_MIME_TYPE):
            return None
        try:
            type_id_ = bytes(
                event_.mimeData().data(INSTRUCTION_MIME_TYPE)
            ).decode("utf-8")
        except UnicodeDecodeError:
            return None
        if self._instruction_types and type_id_ not in self._instruction_types:
            return None
        return type_id_ or None

    def _node_at(self, viewport_position_) -> NodeItem | None:
        item_ = self.itemAt(viewport_position_)
        while item_ is not None and not isinstance(item_, NodeItem):
            item_ = item_.parentItem()
        return item_ if isinstance(item_, NodeItem) else None

    def _add_connection_undo(self, menu):
        count = self.connection_undo_count()
        action = menu.addAction(f'撤销连线操作（剩余 {count} 步，最多 20 步）')
        action.setEnabled(count > 0)
        action.triggered.connect(self.undoConnectionsRequested.emit)
        redo_count = self.connection_redo_count()
        redo = menu.addAction(f'回退连线（重做，剩余 {redo_count} 步）')
        redo.setEnabled(redo_count > 0)
        redo.triggered.connect(self.redoConnectionsRequested.emit)
        return action

    def contextMenuEvent(self, event_):
        if self._pan_moved:
            self._pan_moved = False
            event_.accept()
            return
        node_ = self._node_at(event_.pos())
        edge = self.itemAt(event_.pos())
        selected_edges = [item for item in self.scene().selectedItems() if isinstance(item, EdgeItem)]
        in_edge_selection = False
        if selected_edges:
            bounds = selected_edges[0].sceneBoundingRect()
            for item in selected_edges[1:]:
                bounds = bounds.united(item.sceneBoundingRect())
            in_edge_selection = bounds.contains(self.mapToScene(event_.pos()))
        if node_ is None and (isinstance(edge, EdgeItem) or in_edge_selection):
            if isinstance(edge, EdgeItem) and not edge.isSelected():
                self.scene().clearSelection()
                edge.setSelected(True)
                selected_edges = [edge]
            pairs = [(item.source_node.node_id, item.target_node.node_id) for item in selected_edges]
            menu = QMenu(self)
            delete = menu.addAction('删除此连线' if len(pairs) == 1 else f'删除选中连线（{len(pairs)} 根）')
            self._add_connection_undo(menu)
            chosen = menu.exec(event_.globalPos())
            if chosen == delete:
                if len(pairs) == 1:
                    self.deleteEdgeRequested.emit(*pairs[0])
                else:
                    self.deleteEdgesRequested.emit(pairs)
            menu.deleteLater()
            event_.accept()
            return
        if node_ is None:
            menu_ = QMenu(self)
            self._add_connection_undo(menu_)
            menu_.addSeparator()
            select_all_action_ = menu_.addAction("全选")
            save_template_action_ = menu_.addAction("选中存为模板")
            save_template_action_.setEnabled(bool(self.scene().selected_command_ids()))
            menu_.addSeparator()
            action_types_ = {}
            categories_ = {}
            for type_id_, spec_ in self._instruction_specs.items():
                categories_.setdefault(spec_.category, []).append((type_id_, spec_.title))
            for category_, entries_ in categories_.items():
                category_menu_ = menu_.addMenu(category_)
                for type_id_, title_ in entries_:
                    action_ = category_menu_.addAction(title_)
                    action_types_[action_] = type_id_
            template_actions_ = {}
            template_menu_ = menu_.addMenu("插入模板")
            for name_ in self.template_names_provider() or ():
                action_ = template_menu_.addAction(str(name_))
                template_actions_[action_] = str(name_)
            if not template_actions_:
                template_menu_.addAction("暂无模板").setEnabled(False)
            if not action_types_:
                menu_.addAction("暂无可用指令").setEnabled(False)
            selected_action_ = menu_.exec(event_.globalPos())
            if selected_action_ == select_all_action_:
                for item_ in self.scene().nodes_by_id.values():
                    if not item_.is_terminal:
                        item_.setSelected(True)
                event_.accept()
                return
            if selected_action_ == save_template_action_:
                name_, accepted_ = QInputDialog.getText(self, "模板名称", "名称：", text="我的模板")
                if accepted_ and name_.strip():
                    self.saveTemplateRequested.emit(
                        self.scene().selected_command_ids(), name_.strip()
                    )
                event_.accept()
                return
            template_name_ = template_actions_.get(selected_action_)
            if template_name_ is not None:
                scene_position_ = self.mapToScene(event_.pos())
                self.insertTemplateRequested.emit(
                    template_name_, float(scene_position_.x()), float(scene_position_.y())
                )
                event_.accept()
                return
            type_id_ = action_types_.get(selected_action_)
            if type_id_ is not None:
                scene_position_ = self.mapToScene(event_.pos())
                self.instructionCreateRequested.emit(
                    type_id_, float(scene_position_.x()), float(scene_position_.y())
                )
            event_.accept()
            return
        if node_.is_terminal:
            menu = QMenu(self)
            self._add_connection_undo(menu)
            menu.exec(event_.globalPos())
            menu.deleteLater()
            event_.accept()
            return
        if not node_.isSelected():
            self.scene().clearSelection()
            node_.setSelected(True)
        selected_ids_ = self.scene().selected_command_ids()
        if not selected_ids_:
            return

        menu_ = QMenu(self)
        self._add_connection_undo(menu_)
        menu_.addSeparator()
        configure_action_ = menu_.addAction("配置")
        note_action_ = menu_.addAction("备注")
        save_template_action_ = menu_.addAction("存为模板")
        menu_.addSeparator()
        copy_action_ = menu_.addAction("复制")
        copy_action_.setShortcut(QKeySequence.StandardKey.Copy)
        delete_action_ = menu_.addAction("删除")
        delete_action_.setShortcut(QKeySequence.StandardKey.Delete)
        run_single_action_ = None
        run_from_action_ = None
        if len(selected_ids_) == 1:
            menu_.addSeparator()
            run_single_action_ = menu_.addAction("运行此指令")
            run_from_action_ = menu_.addAction("从此指令运行")
        menu_.addSeparator()
        delete_all_edges_ = menu_.addAction("删除流程连接线")
        delete_incoming_edge_ = menu_.addAction("删除前流程连接线")
        delete_outgoing_edge_ = menu_.addAction("删除后流程连接线")
        for action in (delete_all_edges_, delete_incoming_edge_, delete_outgoing_edge_):
            action.setToolTip('仅作用于当前右键点击的流程方块')
        selected_action_ = menu_.exec(event_.globalPos())
        if selected_action_ is None:
            event_.accept()
            return
        if selected_action_ == configure_action_:
            self.scene().activate_node(node_)
        elif selected_action_ == note_action_:
            note_, accepted_ = QInputDialog.getText(
                self, "备注", "节点备注：", text=node_.note
            )
            if accepted_:
                self.noteChanged.emit(node_.command_id, note_)
        elif selected_action_ == save_template_action_:
            name_, accepted_ = QInputDialog.getText(
                self, "模板名称", "名称：", text=f"{node_.title}模板"
            )
            if accepted_ and name_.strip():
                self.saveTemplateRequested.emit(selected_ids_, name_.strip())
        elif selected_action_ == copy_action_:
            self.copyRequested.emit(selected_ids_)
        elif selected_action_ == delete_action_:
            self.deleteRequested.emit(selected_ids_)
        elif selected_action_ == run_single_action_:
            self.runSingleRequested.emit(selected_ids_[0])
        elif selected_action_ == run_from_action_:
            self.runFromRequested.emit(selected_ids_[0])
        elif selected_action_ == delete_all_edges_:
            self.deleteConnectionsRequested.emit(node_.node_id, "all")
        elif selected_action_ == delete_incoming_edge_:
            self.deleteConnectionsRequested.emit(node_.node_id, "incoming")
        elif selected_action_ == delete_outgoing_edge_:
            self.deleteConnectionsRequested.emit(node_.node_id, "outgoing")
        event_.accept()

    def keyPressEvent(self, event_):
        selected_ids_ = self.scene().selected_command_ids()
        if event_.matches(QKeySequence.StandardKey.SelectAll):
            for item_ in self.scene().nodes_by_id.values():
                if not item_.is_terminal:
                    item_.setSelected(True)
            event_.accept()
            return
        if event_.matches(QKeySequence.StandardKey.Copy) and selected_ids_:
            self.copyRequested.emit(selected_ids_)
            event_.accept()
            return
        if event_.key() == Qt.Key.Key_Delete and selected_ids_:
            self.deleteRequested.emit(selected_ids_)
            event_.accept()
            return
        super().keyPressEvent(event_)

    def fit_graph(self):
        fitted_rect_ = self.scene().graph_items_rect()
        self.fitInView(fitted_rect_, Qt.AspectRatioMode.KeepAspectRatio)
        fitted_zoom_ = self.transform().m11()
        self._zoom = max(MIN_ZOOM, min(fitted_zoom_, MAX_ZOOM))
        if fitted_zoom_ and fitted_zoom_ != self._zoom:
            self.scale(self._zoom / fitted_zoom_, self._zoom / fitted_zoom_)
        self.zoomChanged.emit(round(self._zoom * 100))

    def zoom_in(self):
        self._set_zoom(min(MAX_ZOOM, self._zoom * 1.2))

    def zoom_out(self):
        self._set_zoom(max(MIN_ZOOM, self._zoom / 1.2))

    def _set_zoom(self, zoom_: float):
        zoom_ = max(MIN_ZOOM, min(float(zoom_), MAX_ZOOM))
        if zoom_ == self._zoom:
            return
        self.scale(zoom_ / self._zoom, zoom_ / self._zoom)
        self._zoom = zoom_
        self.zoomChanged.emit(round(self._zoom * 100))
