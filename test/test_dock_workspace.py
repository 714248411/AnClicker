import json
import pytest
from qt_compat.QtCore import Qt, QTimer
from qt_compat.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from instructions.models import InstructionDraft
from dock_workspace import PIN_RESULT


def pump():
    QTest.qWait(25)
    QApplication.processEvents()


def test_five_regions_multiple_panels_and_center_fixed(host):
    v=host.view_workspace; d=v.docking
    host.resize(1400,900);v.show_table();pump()
    assert not d.move_panel('table','left')
    assert not d.move_panel('flow','left')
    for area in ('top','bottom','left','right'):
        assert d.move_panel('main',area)
        assert d.move_panel('code',area,'main','horizontal')
        assert d.move_panel('recording',area,'code','vertical')
        pump()
        for key in ('main','code','recording'):
            assert d.host.dockWidgetArea(d.docks[key]) == __import__('dock_workspace').AREAS[area]
            assert d.docks[key].widget().widget() is d.pages[key]
        assert d.host.centralWidget() is v.tabs
        assert v.tabs.indexOf(v.table_page)==1
    d.move_panel('code','right','main','tabs')
    assert d.docks['code'] in d.host.tabifiedDockWidgets(d.docks['main'])
    for key in ('main','code','recording'): assert d.return_center(key)
    assert v.tabs.count()==len(v._remembered_pages())
    assert v.tabs.widget(2) is v.editor_page


def test_layout_restoration_and_compact_with_detached_log(host):
    v=host.view_workspace;d=v.docking
    d.move_panel('log','bottom');d.move_panel('web_recording','left')
    d.move_panel('code','top');pump();d.save()
    record=json.loads(host.db.get_setting_value('五栏停靠布局'))
    assert set(record['pages'])=={'log','web_recording','code'}
    state=bytes(d.host.saveState(1))
    v.compact.set_active(True);pump()
    assert host.pushButton_5.isVisible()
    assert v.table_splitter.count()==2 # table and temporary log placeholder
    v.compact.set_active(False);pump()
    assert d.docks['log'].widget().widget() is d.pages['log']
    assert d.docks['web_recording'].widget().widget() is v.web_recording_page
    assert d.host.dockWidgetArea(d.docks['code'])==Qt.TopDockWidgetArea
    d.return_center('code');d.return_center('web_recording');d.return_center('log')
    host.db.set_setting_value('五栏停靠布局',json.dumps(record))
    d.restoring=True;d.restore();d.restoring=False;pump()
    assert set(d.placeholders)=={'log','web_recording','code'}
    assert d.host.dockWidgetArea(d.docks['code'])==Qt.TopDockWidgetArea


class DraftDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        QVBoxLayout(self).addWidget(QLabel('测试参数'))
        self.setWindowTitle('测试设置')
    def get_draft(self): return InstructionDraft('时间等待',{})


def test_pin_float_redock_save_once_and_cancel(host):
    w=host.workspace;d=host.view_workspace.docking
    saved=[]
    editor=DraftDialog(host)
    assert w._run_parameter_editor(editor,saved.append,'parameters_test') is None
    dock=d.docks['parameters_test'];pump()
    assert editor.isVisible() and not editor.isModal()
    assert dock.isFloating()
    assert not saved
    d.float_parameters('parameters_test',True);pump();assert dock.isFloating()
    d.float_parameters('parameters_test',False);pump();assert not dock.isFloating()
    editor.accept();pump()
    assert len(saved)==1 and 'parameters_test' not in d.docks
    second=DraftDialog(host)
    w._run_parameter_editor(second,saved.append,'parameters_cancel')
    d.docks['parameters_cancel'].close();pump()
    assert len(saved)==1 and 'parameters_cancel' not in d.parameters


