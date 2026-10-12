from pathlib import Path
import pytest
from qt_compat.QtWidgets import QApplication, QTreeWidgetItem
from qt_compat.QtCore import Qt, QPoint
from test.test_hidden_stop import host

@pytest.mark.parametrize('theme', ['light','dark'])
def test_narrow_window_controls_and_wrapped_palette(host,theme):
    view=host.view_workspace
    view.theme_mode=theme
    view._apply_theme()
    view.show_table()
    host.resize(984,659)
    QApplication.processEvents()
    tree=host.workspace.palette.tree
    item=QTreeWidgetItem(['这是用于检查窄指令栏自动换行显示完整内容的很长指令名称'])
    tree.addTopLevelItem(item)
    view.docking.host.resizeDocks([view.docking.docks['palette']], [140], Qt.Horizontal)
    QApplication.processEvents();tree.doItemsLayout();QApplication.processEvents()
    small=tree.visualItemRect(item).height()
    assert small>tree.fontMetrics().height()+12
    for button in (host.pushButton_5,host.pushButton_6,host.pushButton_7):
        viewport=view.controls_scroll.viewport()
        rect=button.rect()
        assert button.mapTo(viewport,rect.topRight()).x()<viewport.width()
    host.grab().save(str(Path(__file__).resolve().parents[1]/'validation'/('v151-narrow-'+theme+'.png')))
    view.docking.host.resizeDocks([view.docking.docks['palette']], [350], Qt.Horizontal)
    QApplication.processEvents();tree.doItemsLayout();QApplication.processEvents()
    assert tree.visualItemRect(item).height()<small

def test_controls_toggle_compact_restore_and_toolbar_name(host):
    view=host.view_workspace
    actions=host.toolBar.actions()
    assert actions.index(view.controls_action)+1==actions.index(view.donation_action)
    assert host.toolBar.windowTitle()=='显示工具栏'
    assert host.toolBar.toggleViewAction().text()=='显示工具栏'
    view.controls_action.setChecked(False)
    assert view.controls_scroll.isHidden()
    view.show_flow()
    assert view.controls_scroll.isHidden()
    view.compact.set_active(True)
    QApplication.processEvents()
    assert view.controls_scroll.isVisible()
    view.compact.set_active(False)
    QApplication.processEvents()
    assert view.controls_scroll.isHidden()
    view.controls_action.setChecked(True)
    assert view.controls_scroll.isVisible()


def test_recording_buttons_wrap_in_narrow_workspace(host):
    view=host.view_workspace
    host.resize(984,659)
    for name in ('recording_page','web_recording_page'):
        page=getattr(view,name)
        view.tabs.setCurrentWidget(page)
        QApplication.processEvents()
        buttons=[page.start_button,page.stop_button,page.continue_button,page.write_button,page.clear_button]
        for button in buttons:
            assert button.geometry().right()<page.width()
            assert button.geometry().bottom()<page.height()
        for first in buttons:
            for second in buttons:
                if first is not second:
                    assert not first.geometry().intersects(second.geometry())
        host.grab().save(str(Path(__file__).resolve().parents[1]/'validation'/('v151-'+name+'.png')))
