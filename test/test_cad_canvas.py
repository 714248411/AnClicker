import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from qt_compat.QtCore import QPointF, QRectF
from qt_compat.QtWidgets import QApplication
from node_editor.scene import NodeScene
from node_editor.view import NodeView


@pytest.fixture
def canvas():
    app = QApplication.instance() or QApplication([])
    scene = NodeScene()
    view = NodeView(scene)
    view.resize(900, 600)
    view.show()
    app.processEvents()
    yield scene, view
    view.close()
    view.deleteLater()
    app.processEvents()


def test_fit_large_graph_includes_far_coordinates(canvas):
    scene, view = canvas
    bounds = QRectF(-250000, -100000, 500000, 200000)
    scene.addRect(bounds)
    scene.graph_items_rect = lambda: bounds.adjusted(-80, -80, 80, 80)
    view.fit_graph()
    visible = view.mapToScene(view.viewport().rect()).boundingRect()
    assert visible.contains(bounds)
    assert view._zoom < .01


@pytest.mark.parametrize('zoom', [.000001, .001, .05, 1, 8, 64])
def test_zoom_renders_and_returns_to_readable_scale(canvas, zoom):
    scene, view = canvas
    view._set_zoom(zoom)
    assert view._zoom == zoom
    assert not view.grab().isNull()
    view._set_zoom(1)
    assert view.transform().m11() == pytest.approx(1)
    assert view.sceneRect().width() <= 10000


def test_mouse_anchor_stays_in_place(canvas):
    scene, view = canvas
    anchor = QPointF(170, 120)
    before = view.mapToScene(anchor.toPoint())
    view._set_zoom(8, anchor)
    after = view.mapFromScene(before)
    assert abs(after.x() - anchor.x()) <= 2
    assert abs(after.y() - anchor.y()) <= 2


def test_canvas_expands_beyond_old_border(canvas):
    scene, view = canvas
    view._expand_canvas(QPointF(50000, -50000), 1)
    view.centerOn(50000, -50000)
    center = view.mapToScene(view.viewport().rect().center())
    assert abs(center.x()-50000) <= 2
    assert abs(center.y()+50000) <= 2
