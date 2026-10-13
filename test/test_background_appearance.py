import pytest
from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import QApplication, QScrollArea, QLineEdit
from qt_compat.QtGui import QPalette
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from instructions.models import InstructionDraft
from background_catalog import label

@pytest.mark.parametrize('theme',['light','dark'])
@pytest.mark.parametrize('type_id',['绑定选择窗口','后台图色操作','解除后台绑定','后台键鼠操作'])
def test_background_parameter_panel_uses_workspace_theme(host,theme,type_id):
    v=host.view_workspace
    host.resize(1200,850)
    v.theme_mode=theme;v._apply_theme();v.show_table()
    parameters={'接口':label('FindPic'),'参数':'{}'} if type_id=='后台图色操作' else {'接口':label('LeftClick'),'参数':'{}'} if type_id=='后台键鼠操作' else {}
    command=host.workspace.repository.add_command(InstructionDraft(type_id,parameters),unconnected=True)
    v.refresh_table()
    row=next(r for r in range(v.command_table.rowCount()) if v.command_table.item(r,0).data(Qt.UserRole)==command.id)
    v.command_table.cellDoubleClicked.emit(row,2)
    QTest.qWait(100)
    key='parameters_'+str(command.id);dock=v.docking.docks[key];editor=v.docking.parameters[key]
    if type_id=='后台图色操作':dock.resize(760,720)
    QTest.qWait(100)
    if type_id=='绑定选择窗口':assert dock.height()<620
    expected=v.THEMES[theme]['bg'].lower()
    for area in dock.findChildren(QScrollArea):
        assert area.viewport().palette().color(area.viewport().backgroundRole()).name()==expected
    image_name={'绑定选择窗口':'binding','后台图色操作':'image','解除后台绑定':'unbind','后台键鼠操作':'input'}[type_id]
    dock.grab().save('validation/background-'+image_name+'-'+theme+'.png')
    assert all(c.height()>=c.fontMetrics().height() for c in editor.findChildren(QLineEdit) if c.isVisible()), [(c.objectName(),c.width(),c.height()) for c in editor.findChildren(QLineEdit) if c.isVisible()]
    if type_id=='后台图色操作':
        combo=editor._controls['接口'];completer=combo.completer()
        completer.setCompletionPrefix('Find');completer.complete();QTest.qWait(30)
        popup=completer.popup()
        assert popup.isVisible()
        assert popup.palette().color(QPalette.Base)==combo.view().palette().color(QPalette.Base)
        popup.grab().save('validation/background-search-'+theme+'.png')
        popup.hide()
    elif type_id=='绑定选择窗口':
        top=dock.y();height=dock.height()
        editor.advanced_button.setChecked(True);QTest.qWait(100)
        assert editor.advanced_panel.isVisible() and dock.y()==top and dock.height()>=height
        dock.grab().save('validation/background-binding-advanced-'+theme+'.png')
        editor.advanced_button.setChecked(False);QTest.qWait(100)
        assert dock.y()==top and dock.height()==height
    editor.reject();QApplication.processEvents()