def test_sidebar_scaling_restores_without_clipping(host):
    v=host.view_workspace;d=v.docking
    v.show_table();host.resize(1000,650);pump()
    d.host.resizeDocks([d.docks['palette'],d.docks['controls']],[100,150],Qt.Horizontal);pump()
    assert d.scalers[0].last_size<13
    assert d.scalers[1].last_size<13
    for button in (host.pushButton_5,host.pushButton_6,host.pushButton_7):
        vp=v.controls_scroll.viewport()
        assert button.mapTo(vp,button.rect().topRight()).x()<vp.width()
    host.grab().save('validation/docking-narrow.png')
    d.host.resizeDocks([d.docks['palette'],d.docks['controls']],[240,310],Qt.Horizontal);pump()
    assert all(s.last_size==13 for s in d.scalers)


def test_bottom_controls_use_left_settings_right_buttons(host):
    v=host.view_workspace;d=v.docking
    host.resize(1200,800);v.show_table()
    d.move_panel('controls','bottom');pump()
    assert d.controls_horizontal
    assert host.gridLayout_2.getItemPosition(host.gridLayout_2.indexOf(d.control_actions)) == (0,2,4,1)
    assert host.pushButton_5.parentWidget() is d.control_actions
    assert host.pushButton_5.geometry().bottom()<host.pushButton_7.geometry().top()
    assert host.pushButton_7.geometry().bottom()<host.pushButton_6.geometry().top()
    host.grab().save('validation/docking-bottom.png')
    v.compact.set_active(True);pump();assert not d.controls_horizontal
    assert host.pushButton_5.isVisible()
    v.compact.set_active(False);pump();assert d.controls_horizontal
    d.move_panel('controls','left');pump();assert not d.controls_horizontal
    assert host.gridLayout_2.getItemPosition(host.gridLayout_2.indexOf(host.pushButton_5))==(5,0,1,2)


def test_titles_double_click_float_and_embed_without_window_buttons(host):
    host.view_workspace.editable_view_action.setChecked(True)
    from qt_compat.QtWidgets import QDockWidget
    v=host.view_workspace;d=v.docking
    for key in ('palette','controls'):
        dock=d.docks[key]
        assert not dock.features() & QDockWidget.DockWidgetClosable
        assert dock.titleBarWidget() is not None
        assert dock.titleBarWidget().text()==''
        assert dock.titleBarWidget().height()==0
        handle=host.workspace.palette.search_edit if key=='palette' else host.groupBox_3
        from qt_compat.QtCore import QPoint
        QTest.mouseDClick(handle,Qt.LeftButton,Qt.NoModifier,QPoint(20,10));pump()
        assert dock.isFloating()
        QTest.mouseDClick(handle,Qt.LeftButton,Qt.NoModifier,QPoint(20,10));pump()
        assert not dock.isFloating()


def test_real_parameter_editor_scales_and_commits_to_original_command(host):
    from instructions.registry import get_instruction_spec
    repo=host.workspace.repository
    command=repo.add_command(InstructionDraft('时间等待',{}),unconnected=True)
    host.db.set_setting_value('固定指令参数','True')
    host.workspace.edit_command(command.id)
    d=host.view_workspace.docking;key='parameters_'+str(command.id)
    editor=d.parameters[key];dock=d.docks[key]
    d.float_panel(key,True);dock.resize(360,300);pump()
    assert editor._panel_scaler.last_size<13
    assert editor.minimumWidth()==0
    assert editor.isVisible()
    dock.grab().save('validation/docking-parameters-small.png')
    dock.resize(800,700);pump()
    assert editor._panel_scaler.last_size==13
    editor.repeat_count.setValue(3)
    editor._accept_if_valid();pump()
    assert repo.get_command(command.id).repeat_count==3
    assert key not in d.parameters


