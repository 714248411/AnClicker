from unittest.mock import Mock, patch
import pytest
from qt_compat.QtCore import QPoint, QRectF
from qt_compat.QtGui import QContextMenuEvent, QTransform, QFont
from qt_compat.QtWidgets import QApplication
from test.test_cad_canvas import canvas
from test.test_hidden_stop import host


@pytest.fixture
def error_flow(canvas):
    scene, view = canvas
    scene.load_graph([{'id': 1, 'type_id': '时间等待', 'x': 0, 'y': 0},
                      {'id': 2, 'type_id': '报错跳转', 'x': 400, 'y': 200},
                      {'id': 3, 'type_id': '时间等待', 'x': 800, 'y': 0}],
                     [{'source': 1, 'target': 2, 'kind': 5}, {'source': 2, 'target': 3, 'kind': 6}], {}, allow_incomplete=True)
    view.fit_graph()
    QApplication.processEvents()
    return scene, view


def test_error_lines_alone_have_orange_train_arrows_even_when_selected(error_flow):
    scene, view = error_flow
    assert {edge.link_kind for edge in scene.flow_arrow_edges} == {5, 6}
    view.play_run_animation()
    assert view._arrow_timer.isActive()
    for edge in scene.edges:
        edge.setSelected(True)
    painter = Mock()
    painter.worldTransform.return_value = view.viewportTransform()
    view._draw_flow_arrows(painter, QRectF(view.viewport().rect()))
    assert painter.drawPath.call_count == 2
    colors = [call.args[0].color() for call in painter.setPen.call_args_list]
    assert all(color.red() > color.green() > color.blue() for color in colors)


def test_hiding_arrows_removes_heads_and_trains_and_never_restarts_five_seconds(error_flow):
    scene, view = error_flow
    changes = []
    view.arrowsVisibilityChanged.connect(changes.append)
    assert view.arrows_visible and scene.arrows_visible
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        view.set_arrows_visible(False)
        assert not view._arrow_timer.isActive() and not scene.arrows_visible
        painter = Mock()
        painter.font.return_value = QFont()
        view._draw_flow_arrows(painter, QRectF())
        painter.save.assert_not_called()
        for edge in scene.edges:
            edge.paint(painter, None)
        painter.drawPolygon.assert_not_called()
        assert painter.drawPath.call_count == len(scene.edges)
        clock.return_value = 102
        view.set_arrows_visible(True)
        assert view._arrow_timer.isActive() and view._arrow_run_until == 105
        view.set_arrows_visible(False)
        clock.return_value = 110
        view.set_arrows_visible(True)
        assert not view._arrow_timer.isActive() and view._arrow_elapsed() == 5
    assert changes == [False, True, False, True]


def test_hidden_arrow_setting_survives_scene_reload_and_preserves_continuous_mode(error_flow):
    scene, view = error_flow
    view.set_continuous_animation(True)
    view.set_arrows_visible(False)
    scene.load_graph([{'id': 1, 'type_id': '循环', 'x': 0, 'y': 0}], [], {})
    assert not scene.arrows_visible and not view._arrow_timer.isActive()
    assert view.continuous_animation
    view.set_arrows_visible(True)
    assert view._arrow_timer.isActive() and view.continuous_animation


def test_blank_menu_has_independent_arrow_and_animation_switches(error_flow):
    scene, view = error_flow
    point = QPoint(5, 5)
    assert view.itemAt(point) is None
    def choose(menu, position):
        actions = {a.text(): a for a in menu.actions()}
        assert {'打开箭头', '关闭箭头', '打开持续动画', '关闭持续动画'} <= actions.keys()
        assert actions['打开箭头'].isEnabled() != actions['关闭箭头'].isEnabled()
        action = actions['关闭箭头' if view.arrows_visible else '打开箭头']
        assert action.isEnabled()
        action.trigger()
        return action
    with patch('node_editor.view.QMenu.exec', choose):
        event = QContextMenuEvent(QContextMenuEvent.Mouse, point, view.mapToGlobal(point))
        view.contextMenuEvent(event)
        assert not view.arrows_visible and not view.continuous_animation
        view.contextMenuEvent(event)
        assert view.arrows_visible and not view.continuous_animation


def test_arrow_visibility_preference_saved_and_restored(host):
    view = host.workspace.editor.view
    assert view.arrows_visible
    view.set_arrows_visible(False)
    assert host.db.get_setting_value('流程图显示箭头') == 'False'
    from Start_Win import Main_window
    reopened = Main_window()
    try:
        assert not reopened.workspace.editor.view.arrows_visible
        assert not reopened.workspace.editor.scene.arrows_visible
        reopened.workspace.editor.view.set_arrows_visible(True)
        assert host.db.get_setting_value('流程图显示箭头') == 'True'
    finally:
        reopened.hide(); reopened.deleteLater(); QApplication.processEvents()
        view.set_arrows_visible(True)
