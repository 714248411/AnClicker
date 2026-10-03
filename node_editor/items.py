"""Graphics items used by the embeddable instruction editor."""

from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem

from node_editor.style import (
    EDGE_COLOR,
    EDGE_SELECTED_COLOR,
    INPUT_PORT_COLOR,
    NODE_BORDER_COLOR,
    NODE_COLOR,
    NODE_HEIGHT,
    NODE_MIN_WIDTH,
    NODE_SELECTED_COLOR,
    OUTPUT_PORT_COLOR,
    PORT_RADIUS,
    STRAIGHT_EDGE_DISTANCE,
    TEXT_COLOR,
)


class PortItem(QGraphicsObject):
    """A single flow endpoint owned by a node."""

    def __init__(self, node_, direction_):
        super().__init__(node_)
        self.node = node_
        self.direction = direction_
        self.edge: EdgeItem | None = None
        self.setAcceptHoverEvents(True)
        self.setToolTip("流程输入" if direction_ == "input" else "流程输出")

    def boundingRect(self):
        size_ = PORT_RADIUS * 2.0 + 4.0
        return QRectF(-size_ / 2.0, -size_ / 2.0, size_, size_)

    def paint(self, painter_, option_, widget_=None):
        del option_, widget_
        color_ = INPUT_PORT_COLOR if self.direction == "input" else OUTPUT_PORT_COLOR
        if self.isUnderMouse():
            color_ = color_.lighter(135)
        painter_.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter_.setPen(QPen(QColor("#10141b"), 2.0))
        painter_.setBrush(QBrush(color_))
        painter_.drawEllipse(
            QRectF(-PORT_RADIUS, -PORT_RADIUS, PORT_RADIUS * 2, PORT_RADIUS * 2)
        )

    def hoverEnterEvent(self, event_):
        self.update()
        super().hoverEnterEvent(event_)

    def hoverLeaveEvent(self, event_):
        self.update()
        super().hoverLeaveEvent(event_)

    def update_edge(self):
        if self.edge is not None:
            self.edge.update_path()


class NodeItem(QGraphicsObject):
    """Movable instruction or fixed-role terminal node."""

    def __init__(
        self,
        node_id_,
        command_id_,
        type_id_: str,
        title_: str,
        color_: QColor,
        terminal_role_: str | None = None,
    ):
        super().__init__()
        self.node_id = node_id_
        self.command_id = command_id_
        self.type_id = type_id_
        self.title = title_
        self.terminal_role = terminal_role_
        self.header_color = QColor(color_)
        self.title_font = QFont("Microsoft YaHei UI", 10, QFont.Weight.DemiBold)
        title_width_ = QFontMetricsF(self.title_font).horizontalAdvance(title_)
        self.width = max(NODE_MIN_WIDTH, title_width_ + 30.0)
        self.height = NODE_HEIGHT

        self.input_port: PortItem | None = None
        self.output_port: PortItem | None = None
        if terminal_role_ != "start":
            self.input_port = PortItem(self, "input")
            self.input_port.setPos(0.0, self.height / 2.0)
        if terminal_role_ != "end":
            self.output_port = PortItem(self, "output")
            self.output_port.setPos(self.width, self.height / 2.0)
        self._active_connection_port = None

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(1.0)

    @property
    def is_terminal(self) -> bool:
        return self.terminal_role in {"start", "end"}

    def boundingRect(self):
        margin_ = 4.0
        return QRectF(
            -margin_,
            -margin_,
            self.width + margin_ * 2.0,
            self.height + margin_ * 2.0,
        )

    def shape(self):
        path_ = QPainterPath()
        radius_ = self.height / 2.0 if self.is_terminal else 9.0
        path_.addRoundedRect(
            QRectF(0.0, 0.0, self.width, self.height), radius_, radius_
        )
        return path_

    def paint(self, painter_, option_, widget_=None):
        del option_, widget_
        painter_.setRenderHint(QPainter.RenderHint.Antialiasing)
        body_ = self.shape()
        border_ = NODE_SELECTED_COLOR if self.isSelected() else NODE_BORDER_COLOR
        painter_.setPen(QPen(border_, 2.5 if self.isSelected() else 1.2))
        painter_.setBrush(QBrush(NODE_COLOR))
        painter_.drawPath(body_)

        painter_.save()
        painter_.setClipPath(body_)
        painter_.fillRect(QRectF(0.0, 0.0, self.width, 4.0), self.header_color)
        painter_.restore()

        painter_.setPen(TEXT_COLOR)
        painter_.setFont(self.title_font)
        painter_.drawText(
            QRectF(8.0, 4.0, self.width - 16.0, self.height - 4.0),
            Qt.AlignmentFlag.AlignCenter,
            self.title,
        )

    def itemChange(self, change_, value_):
        if change_ == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.input_port is not None:
                self.input_port.update_edge()
            if self.output_port is not None:
                self.output_port.update_edge()
            scene_ = self.scene()
            if scene_ is not None and hasattr(scene_, "node_position_changed"):
                scene_.node_position_changed(self)
        elif change_ == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change_, value_)

    def mousePressEvent(self, event_):
        scene_ = self.scene()
        local_x_ = event_.pos().x()
        if event_.button() == Qt.MouseButton.LeftButton and scene_ is not None:
            port_ = None
            if local_x_ <= self.width * 0.2 and self.input_port is not None:
                port_ = self.input_port
            elif local_x_ >= self.width * 0.8 and self.output_port is not None:
                port_ = self.output_port
            if port_ is not None and hasattr(scene_, "begin_port_connection"):
                self._active_connection_port = port_
                scene_.begin_port_connection(port_)
                event_.accept()
                return
        if (
            event_.button() == Qt.MouseButton.LeftButton
            and scene_ is not None
            and hasattr(scene_, "begin_node_drag")
        ):
            scene_.begin_node_drag(self)
        super().mousePressEvent(event_)

    def mouseMoveEvent(self, event_):
        scene_ = self.scene()
        if self._active_connection_port is not None and scene_ is not None:
            scene_.update_port_connection(event_.scenePos())
            event_.accept()
            return
        super().mouseMoveEvent(event_)

    def mouseReleaseEvent(self, event_):
        scene_ = self.scene()
        if self._active_connection_port is not None and scene_ is not None:
            self._active_connection_port = None
            scene_.end_port_connection(event_.scenePos())
            event_.accept()
            return
        super().mouseReleaseEvent(event_)
        scene_ = self.scene()
        if (
            event_.button() == Qt.MouseButton.LeftButton
            and scene_ is not None
            and hasattr(scene_, "end_node_drag")
        ):
            scene_.end_node_drag(self)

    def mouseDoubleClickEvent(self, event_):
        if not self.is_terminal:
            scene_ = self.scene()
            if scene_ is not None and hasattr(scene_, "activate_node"):
                scene_.activate_node(self)
            event_.accept()
            return
        super().mouseDoubleClickEvent(event_)


