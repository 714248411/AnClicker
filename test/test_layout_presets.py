import json
from qt_compat.QtCore import Qt
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QInputDialog
from test.test_hidden_stop import host


def test_menu_organization(host):
    v=host.view_workspace
    menus=[a.menu() for a in host.menubar.actions() if a.menu()]
    titles=[m.title() for m in menus]
    assert '视图' in titles, repr(titles)
    assert titles.index('界面方案')+1==titles.index('视图')
    view=menus[titles.index('视图')]
    tools=menus[titles.index('工具')]
    assert '中文编程提示' in [a.text() for a in tools.actions()]
    assert '快捷键设置…' in [a.text() for a in tools.actions()]
    assert '中文编程提示' not in [a.text() for a in view.actions()]
    assert v.controls_action.text()=='收起控制栏'
    entries=v.layout_menu.actions()
    assert sum(a.isSeparator() for a in entries)==2
    assert entries[-1].text()=='恢复默认界面'


def test_save_apply_rename_delete_and_restart(host,monkeypatch):
    v=host.view_workspace;d=v.docking;p=v.layout_presets
    host.resize(1200,800);v.show_table();QTest.qWait(25)
    order=host.db.get_setting_value('指令栏置顶顺序')
    p.save();first=p.selected
    assert p.items[0]['name']=='方案1'
    d.move_panel('controls','bottom');d.move_panel('recording','left')
    v.controls_action.setChecked(False);QTest.qWait(25)
    p.save();second=p.selected
    assert p.items[1]['name']=='方案2'
    p.apply(first);QTest.qWait(25)
    assert d.host.dockWidgetArea(d.docks['controls'])==Qt.RightDockWidgetArea
    assert 'recording' not in d.placeholders and v.controls_action.isChecked()
    p.apply(second);QTest.qWait(25)
    assert d.host.dockWidgetArea(d.docks['controls'])==Qt.BottomDockWidgetArea
    assert 'recording' in d.placeholders and not v.controls_action.isChecked()
    assert [a.text() for a in v.layout_menu.actions() if a.isCheckable() and a.isChecked()]==['方案2']
    monkeypatch.setattr(QInputDialog,'getText',lambda *a,**kw:('录制布局',True))
    p.rename();assert p.current()['name']=='录制布局'
    assert host.db.get_setting_value('指令栏置顶顺序')==order
    restored=json.loads(host.db.get_setting_value('界面方案'))
    assert restored['selected']==second and len(restored['items'])==2
    p.delete();assert len(p.items)==1 and p.selected is None
    assert 'recording' in d.placeholders # deletion does not unexpectedly move the workspace
    p.reset();QTest.qWait(25)
    assert not d.placeholders and p.items[0]['id']==first
    assert host.db.get_setting_value('指令栏置顶顺序')==order
    clone=type(host)()
    try:
        assert clone.view_workspace.layout_presets.items[0]['name']=='方案1'
    finally:
        clone.hide();clone.deleteLater()


import pytest

@pytest.mark.parametrize('area',['left','right','top','bottom'])
def test_open_parameters_does_not_move_saved_control_panel(host,area):
    from instructions.models import InstructionDraft
    v=host.view_workspace;d=v.docking
    host.resize(1200,850);v.show_table()
    command=host.workspace.repository.add_command(InstructionDraft('时间等待',{}),unconnected=True)
    v.refresh_table();d.move_panel('controls',area);QTest.qWait(80)
    v.layout_presets.save()
    saved=host.db.get_setting_value('界面方案')
    controls=d.docks['controls']
    geometry=controls.geometry();central=v.tabs.geometry()
    horizontal=d.controls_horizontal
    for _ in range(2):
        row=next(r for r in range(v.command_table.rowCount()) if v.command_table.item(r,0).data(Qt.UserRole)==command.id)
        v.command_table.cellDoubleClicked.emit(row,2);QTest.qWait(80)
        key='parameters_'+str(command.id)
        assert d.docks[key].isFloating()
        assert controls.geometry()==geometry and v.tabs.geometry()==central
        assert d.host.dockWidgetArea(controls)==__import__('dock_workspace').AREAS[area]
        assert d.controls_horizontal==horizontal
        assert host.db.get_setting_value('界面方案')==saved
        d.parameters[key].reject();QTest.qWait(80)
        assert controls.geometry()==geometry and v.tabs.geometry()==central
