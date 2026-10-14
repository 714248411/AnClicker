from qt_compat.QtCore import Qt, QEvent, QTimer, QPoint
from qt_compat.QtGui import QContextMenuEvent
from qt_compat.QtWidgets import QApplication
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from flow_tips import SETTING, TIPS, FlowTips


def test_tips_cycle_and_pause_when_hidden_or_hovered(host):
    view = host.view_workspace
    tips = view.flow_tips
    assert not tips.timer.isActive()
    view.show_flow()
    QTest.qWait(20)
    QApplication.sendEvent(tips, QEvent(QEvent.Leave))
    assert tips.timer.isActive()
    assert tips.label.full_text == TIPS[0]
    tips.next.click()
    assert tips.label.full_text == TIPS[1]
    tips.previous.click()
    assert tips.label.full_text == TIPS[0]
    tips.previous.click()
    assert tips.label.full_text == TIPS[-1]
    QApplication.sendEvent(tips, QEvent(QEvent.Enter))
    assert not tips.timer.isActive()
    QApplication.sendEvent(tips, QEvent(QEvent.Leave))
    tips.timer.setInterval(30)
    QTest.qWait(45)
    assert tips.index == 0
    view.show_main()
    assert not tips.timer.isActive()


def test_context_collapse_removes_row_and_restores_from_view_menu(host):
    view = host.view_workspace
    host.resize(1200, 800)
    view.show_flow()
    tips = view.flow_tips
    QTest.qWait(30)
    old_top = view.flow_splitter.y()
    def choose_collapse():
        menu = QApplication.activePopupWidget()
        assert menu is not None
        next(a for a in menu.actions() if a.text() == '收起提示').trigger()
        menu.close()
    QTimer.singleShot(20, choose_collapse)
    point = tips.rect().center()
    event = QContextMenuEvent(QContextMenuEvent.Mouse, point, tips.mapToGlobal(point))
    QApplication.sendEvent(tips, event)
    QTest.qWait(30)
    assert tips.isHidden() and not tips.timer.isActive()
    assert not view.flow_tips_action.isChecked()
    assert host.db.get_setting_value(SETTING) == 'False'
    assert view.flow_splitter.y() < old_top
    restored = FlowTips(host)
    try:
        assert not restored.expanded and restored.isHidden()
    finally:
        restored.deleteLater()
    view.flow_tips_action.trigger()
    QTest.qWait(30)
    assert tips.isVisible() and tips.expanded
    assert host.db.get_setting_value(SETTING) == 'True'


def test_tip_text_stays_compact_with_full_tooltip(host):
    view = host.view_workspace
    view.show_flow()
    tips = view.flow_tips
    tips.setFixedWidth(260)
    QTest.qWait(30)
    height = tips.height()
    for _ in TIPS:
        assert tips.label.full_text in tips.label.toolTip()
        assert tips.label.accessibleName() == tips.label.full_text
        assert tips.label.fontMetrics().horizontalAdvance(tips.label.text()) <= tips.label.width()
        tips.advance()
        QTest.qWait(5)
        assert tips.height() == height
    assert tips.label.width() > 60
