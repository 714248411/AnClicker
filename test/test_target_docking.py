import pytest
from qt_compat.QtCore import QPoint, QRect
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


@pytest.mark.parametrize('direction', ['left', 'right', 'top', 'bottom'])
def test_target_overlay_and_relative_split(host, direction):
    v = host.view_workspace; d = v.docking
    host.resize(1400, 900); v.show_table(); QTest.qWait(80)
    target = d.docks['controls']
    d.show_targets('palette')
    d.target_timer.stop()
    d.update_targets(target.mapToGlobal(target.rect().center()))
    expected = QRect(target.mapTo(d.host, QPoint()), target.size())
    assert d.target_panel == 'controls' and d.target_rect == expected
    visible = [z for z in d.targets if z.isVisible()]
    assert len(visible) == 5
    assert all(expected.contains(z.geometry()) for z in visible)
    union = QRect()
    for zone in visible: union = union.united(zone.geometry())
    assert union == expected
    assert d.drop_on_target('palette', direction)
    d.hide_targets(); QTest.qWait(300)
    source = d.docks['palette']
    if direction == 'left': assert source.geometry().right() < target.geometry().left()
    if direction == 'right': assert source.geometry().left() > target.geometry().right()
    if direction == 'top': assert source.geometry().bottom() < target.geometry().top()
    if direction == 'bottom': assert source.geometry().top() > target.geometry().bottom()
    assert not d.target_timer.isActive()
    assert not any(z.isVisible() for z in d.targets)


def test_overlay_tracks_target_and_leaves_workspace(host):
    v = host.view_workspace; d = v.docking
    v.show_table(); QTest.qWait(80)
    d.show_targets('log'); d.target_timer.stop()
    for key in ['palette', 'controls']:
        target = d.docks[key]
        d.update_targets(target.mapToGlobal(target.rect().center()))
        assert d.target_panel == key
        assert d.target_rect.size() == target.size()
    d.update_targets(d.host.mapToGlobal(QPoint(-50, -50)))
    assert not any(z.isVisible() for z in d.targets)
    d.hide_targets()
