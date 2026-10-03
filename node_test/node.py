from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject

from node_test.style import (
    INPUT_PORT_COLOR,
    NODE_BORDER_COLOR,
    NODE_COLOR,
    NODE_HEIGHT,
    NODE_MIN_WIDTH,
    NODE_SELECTED_COLOR,
    OUTPUT_PORT_COLOR,
    PORT_RADIUS,
    PORT_TYPE_COLORS,
    TEXT_COLOR,
)


class PortItem(QGraphicsObject):
    """A connection endpoint owned by a node."""

    def __init__(self, node, name, direction):
        super().__init__(node)
        self.node = node
        self.name = name
        self.direction = direction
        self.edges = []
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setToolTip(name)

    def boundingRect(self):
        size = PORT_RADIUS * 2.0 + 4.0
        return QRectF(-size / 2.0, -size / 2.0, size, size)

    def paint(self, painter, option, widget=None):
        del option, widget
        color = self.display_color()
        if self.isUnderMouse():
            color = color.lighter(135)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#10141b"), 2.0))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QRectF(-PORT_RADIUS, -PORT_RADIUS, PORT_RADIUS * 2, PORT_RADIUS * 2))

    def hoverEnterEvent(self, event):
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.update()
        super().hoverLeaveEvent(event)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def update_edges(self):
        for edge in list(self.edges):
            edge.update_path()

    def has_connection(self):
        return bool(self.edges)

    def display_color(self):
        fallback_color = INPUT_PORT_COLOR if self.direction == "input" else OUTPUT_PORT_COLOR
        return PORT_TYPE_COLORS.get(self.name, fallback_color)


class NodeItem(QGraphicsObject):
    """Movable node containing labeled input and output ports."""

    def __init__(self, title, definition):
        super().__init__()
        self.title = title
        self.definition = definition
        self.input_ports = []
        self.output_ports = []
        self.header_color = definition["color"]
        self.title_font = QFont("Microsoft YaHei UI", 10, QFont.Weight.DemiBold)
        title_width = QFontMetricsF(self.title_font).horizontalAdvance(title)
        self.width = max(NODE_MIN_WIDTH, title_width + 30.0)
        self.height = NODE_HEIGHT
        self.is_terminal = title in ("开始", "结束")

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setZValue(1)

        self._create_ports(definition["inputs"], "input")
        self._create_ports(definition["outputs"], "output")

    def _create_ports(self, names, direction):
        ports = self.input_ports if direction == "input" else self.output_ports
        for index, name in enumerate(names):
            port = PortItem(self, name, direction)
            x = self.width * (index + 1) / (len(names) + 1)
            y = 0.0 if direction == "input" else self.height
            port.setPos(x, y)
            ports.append(port)

    def boundingRect(self):
        margin = 4.0
        return QRectF(-margin, -margin, self.width + margin * 2, self.height + margin * 2)

    def shape(self):
        path = QPainterPath()
        radius = self.height / 2.0 if self.is_terminal else 9.0
        path.addRoundedRect(QRectF(0.0, 0.0, self.width, self.height), radius, radius)
        return path

    def paint(self, painter, option, widget=None):
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QPainterPath()
        radius = self.height / 2.0 if self.is_terminal else 9.0
        body.addRoundedRect(QRectF(0.0, 0.0, self.width, self.height), radius, radius)
        border = NODE_SELECTED_COLOR if self.isSelected() else NODE_BORDER_COLOR
        painter.setPen(QPen(border, 2.5 if self.isSelected() else 1.2))
        painter.setBrush(QBrush(NODE_COLOR))
        painter.drawPath(body)

        painter.save()
        painter.setClipPath(body)
        painter.fillRect(QRectF(0.0, 0.0, self.width, 4.0), self.header_color)
        painter.restore()

        painter.setPen(TEXT_COLOR)
        painter.setFont(self.title_font)
        painter.drawText(
            QRectF(8.0, 4.0, self.width - 16.0, self.height - 4.0),
            Qt.AlignmentFlag.AlignCenter,
            self.title,
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.input_ports + self.output_ports:
                port.update_edges()
            scene = self.scene()
            if scene is not None and hasattr(scene, "auto_connect_nearby_ports"):
                scene.auto_connect_nearby_ports(self)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)

    def all_edges(self):
        edges = []
        for port in self.input_ports + self.output_ports:
            for edge in port.edges:
                if edge not in edges:
                    edges.append(edge)
        return edges
