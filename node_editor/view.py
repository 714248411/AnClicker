"""Graphics view with zoom, panning, palette drops and host-owned actions."""

from __future__ import annotations

from qt_compat.QtCore import QPoint, QPointF, QRectF, Signal, Qt, QTimer
import math
from qt_compat.QtGui import QContextMenuEvent, QKeySequence, QPainter, QColor, QPen, QPainterPath, QRegion
from time import monotonic
from qt_compat.QtWidgets import QGraphicsView, QInputDialog, QMenu

from node_editor.items import NodeItem, EdgeItem
from node_editor.palette import INSTRUCTION_MIME_TYPE
from node_editor.style import MAX_ZOOM, MIN_ZOOM, NODE_COLOR, EDGE_SELECTED_COLOR
from node_editor.flow_arrows import arrow_segments, moving_arrows, arrow_repaint_region
from node_editor.cutting import ConnectionCutter


class NodeView(QGraphicsView):
    zoomChanged = Signal(float)
    continuousAnimationChanged = Signal(bool)
    arrowsVisibilityChanged = Signal(bool)
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
        self._arrow_cache = {}
        self._arrow_repaint_region = QRegion()
        self._arrow_epoch = monotonic()
        self._arrow_continuous = False
        self._arrows_visible = True
        self._arrow_run_until = 0.0
        self._arrow_frozen_elapsed = 0.0
        self._arrow_timer = QTimer(self)
        self._arrow_timer.setInterval(33)
        self._arrow_timer.timeout.connect(self._advance_flow_arrows)
        # Expire even when the canvas is hidden or has no animated edges.
        self._arrow_preview_timer = QTimer(self)
        self._arrow_preview_timer.setSingleShot(True)
        self._arrow_preview_timer.setTimerType(Qt.PreciseTimer)
        self._arrow_preview_timer.timeout.connect(self._finish_run_preview)
        graph_changed = getattr(scene_, 'graphChanged', None)
        if graph_changed is not None:
            graph_changed.connect(self._sync_flow_arrows)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPoint()
        self._pan_moved = False
        self._pan_button = Qt.MouseButton.NoButton
        self._pan_origin = QPointF()
        self._pan_scroll_origin = QPoint()
        self._instruction_types: set[str] = set()
        self._instruction_specs = {}
        self.template_names_provider = lambda: ()
        self.connection_undo_count = lambda: 0
        self.connection_redo_count = lambda: 0
        self.can_cut_connections = lambda: True
        self.cutter = ConnectionCutter(self)
        self._suppress_context_until = 0.0
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setToolTip("空白处右键拖拽切断连线，松开生效，Esc 取消；右键单击菜单；中键平移；滚轮缩放；左键框选。")
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    @property
    def arrows_visible(self):
        # Expiry affects this run only; never overwrite the saved user choice.
        return self._arrows_visible and (not self._arrow_run_until or self._arrow_animation_active())

    def set_arrows_visible(self, visible):
        visible = bool(visible)
        if visible == self._arrows_visible and (not visible or self.arrows_visible):
            return
        if visible and self._arrow_run_until and not self._arrow_animation_active():
            # A manual reopen after expiry shows static arrows until the next run.
            self._arrow_frozen_elapsed = self._arrow_elapsed()
            self._arrow_run_until = 0.0
            self._arrow_preview_timer.stop()
        self._arrows_visible = visible
        self._sync_flow_arrows()
        self.arrowsVisibilityChanged.emit(visible)

    @property
    def continuous_animation(self):
        return self._arrow_continuous

    def _arrow_elapsed(self, now=None):
        now = monotonic() if now is None else now
        if self._arrow_continuous:
            return max(0.0, now-self._arrow_epoch)
        if self._arrow_run_until:
            return max(0.0, min(now, self._arrow_run_until)-self._arrow_epoch)
        return self._arrow_frozen_elapsed

    def _arrow_animation_active(self, now=None):
        now = monotonic() if now is None else now
        return self._arrow_continuous or now < self._arrow_run_until

    def play_run_animation(self):
        """One five-second preview per run, never per executed instruction."""
        if self._arrow_continuous:
            self._sync_flow_arrows()
            return
        self._arrow_epoch = monotonic()
        self._arrow_frozen_elapsed = 0.0
        self._arrow_run_until = self._arrow_epoch + 5.0
        self._arrow_preview_timer.start(5000)
        self._sync_flow_arrows()

    def set_continuous_animation(self, enabled):
        enabled = bool(enabled)
        if enabled == self._arrow_continuous:
            return
        now = monotonic()
        elapsed = self._arrow_elapsed(now)
        self._arrow_continuous = enabled
        self._arrow_preview_timer.stop()
        self._arrow_run_until = 0.0
        self._arrow_frozen_elapsed = elapsed
        self._arrow_epoch = now-elapsed
        self._sync_flow_arrows()
        self.continuousAnimationChanged.emit(enabled)

    def _finish_run_preview(self):
        remaining = self._arrow_run_until - monotonic()
        if not self._arrow_continuous and remaining > 0:
            # Windows monotonic clock and Qt timers can differ by one tick.
            self._arrow_preview_timer.start(max(1, int(remaining * 1000) + 1))
            return
        self._sync_flow_arrows()

    def _sync_flow_arrows(self, *_):
        self._arrow_cache.clear()
        visible = self.arrows_visible
        if getattr(self.scene(), 'arrows_visible', True) != visible:
            self.scene().arrows_visible = visible
            # Include terminal arrowheads outside the animated repaint region.
            self.scene().update()
        if not self._arrow_animation_active():
            self._arrow_preview_timer.stop()
        if self.arrows_visible and self.isVisible() and getattr(self.scene(), 'flow_arrow_edges', ()) and self._arrow_animation_active():
            self._arrow_timer.start()
        else:
            self._arrow_timer.stop()
        self.viewport().update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_flow_arrows()

    def _advance_flow_arrows(self):
        if not self._arrow_animation_active():
            self._sync_flow_arrows()
            return
        if not self.arrows_visible or not self.isVisible() or not getattr(self.scene(), 'flow_arrow_edges', ()):
            self._arrow_timer.stop()
            self._arrow_cache.clear()
            return
        if not self.window().isMinimized():
            self.viewport().update(self._arrow_repaint_region)

    def _draw_flow_arrows(self, painter, rect):
        edges = getattr(self.scene(), 'flow_arrow_edges', ())
        if not self.arrows_visible or not edges:
            return
        transform = painter.worldTransform()
        viewport = QRectF(self.viewport().rect())
        visible_scene = self.mapToScene(self.viewport().rect()).boundingRect()
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.Antialiasing)
        # Foreground decorations must never cover a node or its text.
        clip = QPainterPath()
        clip.addRect(viewport)
        bodies = QPainterPath()
        bodies.setFillRule(Qt.WindingFill)
        for item in self.scene().items(visible_scene):
            if isinstance(item, NodeItem):
                bodies.addPath(transform.map(item.mapToScene(item.shape())))
        painter.setClipPath(clip.subtracted(bodies), Qt.IntersectClip)
        painter.setBrush(Qt.NoBrush)
        elapsed = self._arrow_elapsed()
        active_cache = {}
        repaint_region = QRegion()
        for edge in edges:
            if not edge.sceneBoundingRect().intersects(visible_scene):
                continue
            path = edge.path()
            cached = self._arrow_cache.get(edge)
            if cached is None or cached[0] != path or cached[1] != transform or cached[4] != viewport:
                segments, total = arrow_segments(path, transform)
                cached = (path, transform, segments, total, viewport, arrow_repaint_region(segments, viewport))
            active_cache[edge] = cached
            repaint_region |= cached[5]
            arrows = moving_arrows(cached[2], cached[3], viewport, elapsed)
            color, _ = edge._branch_style()
            error_link = edge.link_kind in (5, 6)
            color = color.darker(155) if NODE_COLOR.lightness() > 128 else color.lighter(115 if error_link else 140)
            if edge.isSelected() and not error_link:
                color = EDGE_SELECTED_COLOR
            pen = QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(arrows)
        self._arrow_cache = active_cache
        self._arrow_repaint_region = repaint_region
        painter.restore()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        self._draw_flow_arrows(painter, rect)
        active = next((node for node in self.scene().nodes_by_id.values()
                       if getattr(node, 'runtime_active', False)), None)
        if active is None:
            return
        # Draw above every item/effect, in viewport pixels so fitting a large
        # graph cannot shrink the execution outline into an almost invisible line.
        path = painter.worldTransform().map(active.mapToScene(active.shape()))
        painter.save()
        painter.resetTransform()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        for width, color in ((13, '#405cffae'), (8, '#aa26ff99'),
                             (4, '#32ff9c'), (1.2, '#effff7')):
            pen = QPen(QColor(color), width)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
        painter.restore()

    def set_instruction_types(self, type_ids_) -> None:
        self._instruction_types = {str(type_id_) for type_id_ in type_ids_}
        self._instruction_specs = dict(type_ids_) if hasattr(type_ids_, "items") else {}

    def wheelEvent(self, event_):
        if self._panning or self.cutter.active:
            event_.accept()
            return
        delta = event_.angleDelta().y() or event_.pixelDelta().y()
        if delta:
            factor = 1.15 ** max(-10, min(10, delta / 120.0))
            self._set_zoom(self._zoom * factor, event_.position())
        event_.accept()

    def mousePressEvent(self, event_):
        self._suppress_context_until = 0.0
        if self.cutter.active:
            event_.accept()
            return
        if (not self._panning and event_.button() == Qt.MouseButton.RightButton
                and self.itemAt(event_.position().toPoint()) is None):
            if self.can_cut_connections():
                self._pan_moved = False
                self.cutter.begin(event_.position())
            event_.accept()
            return
        ctrl_pan_ = (
            event_.button() == Qt.MouseButton.LeftButton
            and bool(event_.modifiers() & Qt.KeyboardModifier.ControlModifier)
            and self.itemAt(event_.position().toPoint()) is None
        )
        middle_pan_ = (event_.button() == Qt.MouseButton.MiddleButton
                       and self.itemAt(event_.position().toPoint()) is None)
        if self._panning:
            event_.accept()
            return
        if event_.button() == Qt.MouseButton.RightButton or ctrl_pan_ or middle_pan_:
            self._panning = True
            self._pan_moved = False
            self._pan_start = event_.position().toPoint()
            self._pan_origin = event_.position()
            self._pan_scroll_origin = QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
            self._pan_button = event_.button()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event_.accept()
            return
        super().mousePressEvent(event_)

    def mouseMoveEvent(self, event_):
        if self.cutter.active:
            if not event_.buttons() & Qt.MouseButton.RightButton:
                self.cutter.cancel()
            else:
                self.cutter.move(event_.position())
            event_.accept()
            return
        if self._panning:
            delta_ = event_.position() - self._pan_origin
            center = self.mapToScene(self.viewport().rect().center())
            self._expand_canvas(center - delta_ / self._zoom, self._zoom)
            if abs(delta_.x()) + abs(delta_.y()) > 2:
                self._pan_moved = True
            self.horizontalScrollBar().setValue(
                self._pan_scroll_origin.x() - round(delta_.x())
            )
            self.verticalScrollBar().setValue(
                self._pan_scroll_origin.y() - round(delta_.y())
            )
            event_.accept()
            return
        super().mouseMoveEvent(event_)

    def mouseReleaseEvent(self, event_):
        if self.cutter.active:
            if event_.button() != Qt.MouseButton.RightButton:
                event_.accept()
                return
            dragged, pairs = self.cutter.finish(event_.position())
            if dragged:
                if pairs and self.can_cut_connections():
                    # The host's existing batch deletion gives one undo step and
                    # synchronizes all views. Keep the camera still after reload.
                    transform = self.transform()
                    center = self.mapToScene(self.viewport().rect().center())
                    self.deleteEdgesRequested.emit(pairs)
                    self.setTransform(transform)
                    self._zoom = transform.m11()
                    self.centerOn(center)
                    self.zoomChanged.emit(self._zoom*100)
            else:
                self.contextMenuEvent(QContextMenuEvent(
                    QContextMenuEvent.Reason.Mouse, event_.position().toPoint(),
                    event_.globalPosition().toPoint()))
            self._suppress_context_until = monotonic()+.3
            event_.accept()
            return
        if self._panning and event_.button() == self._pan_button:
            self.mouseMoveEvent(event_)
            self._panning = False
            if self._pan_button != Qt.MouseButton.RightButton:
                self._pan_moved = False
            self._pan_button = Qt.MouseButton.NoButton
            self.unsetCursor()
            event_.accept()
            return
        super().mouseReleaseEvent(event_)

    def focusOutEvent(self, event_):
        self.cutter.cancel()
        self._panning = False
        self._pan_button = Qt.MouseButton.NoButton
        self._pan_moved = False
        self.unsetCursor()
        super().focusOutEvent(event_)

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

    def _add_arrow_actions(self, menu):
        enable = menu.addAction('打开箭头')
        disable = menu.addAction('关闭箭头')
        enable.setEnabled(not self.arrows_visible)
        disable.setEnabled(self.arrows_visible)
        enable.setToolTip('显示连线方向箭头。')
        disable.setToolTip('隐藏所有连线箭头，保留连线和文字。')
        enable.triggered.connect(lambda checked=False: self.set_arrows_visible(True))
        disable.triggered.connect(lambda checked=False: self.set_arrows_visible(False))
        return enable, disable

    def _add_animation_actions(self, menu):
        enable = menu.addAction('打开持续动画')
        disable = menu.addAction('关闭持续动画')
        enable.setEnabled(not self.continuous_animation)
        disable.setEnabled(self.continuous_animation)
        enable.setToolTip('持续播放循环、判断和报错连线上的流动箭头。')
        disable.setToolTip('停止持续播放；以后每次开始运行时显示箭头 5 秒，然后自动隐藏，只保留高亮。')
        enable.triggered.connect(lambda checked=False: self.set_continuous_animation(True))
        disable.triggered.connect(lambda checked=False: self.set_continuous_animation(False))
        return enable, disable

    def contextMenuEvent(self, event_):
        from context_menu_style import style_context_menu
        if self.cutter.active or monotonic() < self._suppress_context_until:
            event_.accept()
            return
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
            style_context_menu(menu, self)
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
            style_context_menu(menu_, self)
            self._add_connection_undo(menu_)
            menu_.addSeparator()
            self._add_arrow_actions(menu_)
            menu_.addSeparator()
            self._add_animation_actions(menu_)
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
                style_context_menu(category_menu_, self)
                for type_id_, title_ in entries_:
                    action_ = category_menu_.addAction(title_)
                    action_types_[action_] = type_id_
            template_actions_ = {}
            template_menu_ = menu_.addMenu("插入模板")
            style_context_menu(template_menu_, self)
            for name_ in self.template_names_provider() or ():
                action_ = template_menu_.addAction(str(name_))
                template_actions_[action_] = str(name_)
            if not template_actions_:
                template_menu_.addAction("暂无模板").setEnabled(False)
            if not action_types_:
                menu_.addAction("暂无可用指令").setEnabled(False)
            selected_action_ = menu_.exec(event_.globalPos())
            menu_.deleteLater()
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
            style_context_menu(menu, self)
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

        style_context_menu(menu_, self)
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
        if event_.key() == Qt.Key.Key_Escape and self.cutter.active:
            self.cutter.cancel()
            self._suppress_context_until = monotonic()+.3
            event_.accept()
            return
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

    def paintEvent(self, event_):
        super().paintEvent(event_)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.cutter.paint(painter)
        painter.end()

    def hideEvent(self, event_):
        self._arrow_timer.stop()
        self._arrow_cache.clear()
        self.cutter.cancel()
        super().hideEvent(event_)

    def fit_graph(self):
        if self.cutter.active:
            self.cutter.cancel()
        fitted_rect_ = self.scene().graph_items_rect()
        self.scene().setSceneRect(self.scene().sceneRect().united(fitted_rect_))
        self.fitInView(fitted_rect_, Qt.AspectRatioMode.KeepAspectRatio)
        fitted_zoom_ = self.transform().m11()
        self._zoom = max(MIN_ZOOM, min(fitted_zoom_, MAX_ZOOM))
        if fitted_zoom_ and fitted_zoom_ != self._zoom:
            self.scale(self._zoom / fitted_zoom_, self._zoom / fitted_zoom_)
        self._expand_canvas(fitted_rect_.center(), self._zoom)
        self.centerOn(fitted_rect_.center())
        self.zoomChanged.emit(self._zoom * 100)

    def zoom_in(self):
        self._set_zoom(min(MAX_ZOOM, self._zoom * 1.2))

    def zoom_out(self):
        self._set_zoom(max(MIN_ZOOM, self._zoom / 1.2))

    def _expand_canvas(self, center, zoom, reset=False):
        width = max(1000.0, self.viewport().width() / zoom * 4)
        height = max(1000.0, self.viewport().height() / zoom * 4)
        needed = QRectF(center.x()-width/2, center.y()-height/2, width, height)
        current = self.scene().itemsBoundingRect() if reset else self.scene().sceneRect()
        if reset or not current.contains(needed):
            self.scene().setSceneRect(current.united(needed))

    def _set_zoom(self, zoom_: float, anchor=None):
        if self.cutter.active:
            self.cutter.cancel()
        if not math.isfinite(float(zoom_)):
            return
        zoom_ = max(MIN_ZOOM, min(float(zoom_), MAX_ZOOM))
        if zoom_ == self._zoom:
            return
        anchor = QPointF(self.viewport().rect().center()) if anchor is None else anchor
        target = self.mapToScene(anchor.toPoint())
        self._expand_canvas(target, zoom_, reset=True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.scale(zoom_ / self._zoom, zoom_ / self._zoom)
        self.centerOn(target + (QPointF(self.viewport().rect().center()) - anchor) / zoom_)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._zoom = zoom_
        self.zoomChanged.emit(self._zoom * 100)

    def resizeEvent(self, event_):
        if hasattr(self, 'cutter') and self.cutter.active:
            self.cutter.cancel()
        super().resizeEvent(event_)
