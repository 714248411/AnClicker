from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QPainter
from PySide6.QtWidgets import QAbstractItemView, QGraphicsView, QTreeWidget


NODE_MIME_TYPE = "application/x-clicker-node-type"


class NodePalette(QTreeWidget):
    nodeActivated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start = QPoint()
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._activate_item)

    def _activate_item(self, item, column):
        del column
        node_type = item.data(0, Qt.ItemDataRole.UserRole)
        if node_type:
            self.nodeActivated.emit(node_type)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return super().mouseMoveEvent(event)
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 8:
            return super().mouseMoveEvent(event)

        item = self.currentItem()
        node_type = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        if not node_type:
            return super().mouseMoveEvent(event)

        mime_data = QMimeData()
        mime_data.setData(NODE_MIME_TYPE, node_type.encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


class NodeView(QGraphicsView):
    zoomChanged = Signal(int)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = QPoint()
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

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        new_zoom = self._zoom * factor
        clamped_zoom = max(0.2, min(new_zoom, 1.0))
        if clamped_zoom != self._zoom:
            self.scale(clamped_zoom / self._zoom, clamped_zoom / self._zoom)
            self._zoom = clamped_zoom
            self.zoomChanged.emit(round(self._zoom * 100))
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            current = event.position().toPoint()
            delta = current - self._pan_start
            self._pan_start = current
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self._panning:
            self._panning = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(NODE_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(NODE_MIME_TYPE):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(NODE_MIME_TYPE):
            node_type = bytes(event.mimeData().data(NODE_MIME_TYPE)).decode("utf-8")
            position = self.mapToScene(event.position().toPoint())
            self.scene().add_node(node_type, position)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def fit_graph(self):
        self.fitInView(self.scene().graph_items_rect(), Qt.AspectRatioMode.KeepAspectRatio)
        fitted_zoom = self.transform().m11()
        self._zoom = max(0.2, min(fitted_zoom, 1.0))
        if fitted_zoom != self._zoom:
            self.scale(self._zoom / fitted_zoom, self._zoom / fitted_zoom)
        self.zoomChanged.emit(round(self._zoom * 100))
