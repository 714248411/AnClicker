import pytest
from qt_compat.QtCore import Qt, QPoint
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host

@pytest.mark.parametrize('area',['left','right','top','bottom'])
def test_palette_collapse_restores_size_and_clock_parent(host,area):
    v=host.view_workspace;d=v.docking
    host.resize(1400,900);v.show_table();d.move_panel('palette',area);QTest.qWait(50)
    dock=d.docks['palette']
    horizontal=area in ('left','right')
    d.host.resizeDocks([dock],[255 if horizontal else 240],Qt.Horizontal if horizontal else Qt.Vertical)
    QTest.qWait(50)
    before=dock.size()
    for _ in range(3):
        v.toggle_palette();QTest.qWait(25)
        assert dock.isHidden()
        v.toggle_palette();QTest.qWait(50)
        assert abs(dock.width()-before.width())<=2
        assert abs(dock.height()-before.height())<=2
    button=host.workspace.palette.schedule_button
    assert button.parent() is host.workspace.palette.tree_surface
    assert button.geometry().bottom() < host.workspace.palette.tree_surface.height()
    assert host.workspace.palette.tree_surface.height() - button.geometry().bottom() <= 5
    assert button.mapTo(host.workspace.palette,QPoint()).x()<15


def test_font_menu_corners_transparent_and_theme_follows(host):
    menu=host.view_workspace.font_size_menu
    for theme in ('light','dark'):
        if host.view_workspace.theme_mode != theme:host.view_workspace.toggle_theme()
        menu.popup(host.mapToGlobal(QPoint(100,80)));QTest.qWait(30)
        assert menu.testAttribute(Qt.WA_TranslucentBackground)
        image=menu.grab().toImage()
        assert image.pixelColor(0,0).alpha()==0
        expected='#202024' if theme=='dark' else '#ffffff'
        assert menu._rounded_menu_background.background.name()==expected
        menu.hide()
