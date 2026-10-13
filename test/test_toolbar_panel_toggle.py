import pytest
from qt_compat.QtCore import Qt
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


@pytest.mark.parametrize('controls_visible', [True, False])
def test_palette_side_switch_preserves_height(host, controls_visible):
    v = host.view_workspace
    host.resize(1400, 850)
    v.show_table()
    v.controls_action.setChecked(controls_visible)
    QTest.qWait(100)
    palette = v.docking.docks['palette']
    height = palette.height()
    for side in ['right', 'left', 'right', 'left']:
        v.palette_side_action.trigger()
        QTest.qWait(300)
        assert v.palette_side == side
        assert palette.height() == height
        assert v.docking.host.dockWidgetArea(palette) == (Qt.RightDockWidgetArea if side == 'right' else Qt.LeftDockWidgetArea)


def test_controls_action_text_tracks_visibility(host):
    v = host.view_workspace
    assert v.controls_action.text() == '收起控制与操作'
    v.controls_action.trigger()
    QTest.qWait(50)
    assert v.controls_action.text() == '展开控制与操作'
    assert not v.docking.docks['controls'].isVisible()
    v.controls_action.trigger()
    QTest.qWait(50)
    assert v.controls_action.text() == '收起控制与操作'
    assert v.docking.docks['controls'].isVisible()
    v.controls_action.trigger()
    v.layout_presets.reset()
    assert v.controls_action.text() == '收起控制与操作'


def test_donation_follows_help_on_menu_bar(host):
    v = host.view_workspace
    actions = host.menubar.actions()
    labels = [action.text().replace('&', '') for action in actions]
    assert labels.index('捐赠') == labels.index('帮助') + 1
    assert v.donation_action not in host.toolBar.actions()
