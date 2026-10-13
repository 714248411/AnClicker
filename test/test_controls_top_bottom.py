import pytest
from qt_compat.QtCore import Qt
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


@pytest.mark.parametrize('area', ['top', 'bottom'])
def test_horizontal_controls_shrink_and_restore(host, area):
    v = host.view_workspace; d = v.docking
    host.resize(1400, 900); v.show_table()
    d.move_panel('controls', area)
    dock = d.docks['controls']
    d.host.resizeDocks([dock], [260], Qt.Vertical)
    QTest.qWait(150)
    assert d.controls_horizontal
    buttons = [host.pushButton_5, host.pushButton_7, host.pushButton_6]
    assert all(button.parentWidget() is d.control_actions for button in buttons)
    assert d.control_actions.geometry().left() > host.checkBox_2.geometry().left()
    font = buttons[0].font().pixelSize()
    height = buttons[0].sizeHint().height()
    assert font == 13
    d.host.resizeDocks([dock], [100], Qt.Vertical)
    QTest.qWait(150)
    assert buttons[0].font().pixelSize() < font
    assert buttons[0].sizeHint().height() < height
    assert all(button.isVisible() for button in buttons)
    d.host.resizeDocks([dock], [260], Qt.Vertical)
    QTest.qWait(150)
    assert buttons[0].font().pixelSize() == font
    d.move_panel('controls', 'left'); QTest.qWait(100)
    assert not d.controls_horizontal
    d.move_panel('controls', area); QTest.qWait(100)
    assert d.controls_horizontal
