from unittest.mock import patch
import pytest
from qt_compat.QtCore import QPoint
from qt_compat.QtGui import QContextMenuEvent
from qt_compat.QtWidgets import QApplication
from test.test_cad_canvas import canvas
from test.test_hidden_stop import host


@pytest.fixture
def flow(canvas):
    scene, view = canvas
    scene.load_graph([{'id':1,'type_id':'循环','x':0,'y':0},
                      {'id':2,'type_id':'时间等待','x':400,'y':0}], [], {})
    view.fit_graph()
    QApplication.processEvents()
    return scene, view


def test_default_static_then_run_plays_exactly_five_seconds_and_can_restart(flow):
    scene, view = flow
    assert not view.continuous_animation and not view._arrow_timer.isActive()
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        assert view._arrow_timer.isActive() and view._arrow_elapsed() == 0
        assert view.arrows_visible and scene.arrows_visible
        clock.return_value = 104.999
        view._advance_flow_arrows()
        assert view._arrow_timer.isActive() and view._arrow_elapsed() == pytest.approx(4.999)
        clock.return_value = 105
        view._advance_flow_arrows()
        assert not view._arrow_timer.isActive() and view._arrow_elapsed() == 5
        assert not view.arrows_visible and not scene.arrows_visible
        assert not view._arrow_preview_timer.isActive()
        clock.return_value = 130
        scene.emit_graph_changed()
        view._set_zoom(2)
        assert not view._arrow_timer.isActive() and view._arrow_elapsed() == 5
        view.play_run_animation()
        assert view._arrow_timer.isActive() and view._arrow_run_until == 135
        assert view._arrow_elapsed() == 0
        assert view.arrows_visible and scene.arrows_visible


def test_expired_arrows_stay_hidden_during_repaint_zoom_and_graph_reload(flow):
    scene, view = flow
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        clock.return_value = 106
        view._advance_flow_arrows()
        from node_editor.flow_arrows import moving_arrows
        with patch('node_editor.view.moving_arrows', wraps=moving_arrows) as draw:
            view.grab()
            draw.assert_not_called()
            assert not scene.arrows_visible
            clock.return_value = 200
            view._set_zoom(1)
            view.grab()
            draw.assert_not_called()
            scene.emit_graph_changed()
            assert not view.arrows_visible and not scene.arrows_visible


def test_hidden_view_never_gets_an_extra_five_seconds_on_return(flow):
    scene, view = flow
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.hide()
        view.play_run_animation()
        assert not view._arrow_timer.isActive()
        clock.return_value = 104
        view.show()
        assert view._arrow_timer.isActive()
        view.hide()
        clock.return_value = 106
        view.show()
        assert not view._arrow_timer.isActive() and view._arrow_elapsed() == 5
        assert not view.arrows_visible and not scene.arrows_visible


def test_continuous_mode_runs_beyond_five_seconds_and_disable_stops_immediately(flow):
    scene, view = flow
    changes = []
    view.continuousAnimationChanged.connect(changes.append)
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.set_continuous_animation(True)
        clock.return_value = 112.5
        view._advance_flow_arrows()
        assert view._arrow_timer.isActive() and view._arrow_elapsed() == 12.5
        view.play_run_animation()
        assert view._arrow_elapsed() == 12.5  # A run must not reset continuous motion.
        view.set_continuous_animation(False)
        assert not view._arrow_timer.isActive()
        clock.return_value = 140
        view._sync_flow_arrows()
        assert not view._arrow_timer.isActive() and view._arrow_elapsed() == 12.5
        view.play_run_animation()
        assert view._arrow_run_until == 145 and view._arrow_timer.isActive()
    assert changes == [True, False]


def test_blank_context_menu_has_both_animation_actions_and_switches_modes(flow):
    scene, view = flow
    point = QPoint(5, 5)
    assert view.itemAt(point) is None
    def choose(menu, position):
        actions = {action.text(): action for action in menu.actions()}
        enable, disable = actions['打开持续动画'], actions['关闭持续动画']
        assert enable.isEnabled() != disable.isEnabled()
        action = disable if view.continuous_animation else enable
        assert action.isEnabled()
        action.trigger()
        return action
    with patch('node_editor.view.QMenu.exec', choose):
        event = QContextMenuEvent(QContextMenuEvent.Mouse, point, view.viewport().mapToGlobal(point))
        view.contextMenuEvent(event)
        assert view.continuous_animation and view._arrow_timer.isActive()
        view.contextMenuEvent(event)
        assert not view.continuous_animation and not view._arrow_timer.isActive()


