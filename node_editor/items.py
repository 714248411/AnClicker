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

    def __init__(self, node_, direction_, link_kind_=None):
        super().__init__(node_)
        self.node = node_
        self.direction = direction_
        self.link_kind = link_kind_
        self.edges: list[EdgeItem] = []
        self.setAcceptHoverEvents(True)
        self.setToolTip("流程输入" if direction_ == "input" else "流程输出")
        if link_kind_ is not None:
            self.setToolTip("条件否（顶部输出）" if link_kind_ == 2 else "条件是（右侧输出）")
        self.setZValue(2.0)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event_):
        if event_.button() == Qt.MouseButton.LeftButton and self.scene() is not None:
            self.scene().begin_port_connection(self)
            event_.accept()
        else:
            super().mousePressEvent(event_)

    def mouseMoveEvent(self, event_):
        if self.scene() is not None:
            self.scene().update_port_connection(event_.scenePos())
            event_.accept()

    def mouseReleaseEvent(self, event_):
        if self.scene() is not None:
            self.scene().end_port_connection(event_.scenePos())
            event_.accept()

    def boundingRect(self):
        size_ = PORT_RADIUS * 2.0 + 4.0
        return QRectF(-size_ / 2.0, -size_ / 2.0, size_, size_)

    def paint(self, painter_, option_, widget_=None):
        del option_, widget_
        color_ = INPUT_PORT_COLOR if self.direction == "input" else OUTPUT_PORT_COLOR
        if self.link_kind == 2:
            color_ = QColor("#d69ad5")
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
        for edge_ in tuple(self.edges):
            edge_.update_path()


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
        control_kind_: str | None = None,
        subtitle_: str = "",
        note_: str = "",
        width_: float | None = None,
        height_: float | None = None,
    ):
        super().__init__()
        self.node_id = node_id_
        self.command_id = command_id_
        self.type_id = type_id_
        self.title = title_
        self.terminal_role = terminal_role_
        self.control_kind = control_kind_
        self.subtitle = str(subtitle_ or "")
        self.note = str(note_ or "")
        self.header_color = QColor(color_)
        self.title_font = QFont("Microsoft YaHei UI", 10, QFont.Weight.DemiBold)
        self.detail_font = QFont("Microsoft YaHei UI", 8)
        text_width_ = max(
            QFontMetricsF(self.title_font).horizontalAdvance(title_),
            QFontMetricsF(self.detail_font).horizontalAdvance(self.subtitle),
        )
        self.width = max(NODE_MIN_WIDTH, text_width_ + 34.0, float(width_ or 0.0))
        self.height = max(NODE_HEIGHT, float(height_ or 0.0))

        self.input_port: PortItem | None = None
        self.output_port: PortItem | None = None
        self.no_port: PortItem | None = None
        if terminal_role_ != "start":
            self.input_port = PortItem(self, "input")
            self.input_port.setPos(0.0, self.height / 2.0)
        if terminal_role_ != "end":
            self.output_port = PortItem(self, "output", 1 if type_id_ in {"条件判断", "颜色判断"} else None)
            self.output_port.setPos(self.width, self.height / 2.0)
        if type_id_ in {"条件判断", "颜色判断"}:
            self.no_port = PortItem(self, "output", 2)
            self.no_port.setPos(self.width / 2.0, 0.0)
        self._active_connection_port = None
        self._resizing = False
        self._hovered = False
        self._resize_origin = QPointF()
        self._resize_start_size = QPointF()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setZValue(1.0)

    @property
    def is_terminal(self) -> bool:
        return self.terminal_role in {"start", "end"}

    def boundingRect(self):
        margin_ = 12.0
        return QRectF(
            -margin_,
            -margin_,
            self.width + margin_ * 2.0,
            self.height + margin_ * 2.0 + (18.0 if self.note else 0.0),
        )

    def shape(self):
        path_ = QPainterPath()
        if self.control_kind == "condition":
            path_.moveTo(self.width / 2.0, 0.0)
            path_.lineTo(self.width, self.height / 2.0)
            path_.lineTo(self.width / 2.0, self.height)
            path_.lineTo(0.0, self.height / 2.0)
            path_.closeSubpath()
            return path_
        radius_ = self.height / 2.0 if self.is_terminal else 9.0
        path_.addRoundedRect(
            QRectF(0.0, 0.0, self.width, self.height), radius_, radius_
        )
        return path_

    def paint(self, painter_, option_, widget_=None):
        del option_, widget_
        painter_.setRenderHint(QPainter.RenderHint.Antialiasing)
        body_ = self.shape()
        if self._hovered:
            # Paint the halo first: the opaque body and text stay crisp above it.
            painter_.setBrush(Qt.BrushStyle.NoBrush)
            for width_, alpha_ in ((20, 12), (14, 22), (8, 42)):
                halo_ = QColor(NODE_SELECTED_COLOR)
                halo_.setAlpha(alpha_)
                painter_.setPen(QPen(halo_, width_))
                painter_.drawPath(body_)
        border_ = NODE_SELECTED_COLOR if self.isSelected() or self._hovered else NODE_BORDER_COLOR
        painter_.setPen(QPen(border_, 2.5 if self.isSelected() else 1.2))
        painter_.setBrush(QBrush(NODE_COLOR))
        painter_.drawPath(body_)
        if self._hovered:
            tint_ = QColor(NODE_SELECTED_COLOR)
            tint_.setAlpha(32)
            painter_.fillPath(body_, tint_)

        if self.control_kind == "condition":
            painter_.setPen(QPen(self.header_color, 3.0))
            painter_.drawPath(body_)
            if self.no_port is not None:
                painter_.setFont(self.detail_font)
                painter_.drawText(QRectF(self.width / 2 + 12, 0, 24, 18), "否")
                painter_.drawText(QRectF(self.width - 31, self.height / 2 - 20, 24, 18), "是")
        else:
            painter_.save()
            painter_.setClipPath(body_)
            painter_.fillRect(QRectF(0.0, 0.0, self.width, 4.0), self.header_color)
            painter_.restore()

        painter_.setPen(TEXT_COLOR)
        painter_.setFont(self.title_font)
        if self.is_terminal:
            painter_.drawText(
                QRectF(8.0, 4.0, self.width - 16.0, self.height - 8.0),
                Qt.AlignmentFlag.AlignCenter,
                self.title,
            )
        else:
            painter_.setFont(self.detail_font)
            painter_.setPen(QColor("#8b91a3"))
            painter_.drawText(QRectF(7.0, 3.0, 28.0, 14.0), f"#{self.command_id}")
            painter_.setPen(TEXT_COLOR)
            painter_.setFont(self.title_font)
            painter_.drawText(
                QRectF(12.0, 14.0, self.width - 24.0, 23.0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self.title,
            )
            painter_.setFont(self.detail_font)
            painter_.setPen(QColor("#aeb6c4"))
            painter_.drawText(
                QRectF(10.0, 37.0, self.width - 20.0, self.height - 42.0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self.subtitle,
            )
            painter_.setPen(QPen(QColor("#8b91a3"), 1.0))
            painter_.drawLine(
                QPointF(self.width - 12.0, self.height - 4.0),
                QPointF(self.width - 4.0, self.height - 4.0),
            )
            painter_.drawLine(
                QPointF(self.width - 4.0, self.height - 12.0),
                QPointF(self.width - 4.0, self.height - 4.0),
            )
            if self.note:
                painter_.setPen(QColor("#d69ad5"))
                painter_.drawText(
                    QRectF(0.0, self.height + 2.0, self.width, 18.0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    self.note,
                )

    def itemChange(self, change_, value_):
        if change_ == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.input_port is not None:
                self.input_port.update_edge()
            if self.output_port is not None:
                self.output_port.update_edge()
            if self.no_port is not None:
                self.no_port.update_edge()
            scene_ = self.scene()
            if scene_ is not None and hasattr(scene_, "node_position_changed"):
                scene_.node_position_changed(self)
        elif change_ == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change_, value_)

    def connection_port_at(self, position_):
        """Disjoint quarter-width/height hotspots; split corners diagonally."""
        x_, y_ = position_.x() / self.width, position_.y() / self.height
        if self.no_port is not None:
            candidates_ = []
            if y_ <= 0.25:
                candidates_.append((y_, 0, self.no_port))
            if x_ <= 0.25:
                candidates_.append((x_, 1, self.input_port))
            if x_ >= 0.75:
                candidates_.append((1 - x_, 2, self.output_port))
            return min(candidates_, key=lambda item_: item_[:2])[2] if candidates_ else None
        if x_ <= 0.2:
            return self.input_port
        if x_ >= 0.8:
            return self.output_port
        return None

    def mousePressEvent(self, event_):
        scene_ = self.scene()
        local_x_ = event_.pos().x()
        if (
            event_.button() == Qt.MouseButton.LeftButton
            and not self.is_terminal
            and local_x_ >= self.width - 16.0
            and event_.pos().y() >= self.height - 16.0
        ):
            self._resizing = True
            self._resize_origin = event_.scenePos()
            self._resize_start_size = QPointF(self.width, self.height)
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            event_.accept()
            return
        if event_.button() == Qt.MouseButton.LeftButton and scene_ is not None:
            port_ = self.connection_port_at(event_.pos())
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
        if self._resizing:
            delta_ = event_.scenePos() - self._resize_origin
            self.prepareGeometryChange()
            self.width = max(NODE_MIN_WIDTH, self._resize_start_size.x() + delta_.x())
            self.height = max(NODE_HEIGHT, self._resize_start_size.y() + delta_.y())
            if self.input_port is not None:
                self.input_port.setPos(0.0, self.height / 2.0)
                self.input_port.update_edge()
            if self.output_port is not None:
                self.output_port.setPos(self.width, self.height / 2.0)
                self.output_port.update_edge()
            if self.no_port is not None:
                self.no_port.setPos(self.width / 2.0, 0.0)
                self.no_port.update_edge()
            self.update()
            event_.accept()
            return
        if self._active_connection_port is not None and scene_ is not None:
            scene_.update_port_connection(event_.scenePos())
            event_.accept()
            return
        super().mouseMoveEvent(event_)

    def mouseReleaseEvent(self, event_):
        scene_ = self.scene()
        if self._resizing:
            self._resizing = False
            self.unsetCursor()
            if scene_ is not None and hasattr(scene_, "commit_node_size"):
                scene_.commit_node_size(self, self.width, self.height)
            event_.accept()
            return
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

    def hoverEnterEvent(self, event_):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event_)

    def hoverLeaveEvent(self, event_):
        self._hovered = False
        self.unsetCursor()
        self.update()
        super().hoverLeaveEvent(event_)

    def hoverMoveEvent(self, event_):
        if (
            not self.is_terminal
            and event_.pos().x() >= self.width - 16.0
            and event_.pos().y() >= self.height - 16.0
        ):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            if self.connection_port_at(event_.pos()) is not None:
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self.unsetCursor()
        super().hoverMoveEvent(event_)


class EdgeItem(QGraphicsPathItem):
    """A visual directed edge; ports may participate in multiple branches."""

    def __init__(self, source_node_: NodeItem, target_node_: NodeItem, link_kind_: int = 0):
        super().__init__()
        if source_node_.output_port is None or target_node_.input_port is None:
            raise ValueError("terminal ports cannot form this edge")
        self.source_node = source_node_
        self.target_node = target_node_
        self.source_port = (source_node_.no_port if link_kind_ == 2 and source_node_.no_port is not None
                            else source_node_.output_port)
        self.target_port = target_node_.input_port
        self.link_kind = int(link_kind_ or 0)
        self.source_port.edges.append(self)
        self.target_port.edges.append(self)
        self.setZValue(-1.0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.update_path()

    def update_path(self):
        start_ = self.source_port.scenePos()
        end_ = self.target_port.scenePos()
        candidates_ = self._route_candidates(start_, end_)
        direct_ = candidates_[0]
        path_ = direct_ if self._route_score(direct_) == direct_.length() else min(candidates_, key=self._route_score)
        self.setPath(path_)
        index_ = getattr(self.scene(), "_route_index", None)
        if index_ is not None:
            stroker_ = QPainterPathStroker()
            stroker_.setWidth(4.0)
            stroke_ = stroker_.createStroke(path_)
            index_.add(self, stroke_.boundingRect(), stroke_)
        branch_color_, _ = self._branch_style()
        color_ = (
            EDGE_SELECTED_COLOR
            if self.isSelected() or self.isUnderMouse()
            else branch_color_
        )
        self.setPen(
            QPen(
                color_,
                3.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )

    @staticmethod
    def _polyline(points_) -> QPainterPath:
        path_ = QPainterPath(points_[0])
        for point_ in points_[1:]:
            path_.lineTo(point_)
        return path_

    def _route_candidates(self, start_: QPointF, end_: QPointF) -> list[QPainterPath]:
        """Build several deterministic routes; scoring selects the clearest one."""
        direct_ = QPainterPath(start_)
        distance_ = max(abs(end_.x() - start_.x()) * 0.5, 60.0)
        direct_.cubicTo(
            QPointF(start_.x(), start_.y() - distance_) if self.source_port is self.source_node.no_port
            else QPointF(start_.x() + distance_, start_.y()),
            QPointF(end_.x() - distance_, end_.y()),
            end_,
        )
        if QLineF(start_, end_).length() <= STRAIGHT_EDGE_DISTANCE:
            direct_ = self._polyline((start_, end_))
        source_rect_ = self.source_node.sceneBoundingRect()
        target_rect_ = self.target_node.sceneBoundingRect()
        if end_.x() < start_.x() and target_rect_.top() > source_rect_.bottom() + 20:
            # Wrap a row of recorded steps through the empty inter-row lane.
            middle_y_ = (source_rect_.bottom() + target_rect_.top()) / 2
            direct_ = self._polyline((start_, QPointF(start_.x() + 26, start_.y()),
                                     QPointF(start_.x() + 26, middle_y_),
                                     QPointF(end_.x() - 26, middle_y_),
                                     QPointF(end_.x() - 26, end_.y()), end_))

        scene_ = self.scene()
        bounds_ = getattr(scene_, "_routing_bounds", None)
        if bounds_ is None:
            node_rects_ = [node_.sceneBoundingRect()
                           for node_ in getattr(scene_, "nodes_by_id", {}).values()]
            top_ = min((rect_.top() for rect_ in node_rects_), default=min(start_.y(), end_.y()))
            bottom_ = max((rect_.bottom() for rect_ in node_rects_), default=max(start_.y(), end_.y()))
        else:
            top_, bottom_ = bounds_
        try:
            lane_index_ = max(0, self.source_port.edges.index(self))
        except ValueError:
            lane_index_ = 0
        lane_gap_ = 34.0 + lane_index_ * 18.0
        start_x_ = start_.x() + 26.0
        end_x_ = end_.x() - 26.0
        middle_x_ = (start_x_ + end_x_) / 2.0
        candidates_ = [
            direct_,
            self._polyline(
                (start_, QPointF(middle_x_, start_.y()), QPointF(middle_x_, end_.y()), end_)
            ),
            self._polyline(
                (
                    start_, QPointF(start_x_, start_.y()), QPointF(start_x_, top_ - lane_gap_),
                    QPointF(end_x_, top_ - lane_gap_), QPointF(end_x_, end_.y()), end_,
                )
            ),
            self._polyline(
                (
                    start_, QPointF(start_x_, start_.y()), QPointF(start_x_, bottom_ + lane_gap_),
                    QPointF(end_x_, bottom_ + lane_gap_), QPointF(end_x_, end_.y()), end_,
                )
            ),
        ]
        if end_.y() < start_.y() - self.source_node.height:
            right_ = getattr(scene_, "_routing_right", None)
            if right_ is None:
                right_ = max((node_.sceneBoundingRect().right()
                              for node_ in getattr(scene_, "nodes_by_id", {}).values()), default=start_.x())
            right_ = max(right_, start_.x()) + lane_gap_
            below_source_ = self.source_node.sceneBoundingRect().bottom() + lane_gap_
            candidates_.append(self._polyline((start_, QPointF(start_x_, start_.y()),
                                               QPointF(start_x_, below_source_),
                                               QPointF(right_, below_source_), QPointF(right_, top_ - lane_gap_),
                                               QPointF(end_x_, top_ - lane_gap_),
                                               QPointF(end_x_, end_.y()), end_)))
        return candidates_

    def _route_score(self, path_: QPainterPath) -> float:
        scene_ = self.scene()
        node_hits_ = 0
        crossing_hits_ = 0
        stroker_ = QPainterPathStroker()
        stroker_.setWidth(4.0)
        route_shape_ = stroker_.createStroke(path_)
        if scene_ is not None:
            # Use Qt's spatial index rather than scanning every recorded node
            # and rebuilding every other edge stroke for each route candidate.
            index_ = getattr(scene_, "_route_index", None)
            nearby_ = (index_.items(route_shape_.boundingRect()) if index_ is not None
                       else scene_.items(route_shape_.boundingRect().adjusted(-10, -10, 10, 10)))
            for node_ in nearby_:
                if not isinstance(node_, NodeItem):
                    continue
                if node_ in {self.source_node, self.target_node}:
                    continue
                rect_ = (index_.records[node_][0] if index_ is not None
                         else node_.sceneBoundingRect().adjusted(-10, -10, 10, 10))
                if route_shape_.intersects(rect_):
                    node_hits_ += 1
            for other_ in nearby_:
                if other_ is self or not isinstance(other_, EdgeItem):
                    continue
                if {
                    self.source_node, self.target_node
                } & {other_.source_node, other_.target_node}:
                    continue
                other_stroke_ = (index_.records[other_][1] if index_ is not None
                                 else stroker_.createStroke(other_.path()))
                if route_shape_.intersects(other_stroke_):
                    crossing_hits_ += 1
        # Node overlap is always worse than a longer detour.  Crossings are
        # the next priority, then path length keeps unobstructed routes tidy.
        return node_hits_ * 1_000_000.0 + crossing_hits_ * 10_000.0 + path_.length()

    def paint(self, painter_, option_, widget_=None):
        super().paint(painter_, option_, widget_)
        end_ = self.path().pointAtPercent(1.0)
        before_ = self.path().pointAtPercent(0.96)
        angle_ = math.atan2(end_.y() - before_.y(), end_.x() - before_.x())
        size_ = 16.0
        left_ = QPointF(
            end_.x() - size_ * math.cos(angle_ - math.pi / 6.0),
            end_.y() - size_ * math.sin(angle_ - math.pi / 6.0),
        )
        right_ = QPointF(
            end_.x() - size_ * math.cos(angle_ + math.pi / 6.0),
            end_.y() - size_ * math.sin(angle_ + math.pi / 6.0),
        )
        branch_color_, branch_label_ = self._branch_style()
        color_ = EDGE_SELECTED_COLOR if self.isSelected() else branch_color_
        painter_.setPen(QPen(color_, 1.0))
        painter_.setBrush(QBrush(color_))
        painter_.drawPolygon(QPolygonF([end_, left_, right_]))
        if branch_label_:
            label_position_ = self.path().pointAtPercent(0.58)
            painter_.setPen(QPen(color_, 1.0))
            painter_.setFont(QFont("Microsoft YaHei UI", 9, QFont.Weight.DemiBold))
            painter_.drawText(label_position_ + QPointF(6.0, -6.0), branch_label_)

    def _branch_style(self):
        if self.link_kind == 1:
            return QColor("#7c8cff"), "是"
        if self.link_kind == 2:
            return QColor("#d69ad5"), "否"
        if self.link_kind == 3:
            return QColor("#6ea8fe"), "循环体"
        if self.link_kind == 4:
            return QColor("#a98eda"), "完成"
        try:
            branch_index_ = self.source_port.edges.index(self)
        except ValueError:
            branch_index_ = -1
        if self.source_node.type_id in {"条件判断", "颜色判断"}:
            return (
                (QColor("#7c8cff"), "是")
                if branch_index_ == 0
                else (QColor("#d69ad5"), "否")
            )
        if self.source_node.type_id in {"循环", "条件循环"}:
            return (
                (QColor("#6ea8fe"), "循环体")
                if branch_index_ == 0
                else (QColor("#a98eda"), "完成")
            )
        return QColor(EDGE_COLOR), ""

    def boundingRect(self):
        return super().boundingRect().adjusted(-20.0, -20.0, 20.0, 20.0)

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
        if self in self.source_port.edges:
            self.source_port.edges.remove(self)
        if self in self.target_port.edges:
            self.target_port.edges.remove(self)
