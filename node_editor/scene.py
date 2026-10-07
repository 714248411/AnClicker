"""Validated directed-flow graphics scene for Clicker instructions."""

from __future__ import annotations

import math
from collections.abc import Mapping

from qt_compat.QtCore import QLineF, QPointF, QRectF, Signal, Qt
from qt_compat.QtGui import QBrush, QColor, QPainterPath, QPen
from qt_compat.QtWidgets import QGraphicsPathItem, QGraphicsScene

from node_editor.items import EdgeItem, NodeItem
from node_editor.specs import NodeDisplaySpec, normalize_specs
from node_editor.style import (
    AUTO_CONNECT_DISTANCE,
    BACKGROUND_COLOR,
    DEFAULT_NODE_COLOR,
    END_COLOR,
    GRID_LARGE_COLOR,
    GRID_SMALL_COLOR,
    START_COLOR,
)


def _record_value(record_, *names_, default=None):
    if isinstance(record_, Mapping):
        for name_ in names_:
            if name_ in record_:
                return record_[name_]
        return default
    for name_ in names_:
        if hasattr(record_, name_):
            return getattr(record_, name_)
    return default


class NodeScene(QGraphicsScene):
    """Scene containing a branch-capable start-to-end DAG."""

    graphChanged = Signal(int, int)
    commandActivated = Signal(object)
    reorderPreview = Signal(object)
    reorderCommitted = Signal(object)
    graphCommitted = Signal(object, object, float, float)
    positionCommitted = Signal(object, float, float)
    sizeCommitted = Signal(object, float, float)
    connectionRequested = Signal(object, object)
    branchConnectionRequested = Signal(object, object, int)

    START_NODE_ID = "__start__"
    END_NODE_ID = "__end__"

    def __init__(self, parent_=None):
        super().__init__(parent_)
        self.setSceneRect(-5000.0, -5000.0, 10000.0, 10000.0)
        self.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
        self.specs: dict[str, NodeDisplaySpec] = {}
        self.nodes_by_id: dict[object, NodeItem] = {}
        self.nodes_by_command_id: dict[object, NodeItem] = {}
        self.chain_order: list[NodeItem] = []
        self.edges: list[EdgeItem] = []

        self._drag_node: NodeItem | None = None
        self._drag_origin_position = QPointF()
        self._drag_original_order: list[NodeItem] = []
        self._preview_order: list[NodeItem] = []
        self._updating_graph = False
        self._complete_chain = True
        self._connection_port = None
        self._connection_preview = None
        self._routing_edges = False

    def reroute_edges(self) -> None:
        """Recalculate all paths so node avoidance and crossing scores agree."""
        if self._routing_edges:
            return
        self._routing_edges = True
        try:
            from .routing_index import RoutingIndex
            from qt_compat.QtGui import QPainterPathStroker
            self._route_index = RoutingIndex()
            for node_ in self.nodes_by_id.values():
                self._route_index.add(node_, node_.sceneBoundingRect().adjusted(-10, -10, 10, 10))
            stroker_ = QPainterPathStroker()
            stroker_.setWidth(4.0)
            for edge_ in self.edges:
                stroke_ = stroker_.createStroke(edge_.path())
                self._route_index.add(edge_, stroke_.boundingRect(), stroke_)
            rects_ = [node_.sceneBoundingRect() for node_ in self.nodes_by_id.values()]
            self._routing_bounds = (
                min((rect_.top() for rect_ in rects_), default=0),
                max((rect_.bottom() for rect_ in rects_), default=0),
            )
            self._routing_right = max((rect_.right() for rect_ in rects_), default=0)
            routing_order_ = sorted(self.edges, key=lambda edge_: QLineF(
                edge_.source_port.scenePos(), edge_.target_port.scenePos()).length(), reverse=True)
            # A second pass lets earlier edges account for routes selected by
            # later edges without introducing an unstable recursive update.
            for _ in range(2):
                for edge_ in routing_order_:
                    edge_.update_path()
        finally:
            self._route_index = None
            self._routing_bounds = None
            self._routing_right = None
            self._routing_edges = False

    def begin_port_connection(self, port_) -> None:
        self.cancel_port_connection()
        self._connection_port = port_
        preview_ = QGraphicsPathItem()
        preview_.setZValue(0.0)
        preview_.setPen(QPen(QColor("#7c8cff"), 2.5, Qt.PenStyle.DashLine))
        self.addItem(preview_)
        self._connection_preview = preview_
        self.update_port_connection(port_.scenePos())

    def update_port_connection(self, scene_position_) -> None:
        if self._connection_port is None or self._connection_preview is None:
            return
        start_ = self._connection_port.scenePos()
        end_ = QPointF(scene_position_)
        path_ = QPainterPath(start_)
        distance_ = max(abs(end_.x() - start_.x()) * 0.5, 60.0)
        path_.cubicTo(
            QPointF(start_.x(), start_.y() - distance_)
            if self._connection_port is self._connection_port.node.no_port
            else QPointF(start_.x() + (distance_ if self._connection_port.direction == "output" else -distance_), start_.y()),
            QPointF(end_.x() - distance_, end_.y()), end_,
        )
        self._connection_preview.setPath(path_)

    def end_port_connection(self, scene_position_) -> None:
        source_port_ = self._connection_port
        target_node_ = None
        for item_ in self.items(QPointF(scene_position_)):
            candidate_ = item_
            while candidate_ is not None and not isinstance(candidate_, NodeItem):
                candidate_ = candidate_.parentItem()
            if isinstance(candidate_, NodeItem):
                target_node_ = candidate_
                break
        self.cancel_port_connection()
        if source_port_ is None or target_node_ is None or target_node_ is source_port_.node:
            return
        if source_port_.direction == "output" and target_node_.input_port is not None:
            if source_port_.link_kind is not None:
                self.branchConnectionRequested.emit(source_port_.node.node_id, target_node_.node_id, source_port_.link_kind)
            else:
                self.connectionRequested.emit(source_port_.node.node_id, target_node_.node_id)
        elif source_port_.direction == "input" and target_node_.output_port is not None:
            target_port_ = target_node_.connection_port_at(target_node_.mapFromScene(scene_position_))
            if target_node_.type_id in {"条件判断", "颜色判断"}:
                kind_ = 2 if target_port_ is target_node_.no_port else 1
                self.branchConnectionRequested.emit(target_node_.node_id, source_port_.node.node_id, kind_)
            else:
                self.connectionRequested.emit(target_node_.node_id, source_port_.node.node_id)

    def cancel_port_connection(self) -> None:
        if self._connection_preview is not None and self._connection_preview.scene() is self:
            self.removeItem(self._connection_preview)
        self._connection_preview = None
        self._connection_port = None

    def load_graph(self, nodes_, edges_, specs_, allow_incomplete=False) -> None:
        """Replace scene contents with a validated directed graph.

        Node records accept ``node_id``/``id``, ``command_id``, ``type_id``/
        ``type``, ``x`` and ``y``.  Terminals may use ``role='start'`` or
        ``role='end'``; missing terminals are added automatically.  Edges accept
        two-item sequences or mappings with ``source`` and ``target`` keys.  If
        no edges are supplied, input node order is used as the chain order.
        """

        specs_normalized_ = normalize_specs(specs_)
        node_records_ = list(nodes_ or [])
        edge_records_ = list(edges_ or [])

        prepared_records_: list[dict] = []
        start_count_ = 0
        end_count_ = 0
        for sequence_index_, record_ in enumerate(node_records_):
            type_value_ = _record_value(record_, "type_id", "type", "指令类型", default="")
            type_id_ = str(type_value_)
            role_value_ = _record_value(
                record_, "role", "terminal_role", "kind", default=None
            )
            role_ = str(role_value_).casefold() if role_value_ is not None else None
            if role_ not in {"start", "end"}:
                if type_id_.casefold() in {"start", "__start__", "开始"}:
                    role_ = "start"
                elif type_id_.casefold() in {"end", "__end__", "结束"}:
                    role_ = "end"
                else:
                    role_ = None

            node_id_ = _record_value(record_, "node_id", "id", "节点ID", default=None)
            command_id_ = _record_value(record_, "command_id", "命令ID", default=None)
            if role_ == "start":
                start_count_ += 1
                node_id_ = self.START_NODE_ID if node_id_ is None else node_id_
                command_id_ = None
                type_id_ = "start"
            elif role_ == "end":
                end_count_ += 1
                node_id_ = self.END_NODE_ID if node_id_ is None else node_id_
                command_id_ = None
                type_id_ = "end"
            else:
                if node_id_ is None:
                    node_id_ = command_id_
                if command_id_ is None:
                    command_id_ = node_id_
                if node_id_ is None:
                    raise ValueError("instruction node is missing id")
                if not type_id_:
                    raise ValueError(f"instruction node {node_id_!r} is missing type_id")

            prepared_records_.append(
                {
                    "node_id": node_id_,
                    "command_id": command_id_,
                    "type_id": type_id_,
                    "role": role_,
                    "x": float(_record_value(record_, "x", default=0.0)),
                    "y": float(
                        _record_value(record_, "y", default=sequence_index_ * 120.0)
                    ),
                    "repeat_count": int(_record_value(record_, "repeat_count", default=1)),
                    "parameters": dict(_record_value(record_, "parameters", default={}) or {}),
                    "note": str(_record_value(record_, "note", default="") or ""),
                    "width": _record_value(record_, "width", default=None),
                    "height": _record_value(record_, "height", default=None),
                }
            )

        if start_count_ > 1 or end_count_ > 1:
            raise ValueError("graph must contain exactly one start and one end")

        command_records_ = [record_ for record_ in prepared_records_ if record_["role"] is None]
        if start_count_ == 0:
            minimum_y_ = min((record_["y"] for record_ in command_records_), default=0.0)
            prepared_records_.insert(
                0,
                {
                    "node_id": self.START_NODE_ID,
                    "command_id": None,
                    "type_id": "start",
                    "role": "start",
                    "x": 0.0,
                    "y": minimum_y_ - 120.0,
                    "repeat_count": 1,
                    "parameters": {},
                    "note": "",
                    "width": None,
                    "height": None,
                },
            )
        if end_count_ == 0:
            maximum_y_ = max((record_["y"] for record_ in command_records_), default=0.0)
            prepared_records_.append(
                {
                    "node_id": self.END_NODE_ID,
                    "command_id": None,
                    "type_id": "end",
                    "role": "end",
                    "x": 0.0,
                    "y": maximum_y_ + 120.0,
                    "repeat_count": 1,
                    "parameters": {},
                    "note": "",
                    "width": None,
                    "height": None,
                }
            )

        node_ids_ = [record_["node_id"] for record_ in prepared_records_]
        if len(set(node_ids_)) != len(node_ids_):
            raise ValueError("node ids must be unique")
        command_ids_ = [
            record_["command_id"]
            for record_ in prepared_records_
            if record_["role"] is None
        ]
        if len(set(command_ids_)) != len(command_ids_):
            raise ValueError("command ids must be unique")

        self._updating_graph = True
        try:
            self.clear()
            self.nodes_by_id.clear()
            self.nodes_by_command_id.clear()
            self.chain_order.clear()
            self.edges.clear()
            self.specs = specs_normalized_

            input_order_: list[NodeItem] = []
            for record_ in prepared_records_:
                role_ = record_["role"]
                if role_ == "start":
                    title_ = "开始"
                    color_ = START_COLOR
                elif role_ == "end":
                    title_ = "结束"
                    color_ = END_COLOR
                else:
                    spec_ = specs_normalized_.get(record_["type_id"])
                    title_ = spec_.title if spec_ is not None else record_["type_id"]
                    color_ = spec_.color if spec_ is not None else DEFAULT_NODE_COLOR
                    if record_["type_id"] in {"循环", "条件循环"}:
                        count_ = int(record_["parameters"].get("次数", record_["repeat_count"]))
                        title_ = f"{title_}  × {count_}"
                node_ = NodeItem(
                    record_["node_id"],
                    record_["command_id"],
                    record_["type_id"],
                    title_,
                    color_,
                    role_,
                    control_kind_=(
                        "condition" if record_["type_id"] in {"条件判断", "条件循环", "颜色判断"}
                        else "loop" if record_["type_id"] == "循环" else None
                    ),
                    subtitle_=self._node_subtitle(
                        record_["type_id"], record_["parameters"], record_["repeat_count"]
                    ),
                    note_=record_["note"],
                    width_=record_["width"],
                    height_=record_["height"],
                )
                self.addItem(node_)
                node_.setPos(record_["x"], record_["y"])
                self.nodes_by_id[node_.node_id] = node_
                if not node_.is_terminal:
                    self.nodes_by_command_id[node_.command_id] = node_
                input_order_.append(node_)

            if edge_records_:
                try:
                    graph_order_ = self._validate_and_order_edges(edge_records_)
                    self.chain_order = graph_order_
                    endpoints_ = [self._edge_endpoints(edge_) for edge_ in edge_records_]
                    outgoing_counts_: dict[object, int] = {}
                    incoming_counts_: dict[object, int] = {}
                    for source_id_, target_id_ in endpoints_:
                        outgoing_counts_[source_id_] = outgoing_counts_.get(source_id_, 0) + 1
                        incoming_counts_[target_id_] = incoming_counts_.get(target_id_, 0) + 1
                        edge_ = EdgeItem(
                            self.nodes_by_id[source_id_], self.nodes_by_id[target_id_],
                            self._edge_kind(edge_records_[len(self.edges)])
                        )
                        self.addItem(edge_)
                        self.edges.append(edge_)
                    # Drag-to-reorder is only meaningful for a true linear chain.
                    self._complete_chain = (
                        len(endpoints_) == len(self.nodes_by_id) - 1
                        and max(outgoing_counts_.values(), default=0) <= 1
                        and max(incoming_counts_.values(), default=0) <= 1
                    )
                except ValueError:
                    if not allow_incomplete:
                        raise
                    # Editing is allowed to hold a temporarily incomplete flow.
                    self._complete_chain = False
                    self.chain_order = list(input_order_)
                    for edge_record_ in edge_records_:
                        source_id_, target_id_ = self._edge_endpoints(edge_record_)
                        edge_ = EdgeItem(
                            self.nodes_by_id[source_id_], self.nodes_by_id[target_id_],
                            self._edge_kind(edge_record_)
                        )
                        self.addItem(edge_)
                        self.edges.append(edge_)
            else:
                start_node_ = next(node_ for node_ in input_order_ if node_.terminal_role == "start")
                end_node_ = next(node_ for node_ in input_order_ if node_.terminal_role == "end")
                command_nodes_ = [node_ for node_ in input_order_ if not node_.is_terminal]
                chain_order_ = [start_node_, *command_nodes_, end_node_]
                if allow_incomplete:
                    self.chain_order = chain_order_
                    self._complete_chain = False
                else:
                    self._complete_chain = True
                    self._set_chain_order(chain_order_)
            self.reroute_edges()
        finally:
            self._updating_graph = False
        self.clearSelection()
        self.emit_graph_changed()

    @staticmethod
    def _node_subtitle(type_id_: str, parameters_: Mapping, repeat_count_: int) -> str:
        visible_ = {
            str(key_): value_ for key_, value_ in dict(parameters_ or {}).items()
            if not str(key_).startswith("__flow_") and key_ not in {"录制批次", "录制时间"}
        }
        if type_id_ == "条件判断":
            return str(visible_.get("条件", "True"))
        if type_id_ in {"循环", "条件循环"}:
            mode_ = str(visible_.get("方式", "次数"))
            if mode_ in {"条件", "cond"} or type_id_ == "条件循环":
                return f"条件：{visible_.get('条件', 'True')}"
            return f"循环 {visible_.get('次数', 1)} 次"
        parts_ = [f"{key_}: {value_}" for key_, value_ in list(visible_.items())[:2]]
        if repeat_count_ > 1:
            parts_.append(f"重复 ×{repeat_count_}")
        return "  ·  ".join(parts_) or "双击配置"

    def commit_node_size(self, node_, width_: float, height_: float) -> None:
        self.sizeCommitted.emit(node_.node_id, float(width_), float(height_))

    def _edge_endpoints(self, edge_record_):
        if isinstance(edge_record_, Mapping):
            source_id_ = _record_value(
                edge_record_, "source", "source_id", "from", "起点"
            )
            target_id_ = _record_value(
                edge_record_, "target", "target_id", "to", "终点"
            )
        else:
            try:
                source_id_, target_id_ = edge_record_
            except (TypeError, ValueError) as error_:
                raise ValueError("edge must contain source and target ids") from error_
        if source_id_ not in self.nodes_by_id or target_id_ not in self.nodes_by_id:
            raise ValueError("edge references an unknown node")
        return source_id_, target_id_

    @staticmethod
    def _edge_kind(edge_record_) -> int:
        if isinstance(edge_record_, Mapping):
            return int(_record_value(edge_record_, "kind", "link_kind", "类型", default=0) or 0)
        return int(getattr(edge_record_, "kind", 0) or 0)

    def _validate_and_order_edges(self, edge_records_) -> list[NodeItem]:
        """Validate a complete DAG and return a stable topological order."""
        successors_: dict[object, set[object]] = {
            node_id_: set() for node_id_ in self.nodes_by_id
        }
        predecessors_: dict[object, set[object]] = {
            node_id_: set() for node_id_ in self.nodes_by_id
        }
        pairs_: set[tuple[object, object]] = set()
        for edge_record_ in edge_records_:
            source_id_, target_id_ = self._edge_endpoints(edge_record_)
            if source_id_ == target_id_:
                raise ValueError("self-loop is not allowed")
            if (source_id_, target_id_) in pairs_:
                raise ValueError("duplicate edge is not allowed")
            pairs_.add((source_id_, target_id_))
            successors_[source_id_].add(target_id_)
            predecessors_[target_id_].add(source_id_)

        start_node_ = next(
            node_ for node_ in self.nodes_by_id.values() if node_.terminal_role == "start"
        )
        end_node_ = next(
            node_ for node_ in self.nodes_by_id.values() if node_.terminal_role == "end"
        )
        if predecessors_[start_node_.node_id]:
            raise ValueError("start node cannot have an input")
        if successors_[end_node_.node_id]:
            raise ValueError("end node cannot have an output")

        reachable_ = {start_node_.node_id}
        pending_ = [start_node_.node_id]
        while pending_:
            for target_id_ in successors_[pending_.pop()]:
                if target_id_ not in reachable_:
                    reachable_.add(target_id_)
                    pending_.append(target_id_)
        can_reach_end_ = {end_node_.node_id}
        pending_ = [end_node_.node_id]
        while pending_:
            for source_id_ in predecessors_[pending_.pop()]:
                if source_id_ not in can_reach_end_:
                    can_reach_end_.add(source_id_)
                    pending_.append(source_id_)
        if reachable_ != set(self.nodes_by_id) or can_reach_end_ != set(self.nodes_by_id):
            if any(len(targets_) > 1 for targets_ in successors_.values()):
                raise ValueError("every fan-out branch must lead to end")
            if any(len(sources_) > 1 for sources_ in predecessors_.values()):
                raise ValueError("multiple inputs must all be reachable from start")
            raise ValueError("every node must be reachable from start and lead to end")

        input_rank_ = {node_.node_id: index_ for index_, node_ in enumerate(self.nodes_by_id.values())}
        indegree_ = {node_id_: len(items_) for node_id_, items_ in predecessors_.items()}
        ready_ = sorted(
            (node_id_ for node_id_, count_ in indegree_.items() if count_ == 0),
            key=input_rank_.get,
        )
        ordered_ids_: list[object] = []
        while ready_:
            node_id_ = ready_.pop(0)
            ordered_ids_.append(node_id_)
            for target_id_ in sorted(successors_[node_id_], key=input_rank_.get):
                indegree_[target_id_] -= 1
                if indegree_[target_id_] == 0:
                    ready_.append(target_id_)
                    ready_.sort(key=input_rank_.get)
        if len(ordered_ids_) != len(self.nodes_by_id):
            raise ValueError("cycles are not allowed")
        return [self.nodes_by_id[node_id_] for node_id_ in ordered_ids_]

    def _clear_edges(self) -> None:
        for edge_ in self.edges:
            edge_.detach()
            if edge_.scene() is self:
                self.removeItem(edge_)
        self.edges.clear()

    def _set_chain_order(self, order_) -> None:
        order_list_ = list(order_)
        if len(order_list_) < 2:
            raise ValueError("graph must include start and end nodes")
        if order_list_[0].terminal_role != "start" or order_list_[-1].terminal_role != "end":
            raise ValueError("chain must begin with start and end with end")
        if len(set(order_list_)) != len(order_list_):
            raise ValueError("chain cannot contain a node more than once")

        self._clear_edges()
        self.chain_order = order_list_
        for source_node_, target_node_ in zip(order_list_, order_list_[1:]):
            edge_ = EdgeItem(source_node_, target_node_)
            self.addItem(edge_)
            self.edges.append(edge_)

    @staticmethod
    def _command_order(order_) -> list:
        return [node_.command_id for node_ in order_ if not node_.is_terminal]

    def begin_node_drag(self, node_: NodeItem) -> None:
        if self._updating_graph:
            return
        self._drag_node = node_
        self._drag_origin_position = QPointF(node_.pos())
        self._drag_original_order = list(self.chain_order)
        self._preview_order = list(self.chain_order)

    def node_position_changed(self, node_: NodeItem) -> None:
        if self._updating_graph:
            return
        self.reroute_edges()
        if (self._updating_graph or not self._complete_chain
                or node_ is not self._drag_node or node_.is_terminal):
            return
        candidate_order_ = self._candidate_order(node_)
        desired_order_ = candidate_order_ or self._drag_original_order
        if desired_order_ != self._preview_order:
            self._set_chain_order(desired_order_)
            self._preview_order = list(desired_order_)
            self.reorderPreview.emit(self._command_order(desired_order_))
            self.emit_graph_changed()

    def _candidate_order(self, node_: NodeItem) -> list[NodeItem] | None:
        if node_.input_port is None or node_.output_port is None:
            return None
        base_order_ = [item_ for item_ in self._drag_original_order if item_ is not node_]
        candidates_: list[tuple[float, int]] = []
        for insertion_index_ in range(1, len(base_order_)):
            previous_node_ = base_order_[insertion_index_ - 1]
            next_node_ = base_order_[insertion_index_]
            if previous_node_.output_port is None or next_node_.input_port is None:
                continue
            # Reordering keeps the original vertical snap gesture even though
            # explicit flow ports now live on the left and right edges.
            previous_bottom_ = previous_node_.scenePos() + QPointF(
                previous_node_.width / 2.0, previous_node_.height
            )
            node_top_ = node_.scenePos() + QPointF(node_.width / 2.0, 0.0)
            node_bottom_ = node_.scenePos() + QPointF(
                node_.width / 2.0, node_.height
            )
            next_top_ = next_node_.scenePos() + QPointF(
                next_node_.width / 2.0, 0.0
            )
            incoming_distance_ = QLineF(previous_bottom_, node_top_).length()
            outgoing_distance_ = QLineF(node_bottom_, next_top_).length()
            if (
                incoming_distance_ <= AUTO_CONNECT_DISTANCE
                and outgoing_distance_ <= AUTO_CONNECT_DISTANCE
            ):
                candidates_.append(
                    (incoming_distance_ + outgoing_distance_, insertion_index_)
                )
        if not candidates_:
            return None
        _, insertion_index_ = min(candidates_, key=lambda candidate_: candidate_[0])
        return [
            *base_order_[:insertion_index_],
            node_,
            *base_order_[insertion_index_:],
        ]

    def end_node_drag(self, node_: NodeItem) -> None:
        if node_ is not self._drag_node:
            return
        origin_position_ = QPointF(self._drag_origin_position)
        original_order_ = list(self._drag_original_order)
        candidate_order_ = None if node_.is_terminal else self._candidate_order(node_)
        position_changed_ = node_.pos() != origin_position_

        self._drag_node = None
        self._drag_original_order = []
        self._preview_order = []

        if not self._complete_chain:
            if position_changed_:
                self.positionCommitted.emit(
                    node_.node_id, float(node_.pos().x()), float(node_.pos().y())
                )
            return

        if node_.is_terminal:
            if position_changed_:
                self.positionCommitted.emit(
                    node_.node_id, float(node_.pos().x()), float(node_.pos().y())
                )
            return

        if candidate_order_ is None:
            self._set_chain_order(original_order_)
            self.reorderPreview.emit(self._command_order(original_order_))
            if position_changed_:
                self.positionCommitted.emit(
                    node_.node_id, float(node_.pos().x()), float(node_.pos().y())
                )
            self.emit_graph_changed()
            return

        self._set_chain_order(candidate_order_)
        if candidate_order_ != original_order_:
            command_order_ = self._command_order(candidate_order_)
            node_id_ = node_.node_id
            node_x_ = float(node_.pos().x())
            node_y_ = float(node_.pos().y())
            # The host persists topology, ordering and the final drag position
            # in one transaction.  Capture all values before emitting because
            # a direct slot may synchronously reload (and delete) scene items.
            self.graphCommitted.emit(command_order_, node_id_, node_x_, node_y_)
            self.reorderCommitted.emit(command_order_)
        elif position_changed_:
            self.positionCommitted.emit(
                node_.node_id, float(node_.pos().x()), float(node_.pos().y())
            )
        self.emit_graph_changed()

    def activate_node(self, node_: NodeItem) -> None:
        if not node_.is_terminal:
            self.commandActivated.emit(node_.command_id)

    def selected_command_ids(self) -> list:
        selected_nodes_ = {
            item_
            for item_ in self.selectedItems()
            if isinstance(item_, NodeItem) and not item_.is_terminal
        }
        return [
            node_.command_id for node_ in self.chain_order if node_ in selected_nodes_
        ]

    def focus_command(self, command_id_) -> NodeItem | None:
        node_ = self.nodes_by_command_id.get(command_id_)
        if node_ is None:
            return None
        self.clearSelection()
        node_.setSelected(True)
        return node_

    def graph_items_rect(self):
        nodes_ = list(self.nodes_by_id.values())
        if not nodes_:
            return QRectF(-200.0, -150.0, 400.0, 300.0)
        rect_ = nodes_[0].sceneBoundingRect()
        for node_ in nodes_[1:]:
            rect_ = rect_.united(node_.sceneBoundingRect())
        return rect_.adjusted(-80.0, -80.0, 80.0, 80.0)

    def emit_graph_changed(self):
        self.graphChanged.emit(len(self.nodes_by_id), len(self.edges))

    def drawBackground(self, painter_, rect_):
        self.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
        painter_.fillRect(rect_, BACKGROUND_COLOR)
        small_grid_ = 20
        large_grid_ = 100
        left_ = int(math.floor(rect_.left() / small_grid_) * small_grid_)
        top_ = int(math.floor(rect_.top() / small_grid_) * small_grid_)
        small_lines_ = []
        large_lines_ = []

        x_ = left_
        while x_ < rect_.right():
            line_ = QLineF(float(x_), rect_.top(), float(x_), rect_.bottom())
            (large_lines_ if x_ % large_grid_ == 0 else small_lines_).append(line_)
            x_ += small_grid_

        y_ = top_
        while y_ < rect_.bottom():
            line_ = QLineF(rect_.left(), float(y_), rect_.right(), float(y_))
            (large_lines_ if y_ % large_grid_ == 0 else small_lines_).append(line_)
            y_ += small_grid_

        painter_.setPen(QPen(GRID_SMALL_COLOR, 1.0))
        painter_.drawLines(small_lines_)
        painter_.setPen(QPen(GRID_LARGE_COLOR, 1.0))
        painter_.drawLines(large_lines_)