def test_real_worker_start_signal_triggers_preview_once_not_each_instruction(host):
    view = host.workspace.editor.view
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        assert view._arrow_run_until == 0
        host.command_thread.started.emit()
        QApplication.processEvents()
        assert view._arrow_run_until == 105
        clock.return_value = 103
        command = host.workspace.repository.list_commands()[0]
        host.command_thread.send_type_and_id.emit(command.type_id, str(command.id))
        QApplication.processEvents()
        assert view._arrow_run_until == 105
        host.command_thread.started.emit()
        QApplication.processEvents()
        assert view._arrow_run_until == 108


def test_continuous_preference_is_saved_and_restored_in_main_window(host):
    view = host.workspace.editor.view
    assert not view.continuous_animation
    view.set_continuous_animation(True)
    assert host.db.get_setting_value('流程图持续动画') == 'True'
    from Start_Win import Main_window
    reopened = Main_window()
    try:
        assert reopened.workspace.editor.view.continuous_animation
        reopened.workspace.editor.view.set_continuous_animation(False)
        assert host.db.get_setting_value('流程图持续动画') == 'False'
    finally:
        reopened.hide(); reopened.deleteLater(); QApplication.processEvents()
        view.set_continuous_animation(False)


def test_auto_hide_preserves_highlight_and_removes_terminal_heads(flow):
    from unittest.mock import Mock
    from qt_compat.QtGui import QFont
    scene, view = flow
    loop = scene.nodes_by_command_id[1]
    loop.setSelected(True)
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        clock.return_value = 105
        view._advance_flow_arrows()
        edges = [edge for edge in scene.edges if edge._control_highlight()]
        assert edges and loop.isSelected()
        painter = Mock()
        painter.font.return_value = QFont()
        for edge in edges:
            edge.paint(painter, None)
        painter.drawPolygon.assert_not_called()
        assert painter.drawPath.call_count >= 2 * len(edges)  # Highlight halo plus line.
        assert any(call.args[0].color().alpha() == 55 for call in painter.setPen.call_args_list)


@pytest.mark.parametrize('hidden', [False, True])
def test_deadline_hides_arrows_even_without_a_running_animation_timer(flow, hidden):
    scene, view = flow
    scene.load_graph([{'id': 1, 'type_id': '时间等待', 'x': 0, 'y': 0}], [], {})
    if hidden:
        view.hide()
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        assert not scene.flow_arrow_edges and not view._arrow_timer.isActive()
        assert view._arrow_preview_timer.isActive() and scene.arrows_visible
        clock.return_value = 105
        view._arrow_preview_timer.timeout.emit()
        assert not scene.arrows_visible and not view.arrows_visible
        assert not view._arrow_preview_timer.isActive()


def test_auto_hide_keeps_saved_preference_and_next_run_restores_arrows(host):
    view = host.workspace.editor.view
    view.set_arrows_visible(False)
    view.set_arrows_visible(True)
    changes = []
    view.arrowsVisibilityChanged.connect(changes.append)
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        host.command_thread.started.emit()
        QApplication.processEvents()
        clock.return_value = 105
        view._advance_flow_arrows()
        assert not view.arrows_visible and not changes
        assert host.db.get_setting_value('流程图显示箭头') == 'True'
        clock.return_value = 110
        host.command_thread.started.emit()
        QApplication.processEvents()
        assert view.arrows_visible and view._arrow_run_until == 115
        view.set_arrows_visible(False)
        clock.return_value = 120
        host.command_thread.started.emit()
        QApplication.processEvents()
        assert not view.arrows_visible and not view._arrow_timer.isActive()
        assert host.db.get_setting_value('流程图显示箭头') == 'False'


def test_manual_reopen_and_continuous_mode_work_after_auto_hide(flow):
    scene, view = flow
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        clock.return_value = 105
        view._advance_flow_arrows()
        assert not view.arrows_visible
        view.set_arrows_visible(True)
        assert view.arrows_visible and scene.arrows_visible
        assert not view._arrow_timer.isActive() and not view._arrow_preview_timer.isActive()
        view.play_run_animation()
        clock.return_value = 111
        view._advance_flow_arrows()
        assert not view.arrows_visible
        view.set_continuous_animation(True)
        assert view.arrows_visible and scene.arrows_visible and view._arrow_timer.isActive()
        assert not view._arrow_preview_timer.isActive()
        clock.return_value = 200
        view._advance_flow_arrows()
        assert view.arrows_visible and view._arrow_timer.isActive()


def test_early_deadline_callback_rearms_without_leaving_hidden_canvas_arrows(flow):
    scene, view = flow
    view.hide()
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        clock.return_value = 104.999
        view._arrow_preview_timer.stop()
        view._arrow_preview_timer.timeout.emit()
        assert scene.arrows_visible and view._arrow_preview_timer.isActive()
        assert 1 <= view._arrow_preview_timer.interval() <= 2
        clock.return_value = 105
        view._arrow_preview_timer.timeout.emit()
        assert not scene.arrows_visible and not view._arrow_preview_timer.isActive()
