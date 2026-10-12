"""Viewport-space cut gesture and bounded, transient feedback (no scene items)."""
from time import monotonic
import math

from qt_compat.QtCore import QObject, QPointF, Qt, QTimer
from qt_compat.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen
from qt_compat.QtWidgets import QApplication

class ConnectionCutter(QObject):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.active = False
        self.dragged = False
        self.points = []
        self.hits = {}
        self.candidates = []
        self.blockers = QPainterPath()
        self.flashes = []
        self.started = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)

    def begin(self, position):
        self.cancel()
        self.active = True
        self.points = [QPointF(position)]
        for node in getattr(self.view.scene(), 'nodes_by_id', {}).values():
            if node.isVisible():
                body = self.view.viewportTransform().map(node.mapToScene(node.shape()))
                self.blockers = self.blockers.united(body)
        # Copy paths rather than retaining graphics items: the host reloads the
        # graph after a deletion. Geometry and hit tolerance are in screen pixels.
        self.candidates = [
            ((edge.source_node.node_id, edge.target_node.node_id),
             self.view.viewportTransform().map(edge.mapToScene(edge.path())))
            for edge in getattr(self.view.scene(), 'edges', ()) if edge.isVisible()
        ]

    def move(self, position):
        if not self.active:
            return
        point = QPointF(position)
        if not self.dragged:
            delta = point - self.points[0]
            if abs(delta.x()) + abs(delta.y()) < QApplication.startDragDistance():
                return
            self.dragged = True
            self.view.setCursor(Qt.CursorShape.CrossCursor)
        segment = QPainterPath(self.points[-1])
        segment.lineTo(point)
        stroker = QPainterPathStroker()
        stroker.setWidth(5.0)
        # Do not cut an invisible portion of an edge hidden behind a node.
        swept = stroker.createStroke(segment).subtracted(self.blockers)
        for pair, path in self.candidates:
            if pair not in self.hits and swept.intersects(path):
                self.hits[pair] = QPainterPath(path)
        self.points.append(point)
        self.points = self.points[-160:]
        self.view.viewport().update()

    def finish(self, position):
        self.move(position)
        dragged, pairs = self.dragged, list(self.hits)
        if dragged:
            self.flashes = list(self.points)
            self.started = monotonic()
            self.timer.start()
        self.active = False
        self.points = []
        self.hits = {}
        self.candidates = []
        self.blockers = QPainterPath()
        self.view.unsetCursor()
        self.view.viewport().update()
        return dragged, pairs

    def cancel(self):
        self.active = self.dragged = False
        self.points = []
        self.hits = {}
        self.candidates = []
        self.blockers = QPainterPath()
        self.flashes = []
        self.timer.stop()
        self.view.unsetCursor()
        self.view.viewport().update()

    def tick(self):
        if monotonic() - self.started >= .32:
            self.flashes = []
            self.timer.stop()
        self.view.viewport().update()

    @staticmethod
    def trail(points):
        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        return path

    def paint(self, painter):
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.save()
        clip = QPainterPath()
        from qt_compat.QtCore import QRectF
        clip.addRect(QRectF(self.view.viewport().rect()))
        painter.setClipPath(clip.subtracted(self.blockers))
        for path in self.hits.values():
            painter.setPen(QPen(QColor(255, 125, 83, 60), 10))
            painter.drawPath(path)
            painter.setPen(QPen(QColor('#ed875d'), 2))
            painter.drawPath(path)
        painter.restore()
        points = self.points if self.active and self.dragged else self.flashes
        if len(points) >= 2:
            opacity = 1.0 if self.active else max(0, 1-(monotonic()-self.started)/.32)
            path = self.trail(points)
            for width, alpha in ((14, 25), (7, 60), (2, 240)):
                pen = QPen(QColor(85, 165, 255, round(alpha*opacity)), width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)
            # Small radial spark; no particles or timers accumulate in the scene.
            tip = points[-1]
            radius = 5 if self.active else 5 + 16*(1-opacity)
            painter.setPen(QPen(QColor(130, 190, 255, round(200*opacity)), 1.5))
            for index in range(8):
                angle = index*math.pi/4
                direction = QPointF(math.cos(angle), math.sin(angle))
                painter.drawLine(tip+direction*radius, tip+direction*(radius+4))
        painter.restore()