def test_tab_drag_targets_accept_pages_but_reject_fixed_views(host):
    host.view_workspace.editable_view_action.setChecked(True)
    from qt_compat.QtCore import QMimeData,QPoint,QPointF
    from qt_compat.QtGui import QDragEnterEvent,QDropEvent
    from dock_workspace import PANEL_MIME
    d=host.view_workspace.docking
    d.show_targets()
    zone=next(z for z in d.targets if z.key=='left')
    mime=QMimeData();mime.setData(PANEL_MIME,b'code')
    enter=QDragEnterEvent(QPoint(10,10),Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(zone,enter);assert enter.isAccepted()
    drop=QDropEvent(QPointF(10,10),Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(zone,drop);pump()
    assert drop.isAccepted() and 'code' in d.docks
    assert not any(z.isVisible() for z in d.targets)
    assert not d.move_panel('flow','right') and not d.move_panel('table','right')


def test_semantic_drag_handles_leave_controls_and_typing_usable(host):
    host.view_workspace.editable_view_action.setChecked(True)
    from qt_compat.QtCore import QEvent,QPointF
    from qt_compat.QtGui import QMouseEvent
    d=host.view_workspace.docking
    controls=next(f for f in d.filters if f.key=='controls')
    search=next(f for f in d.filters if f.key=='palette')
    assert controls.header_only and not search.context_menu
    press=QMouseEvent(QEvent.MouseButtonPress,QPointF(20,12),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
    controls.eventFilter(host.groupBox_3,press)
    assert controls.origin[1]=='controls'
    press=QMouseEvent(QEvent.MouseButtonPress,QPointF(20,80),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
    controls.eventFilter(host.groupBox_3,press)
    assert controls.origin is None
    edit=host.workspace.palette.search_edit
    edit.setFocus();QTest.keyClicks(edit,'Excel');assert edit.text()=='Excel'
    d.float_panel('log',True);pump()
    assert d.docks['log'].isFloating()
    QTest.mouseDClick(d.pages['log'].findChild(QLabel),Qt.LeftButton);pump()
    assert not d.docks['log'].isFloating()


def test_corrupt_saved_layout_is_ignored(host):
    d=host.view_workspace.docking
    for value in ('[]','null','{"version":1,"pages":null}','{"version":1,"pages":[{}],"state":"invalid"}'):
        host.db.set_setting_value('五栏停靠布局',value)
        d.restore()
    assert d.host.centralWidget() is host.tabWidget


def test_reset_view_keeps_palette_order_and_unsaved_parameters(host):
    d=host.view_workspace.docking;v=host.view_workspace
    saved_order=host.db.get_setting_value('指令栏置顶顺序')
    editor=DraftDialog(host)
    d.pin_editor(editor,lambda draft:None,'parameters_unsaved')
    d.move_panel('controls','bottom');d.move_panel('code','left')
    d.move_panel('log','top');v.palette_collapsed=True
    v.controls_action.setChecked(False)
    v.restore_view_action.trigger();pump()
    assert not d.placeholders
    assert d.host.dockWidgetArea(d.docks['controls'])==Qt.RightDockWidgetArea
    assert d.host.dockWidgetArea(d.docks['palette'])==Qt.LeftDockWidgetArea
    assert d.docks['controls'].isVisible() and d.docks['palette'].isHidden()
    assert not d.controls_horizontal
    assert host.db.get_setting_value('指令栏置顶顺序')==saved_order
    assert d.parameters['parameters_unsaved'] is editor
    assert d.docks['parameters_unsaved'].isFloating()
    assert editor.isVisible()


@pytest.mark.parametrize('key',['palette','controls','log','parameters_drag'])
def test_content_handle_drag_outside_floats_panel(host,monkeypatch,key):
    host.view_workspace.editable_view_action.setChecked(True)
    from types import SimpleNamespace
    from qt_compat.QtCore import QEvent,QPoint,QPointF
    from qt_compat.QtGui import QMouseEvent
    import dock_workspace as module
    d=host.view_workspace.docking
    if key.startswith('parameters_'):
        editor=DraftDialog(host);d.pin_editor(editor,lambda draft:None,key)
        handle=editor.findChild(QLabel);filter_=editor._drag_filter
    else:
        filter_=next(f for f in d.filters if f.key==key)
        handle={'palette':host.workspace.palette.search_edit,'controls':host.groupBox_3,
                'log':d.pages['log'].findChild(QLabel)}[key]
    class Drag:
        def __init__(self,source): pass
        def setMimeData(self,mime): assert mime.hasFormat(module.PANEL_MIME)
        def exec(self,action): return Qt.IgnoreAction
    monkeypatch.setattr(module,'QDrag',Drag)
    outside=host.mapToGlobal(QPoint(host.width()+60,host.height()//2))
    monkeypatch.setattr(module,'QCursor',SimpleNamespace(pos=lambda:outside))
    press=QMouseEvent(QEvent.MouseButtonPress,QPointF(20,10),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
    move=QMouseEvent(QEvent.MouseMove,QPointF(70,10),Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
    filter_.eventFilter(handle,press)
    assert filter_.eventFilter(handle,move)
    pump()
    assert d.docks[key].isFloating()
    assert not any(zone.isVisible() for zone in d.targets)


def test_code_view_hides_palette_and_editor_navigation_expands_it(host):
    v=host.view_workspace;d=v.docking
    v.show_table();pump();assert d.docks['palette'].isVisible()
    v.show_code();pump();assert d.docks['palette'].isHidden()
    assert not v.palette_collapsed
    v.show_table();pump();assert d.docks['palette'].isVisible()
    v.toggle_palette();assert v.palette_collapsed
    v.show_code();v.show_flow();pump()
    assert d.docks['palette'].isVisible() and not v.palette_collapsed


def test_floating_parameters_hide_both_windows_for_point_picker(host,monkeypatch):
    from instructions.registry import get_instruction_spec
    import instructions.common.editor as module
    d=host.view_workspace.docking
    editor=get_instruction_spec('坐标点击').create_editor(parent=host,context=host.workspace._editor_context())
    d.pin_editor(editor,lambda draft:None,'parameters_point')
    d.float_panel('parameters_point',True);pump()
    observed=[]
    class Picker:
        point=(42,81)
        capture_error=None
        def __init__(self,parent): pass
        def exec(self):
            observed.append((host.windowOpacity(),d.docks['parameters_point'].windowOpacity()))
            return QDialog.Accepted
        def deleteLater(self): pass
    monkeypatch.setattr(module,'_PointSelectionDialog',Picker)
    editor._select_screen_point('坐标',editor._controls['坐标'])
    assert observed==[(0.0,0.0)]
    assert host.windowOpacity()==1.0 and d.docks['parameters_point'].windowOpacity()==1.0
    assert editor._controls['坐标'].text()=='42,81'


def test_parameter_float_preserves_popup_size_centers_and_close_cancels(host):
    from qt_compat.QtWidgets import QDockWidget
    from qt_compat.QtCore import QSize
    d=host.view_workspace.docking
    editor=DraftDialog(host)
    editor.resize(580,440)
    saved=[]
    d.pin_editor(editor,saved.append,'parameters_geometry')
    dock=d.docks['parameters_geometry']
    assert editor._original_popup_size==QSize(580,440)
    d.float_panel('parameters_geometry',True);pump()
    assert dock.isFloating()
    assert dock.titleBarWidget().close_button.isVisible()
    assert dock.features() & QDockWidget.DockWidgetClosable
    assert dock.size()==QSize(580,440)
    assert (dock.frameGeometry().center()-host.frameGeometry().center()).manhattanLength()<8
    d.float_panel('parameters_geometry',False);pump()
    assert dock.titleBarWidget().height()==0
    assert not dock.features() & QDockWidget.DockWidgetClosable
    d.float_panel('parameters_geometry',True);pump()
    dock.close();pump()
    assert not saved and 'parameters_geometry' not in d.parameters
