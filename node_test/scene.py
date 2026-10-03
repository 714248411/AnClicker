import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Signal, Qt
from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QGraphicsScene

from node_test.edge import EdgeItem
from node_test.node import NodeItem, PortItem
from node_test.style import (
    AUTO_CONNECT_DISTANCE,
    BACKGROUND_COLOR,
    GRID_LARGE_COLOR,
    GRID_SMALL_COLOR,
    NODE_TYPES,
)


class NodeScene(QGraphicsScene):
    graphChanged = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000.0, -5000.0, 10000.0, 10000.0)
        self.setBackgroundBrush(QBrush(BACKGROUND_COLOR))
        self.drag_edge = None
        self._node_offset = 0

    def add_node(self, node_type, position=None):
        definition = NODE_TYPES.get(node_type)
        if definition is None:
            return None
        node = NodeItem(node_type, definition)
        self.addItem(node)
        if position is None:
            offset = float((self._node_offset % 8) * 28)
            position = QPointF(-80.0 + offset, -60.0 + offset)
            self._node_offset += 1
        node.setPos(position)
        self.clearSelection()
        node.setSelected(True)
        self.emit_graph_changed()
        self.auto_connect_nearby_ports(node)
        return node

    def connect_ports(self, source_port, target_port):
        if not self.can_connect(source_port, target_port):
            return None
        edge = EdgeItem(source_port, target_port)
        self.addItem(edge)
        self.emit_graph_changed()
        return edge

    def auto_connect_nearby_ports(self, node):
        """Connect compatible ports close to a newly placed or moved node."""
        if not isinstance(node, NodeItem) or node.scene() is not self:
            return []

        candidates = []
        node_ports = node.input_ports + node.output_ports
        other_ports = [
            item
            for item in self.items()
            if isinstance(item, PortItem) and item.node is not node
        ]
        for node_port in node_ports:
            for other_port in other_ports:
                source_port = node_port if node_port.direction == "output" else other_port
                target_port = node_port if node_port.direction == "input" else other_port
                if not self.can_connect(source_port, target_port):
                    continue
                distance = QLineF(source_port.scenePos(), target_port.scenePos()).length()
                if distance <= AUTO_CONNECT_DISTANCE:
                    candidates.append((distance, source_port, target_port))

        connected_edges = []
        for _distance, source_port, target_port in sorted(candidates, key=lambda item: item[0]):
            edge = self.connect_ports(source_port, target_port)
            if edge is not None:
                connected_edges.append(edge)
        return connected_edges

    @staticmethod
    def can_connect(source_port, target_port):
        return (
            isinstance(source_port, PortItem)
            and isinstance(target_port, PortItem)
            and source_port.direction == "output"
            and target_port.direction == "input"
            and source_port.node is not target_port.node
            and not target_port.has_connection()
        )

    def remove_edge(self, edge):
        if edge.scene() is not self:
            return
        edge.detach()
        self.removeItem(edge)

    def delete_selected(self):
        selected = list(self.selectedItems())
        nodes = [item for item in selected if isinstance(item, NodeItem)]
        edges = [item for item in selected if isinstance(item, EdgeItem)]

        for node in nodes:
            for edge in node.all_edges():
                self.remove_edge(edge)
            self.removeItem(node)
        for edge in edges:
            if edge.scene() is self:
                self.remove_edge(edge)
        if nodes or edges:
            self.emit_graph_changed()

    def clear_graph(self):
        for item in list(self.items()):
            if isinstance(item, EdgeItem):
                self.remove_edge(item)
        for item in list(self.items()):
            if isinstance(item, NodeItem):
                self.removeItem(item)
        self.drag_edge = None
        self.emit_graph_changed()

    def graph_items_rect(self):
        nodes = [item for item in self.items() if isinstance(item, NodeItem)]
        if not nodes:
            return QRectF(-200.0, -150.0, 400.0, 300.0)
        rect = nodes[0].sceneBoundingRect()
        for node in nodes[1:]:
            rect = rect.united(node.sceneBoundingRect())
        return rect.adjusted(-80.0, -80.0, 80.0, 80.0)

    def emit_graph_changed(self):
        node_count = sum(isinstance(item, NodeItem) for item in self.items())
        edge_count = sum(
            isinstance(item, EdgeItem) and item.target_port is not None
            for item in self.items()
        )
        self.graphChanged.emit(node_count, edge_count)

    def port_at(self, position):
        for item in self.items(position):
            if isinstance(item, PortItem):
                return item
        return None

    def mousePressEvent(self, event):
        port = self.port_at(event.scenePos())
        if event.button() == Qt.MouseButton.LeftButton and port is not None and port.direction == "output":
            self.clearSelection()
            self.drag_edge = EdgeItem(port)
            self.addItem(self.drag_edge)
            self.drag_edge.set_drag_position(event.scenePos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_edge is not None:
            target = self.port_at(event.scenePos())
            is_valid = target is None or self.can_connect(self.drag_edge.source_port, target)
            self.drag_edge.set_drag_position(event.scenePos(), is_valid)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_edge is not None and event.button() == Qt.MouseButton.LeftButton:
            edge = self.drag_edge
            self.drag_edge = None
            target = self.port_at(event.scenePos())
            if self.can_connect(edge.source_port, target):
                edge.set_target_port(target)
                self.emit_graph_changed()
            else:
                self.remove_edge(edge)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, BACKGROUND_COLOR)
        small_grid = 20
        large_grid = 100

        left = int(math.floor(rect.left() / small_grid) * small_grid)
        top = int(math.floor(rect.top() / small_grid) * small_grid)
        small_lines = []
        large_lines = []

        x = left
        while x < rect.right():
            line = QLineF(float(x), rect.top(), float(x), rect.bottom())
            (large_lines if x % large_grid == 0 else small_lines).append(line)
            x += small_grid

        y = top
        while y < rect.bottom():
            line = QLineF(rect.left(), float(y), rect.right(), float(y))
            (large_lines if y % large_grid == 0 else small_lines).append(line)
            y += small_grid

        painter.setPen(QPen(GRID_SMALL_COLOR, 1.0))
        painter.drawLines(small_lines)
        painter.setPen(QPen(GRID_LARGE_COLOR, 1.0))
        painter.drawLines(large_lines)
