from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from node_test.style import (
    EDGE_COLOR,
    INVALID_EDGE_COLOR,
    STRAIGHT_EDGE_DISTANCE,
)


class EdgeItem(QGraphicsPathItem):
    """Visual connection between an output port and an input port."""

    def __init__(self, source_port, target_port=None):
        super().__init__()
        self.source_port = source_port
        self.target_port = target_port
        self.drag_position = source_port.scenePos()
        self.is_valid_target = True
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.source_port.add_edge(self)
        if self.target_port is not None:
            self.target_port.add_edge(self)
        self.update_path()

    def set_drag_position(self, position, is_valid=True):
        self.drag_position = QPointF(position)
        self.is_valid_target = is_valid
        self.update_path()

    def set_target_port(self, port):
        if self.target_port is port:
            return
        if self.target_port is not None:
            self.target_port.remove_edge(self)
        self.target_port = port
        if port is not None:
            port.add_edge(self)
        self.update_path()

    def update_path(self):
        start = self.source_port.scenePos()
        end = self.target_port.scenePos() if self.target_port is not None else self.drag_position
        path = QPainterPath(start)
        if QLineF(start, end).length() <= STRAIGHT_EDGE_DISTANCE:
            path.lineTo(end)
        else:
            distance = max(abs(end.y() - start.y()) * 0.5, 60.0)
            path.cubicTo(
                QPointF(start.x(), start.y() + distance),
                QPointF(end.x(), end.y() - distance),
                end,
            )
        self.setPath(path)

        color = EDGE_COLOR
        if self.isSelected() or self.isUnderMouse():
            color = self.source_port.display_color()
        if self.target_port is None and not self.is_valid_target:
            color = INVALID_EDGE_COLOR
        self.setPen(QPen(color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12.0)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_path()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.update_path()

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.update_path()

    def detach(self):
        self.source_port.remove_edge(self)
        if self.target_port is not None:
            self.target_port.remove_edge(self)
        self.source_port = None
        self.target_port = None
