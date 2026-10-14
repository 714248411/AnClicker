import json
from unittest.mock import Mock
from qt_compat.QtCore import Qt
from qt_compat.QtGui import QAction
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from toolbar_reorder import SETTING


def buttons(host):
    custom = host.view_workspace.toolbar_customization
    actions = []
    for i in range(2):
        action = QAction('拖动测试' + str(i), host)
        action.setProperty('toolbarOrderId', 'test:' + str(i))
        host.toolBar.insertAction(custom.add_action, action)
        actions.append(action)
    custom.reorder.refresh()
    QTest.qWait(30)
    return custom, actions


def test_short_click_and_long_press_reorder(host):
    custom, (first, second) = buttons(host)
    callback = Mock()
    second.triggered.connect(callback)
    button = host.toolBar.widgetForAction(second)
    QTest.mouseClick(button, Qt.LeftButton)
    assert callback.call_count == 1
    target = host.toolBar.actionGeometry(first).topLeft()
    QTest.mousePress(button, Qt.LeftButton)
    QTest.qWait(custom.reorder.HOLD_MS + 30)
    assert custom.reorder.dragging
    QTest.mouseRelease(button, Qt.LeftButton, pos=button.mapFrom(host.toolBar, target))
    assert callback.call_count == 1
    assert host.toolBar.actions().index(second) < host.toolBar.actions().index(first)
    saved = json.loads(host.db.get_setting_value(SETTING))
    assert saved.index('test:1') < saved.index('test:0')
    custom.sync()
    assert host.toolBar.actions().index(second) < host.toolBar.actions().index(first)
    assert host.toolBar.widgetForAction(second).isVisible()
    assert host.toolBar.actions()[-1] == custom.add_action


def test_drag_outside_cancels_without_click(host):
    custom, (first, second) = buttons(host)
    callback = Mock()
    first.triggered.connect(callback)
    button = host.toolBar.widgetForAction(first)
    before = host.toolBar.actions()
    QTest.mousePress(button, Qt.LeftButton)
    QTest.qWait(custom.reorder.HOLD_MS + 30)
    from qt_compat.QtCore import QPoint
    QTest.mouseRelease(button, Qt.LeftButton, pos=QPoint(-1000, -1000))
    assert host.toolBar.actions() == before
    callback.assert_not_called()


def test_saved_order_restores(host):
    custom, (first, second) = buttons(host)
    custom.reorder.move_to(second, host.toolBar.actionGeometry(first).topLeft())
    # Simulate the construction order on the next launch, then read stored IDs.
    host.toolBar.insertAction(second, first)
    custom.reorder.order = json.loads(host.db.get_setting_value(SETTING))
    custom.reorder.refresh()
    assert host.toolBar.actions().index(second) < host.toolBar.actions().index(first)


def mouse_move(host, button, position):
    from qt_compat.QtCore import QEvent, QPointF
    from qt_compat.QtGui import QMouseEvent
    from qt_compat.QtWidgets import QApplication
    local = button.mapFrom(host.toolBar, position)
    event = QMouseEvent(QEvent.MouseMove, QPointF(local),
                       QPointF(host.toolBar.mapToGlobal(position)),
                       Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(button, event)


def test_live_neighbors_slide_and_reverse_before_commit(host):
    custom, (first, second) = buttons(host)
    reorder = custom.reorder
    button = host.toolBar.widgetForAction(second)
    before = host.toolBar.actions()
    saved = host.db.get_setting_value(SETTING)
    QTest.mousePress(button, Qt.LeftButton)
    QTest.qWait(reorder.HOLD_MS + 30)
    preview = reorder.preview
    start = preview.positions[first].x()
    target = host.toolBar.actionGeometry(first).topLeft()
    mouse_move(host, button, target)
    assert preview.items.index(second) < preview.items.index(first)
    assert preview.targets[first].x() > start
    assert host.toolBar.actions() == before
    assert host.db.get_setting_value(SETTING) == saved
    QTest.qWait(65)
    assert start < preview.positions[first].x() < preview.targets[first].x()
    # A stationary pointer must not keep swapping neighboring icons.
    items = list(preview.items)
    mouse_move(host, button, target)
    assert preview.items == items
    QTest.qWait(150)
    assert preview.positions[first] == preview.targets[first]
    # Move back across the same neighbor; it now slides left into its old slot.
    mouse_move(host, button, preview.origin.toPoint())
    assert preview.items.index(first) < preview.items.index(second)
    assert preview.targets[first].x() == start
    QTest.keyClick(host, Qt.Key_Escape)
    assert reorder.preview is None and not reorder.dragging
    QTest.mouseRelease(button, Qt.LeftButton)
    assert host.toolBar.actions() == before
    assert host.db.get_setting_value(SETTING) == saved


def test_release_commits_preview_order_without_activating(host):
    custom, (first, second) = buttons(host)
    button = host.toolBar.widgetForAction(second)
    callback = Mock()
    second.triggered.connect(callback)
    QTest.mousePress(button, Qt.LeftButton)
    QTest.qWait(custom.reorder.HOLD_MS + 30)
    position = host.toolBar.actionGeometry(first).topLeft()
    mouse_move(host, button, position)
    planned = list(custom.reorder.preview.items)
    QTest.mouseRelease(button, Qt.LeftButton, pos=button.mapFrom(host.toolBar, position))
    assert custom.reorder.preview is None
    assert [a for a in host.toolBar.actions() if a in planned] == planned
    callback.assert_not_called()


def test_drag_preview_respects_vertical_toolbar(host):
    custom, (first, second) = buttons(host)
    host.addToolBar(Qt.LeftToolBarArea, host.toolBar)
    QTest.qWait(50)
    button = host.toolBar.widgetForAction(second)
    assert button.isVisible()
    QTest.mousePress(button, Qt.LeftButton)
    QTest.qWait(custom.reorder.HOLD_MS + 30)
    preview = custom.reorder.preview
    assert preview.vertical
    start = preview.positions[first].y()
    target = host.toolBar.actionGeometry(first).topLeft()
    mouse_move(host, button, target)
    assert preview.targets[first].y() > start
    assert preview.items.index(second) < preview.items.index(first)
    QTest.keyClick(host, Qt.Key_Escape)
    QTest.mouseRelease(button, Qt.LeftButton)
