from qt_compat.QtCore import Qt, QPoint
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


def test_home_uses_full_workspace_and_editors_expand_palette(host):
    view = host.view_workspace
    host.resize(1234, 800)
    palette = view.docking.docks['palette']
    controls = view.docking.docks['controls']
    QTest.qWait(80)
    assert view.tabs.currentIndex() == 0
    assert palette.isHidden() and controls.isVisible()
    assert view.palette_collapse_action.text() == '展开指令栏'
    assert view.main_page._columns == 2
    bar = view.tabs.tabBar()
    for index in (1, 2):
        # Clicking a tab and using home actions share the navigation behavior.
        QTest.mouseClick(bar, Qt.LeftButton, pos=bar._button_rect(index).center())
        QTest.qWait(30)
        assert palette.isVisible() and not view.palette_collapsed
        assert palette.width() >= 200
        assert view.palette_collapse_action.text() == '收起指令栏'
        view.toggle_palette()
        assert palette.isHidden()
        # A refresh must respect a manual collapse on the current editor page.
        view.docking.sync_visibility()
        assert palette.isHidden()
        view.show_main()
        assert palette.isHidden() and controls.isVisible()
    view.main_page.continue_button.click()
    assert view.tabs.currentIndex() == 2 and palette.isVisible()


def test_palette_width_survives_home_round_trip(host):
    view = host.view_workspace
    host.resize(1234, 800)
    view.show_table()
    palette = view.docking.docks['palette']
    QTest.qWait(60)
    view.docking.host.resizeDocks([palette], [240], Qt.Horizontal)
    QTest.qWait(60)
    width = palette.width()
    view.show_main()
    QTest.qWait(30)
    view.show_flow()
    QTest.qWait(60)
    assert abs(palette.width() - width) <= 2


def test_saved_layout_visibility_still_restores(host):
    view = host.view_workspace
    view.show_table()
    view.toggle_palette()
    view.layout_presets.save()
    key = view.layout_presets.selected
    view.show_main()
    view.layout_presets.apply(key)
    assert view.tabs.currentIndex() == 1
    assert view.docking.docks['palette'].isHidden()
    view.show_main()
    view.show_table()
    assert view.docking.docks['palette'].isVisible()
