from qt_compat.QtCore import QPoint, Qt
from qt_compat.QtGui import QColor
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


def test_all_tabs_attach_to_content_with_external_recording_gap(host):
    view = host.view_workspace
    host.resize(1200, 800)
    bar = view.tabs.tabBar()
    assert not bar.drawBase()
    assert [bar.tabText(i) for i in range(bar.count()) if bar.is_embedded(i)] == ['主界面', '表格图', '流程图', '多功能', '录制', '网页录制']
    for theme in ('dark', 'light'):
        if view.theme_mode != theme:
            view.toggle_theme()
        for index in range(bar.count()):
            QTest.mouseClick(bar, Qt.LeftButton, pos=bar._button_rect(index).center())
            QTest.qWait(25)
            assert view.tabs.currentIndex() == index
            page = view.tabs.currentWidget()
            assert page.mapTo(view.tabs, QPoint(0, 0)).y() == bar.geometry().bottom() + 1
            pixels = view.tabs.grab().toImage()
            x = bar.mapTo(view.tabs, bar._button_rect(index).center()).x()
            # No divider or gap between the selected editor tab and its page.
            expected = QColor(view.THEMES[theme]['surface' if index in (1, 2, 3) else 'bg'])
            assert pixels.pixelColor(x, bar.geometry().bottom()) == expected
            assert pixels.pixelColor(x, bar.geometry().bottom() + 1) == expected
    for index in (0, 4, 5):
        QTest.mouseClick(bar, Qt.LeftButton, pos=bar._button_rect(index).center())
        assert view.tabs.currentIndex() == index
    gap = bar._gap(4)
    point = QPoint(bar.tabRect(4).left() + gap // 2, bar.tabRect(4).center().y())
    assert bar.tabAt(point) == -1
    QTest.mouseClick(bar, Qt.LeftButton, pos=point)
    assert view.tabs.currentIndex() == 5


def test_navigation_keeps_size_and_keyboard_access_in_narrow_workspace(host):
    view = host.view_workspace
    bar = view.tabs.tabBar()
    host.resize(900, 800)
    view.show_main()
    QTest.qWait(50)
    sizes = [bar.tabSizeHint(i) for i in range(bar.count())]
    bar.setFocus()
    for index in range(1, bar.count()):
        QTest.keyClick(bar, Qt.Key_Right)
        QTest.qWait(20)
        assert view.tabs.currentIndex() == index
        assert [bar.tabSizeHint(i) for i in range(bar.count())] == sizes
        # The selected page remains reachable even when the row must scroll.
        center = bar._button_rect(index).center()
        assert bar.rect().contains(center)
        assert bar.tabAt(center) == index
    # Home now frees the sidebar; force a genuinely narrow row for overflow.
    bar.setMaximumWidth(280)
    QTest.qWait(30)
    from qt_compat.QtWidgets import QToolButton
    arrows = [b for b in bar.findChildren(QToolButton) if b.isVisible()]
    assert arrows
    assert len({size.height() for size in sizes}) == 1