class EdgeItem(QGraphicsPathItem):
    """A visual edge in the validated single instruction chain."""

    def __init__(self, source_node_: NodeItem, target_node_: NodeItem):
        super().__init__()
        if source_node_.output_port is None or target_node_.input_port is None:
            raise ValueError("terminal ports cannot form this edge")
        self.source_node = source_node_
        self.target_node = target_node_
        self.source_port = source_node_.output_port
        self.target_port = target_node_.input_port
        self.source_port.edge = self
        self.target_port.edge = self
        self.setZValue(-1.0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.update_path()

    def update_path(self):
        start_ = self.source_port.scenePos()
        end_ = self.target_port.scenePos()
        path_ = QPainterPath(start_)
        if QLineF(start_, end_).length() <= STRAIGHT_EDGE_DISTANCE:
            path_.lineTo(end_)
        else:
            distance_ = max(abs(end_.x() - start_.x()) * 0.5, 60.0)
            path_.cubicTo(
                QPointF(start_.x() + distance_, start_.y()),
                QPointF(end_.x() - distance_, end_.y()),
                end_,
            )
        self.setPath(path_)
        color_ = EDGE_SELECTED_COLOR if self.isSelected() or self.isUnderMouse() else EDGE_COLOR
        self.setPen(
            QPen(
                color_,
                3.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )

    def paint(self, painter_, option_, widget_=None):
        super().paint(painter_, option_, widget_)
        end_ = self.path().pointAtPercent(1.0)
        before_ = self.path().pointAtPercent(0.96)
        angle_ = math.atan2(end_.y() - before_.y(), end_.x() - before_.x())
        size_ = 10.0
        left_ = QPointF(
            end_.x() - size_ * math.cos(angle_ - math.pi / 6.0),
            end_.y() - size_ * math.sin(angle_ - math.pi / 6.0),
        )
        right_ = QPointF(
            end_.x() - size_ * math.cos(angle_ + math.pi / 6.0),
            end_.y() - size_ * math.sin(angle_ + math.pi / 6.0),
        )
        color_ = EDGE_SELECTED_COLOR if self.isSelected() else EDGE_COLOR
        painter_.setPen(QPen(color_, 1.0))
        painter_.setBrush(QBrush(color_))
        painter_.drawPolygon(QPolygonF([end_, left_, right_]))

    def shape(self):
        stroker_ = QPainterPathStroker()
        stroker_.setWidth(12.0)
        return stroker_.createStroke(self.path())

    def itemChange(self, change_, value_):
        if change_ == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_path()
        return super().itemChange(change_, value_)

    def hoverEnterEvent(self, event_):
        super().hoverEnterEvent(event_)
        self.update_path()

    def hoverLeaveEvent(self, event_):
        super().hoverLeaveEvent(event_)
        self.update_path()

    def detach(self):
        if self.source_port.edge is self:
            self.source_port.edge = None
        if self.target_port.edge is self:
            self.target_port.edge = None
