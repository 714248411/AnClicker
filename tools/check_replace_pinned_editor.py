import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='anclicker-settings-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog
from anclicker.platform.qt_compat.QtCore import Qt,QEvent,QPointF
from anclicker.platform.qt_compat.QtGui import QMouseEvent
from anclicker.app.Start_Win import Main_window
from anclicker.ui.dialogs.设置窗口 import Setting,SETTINGS_SECTIONS
app=QApplication([])
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.workspace_constants import FLOW_VIEW
from anclicker.platform.qt_compat.QtWidgets import QDialog
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.resize(1400,900);w.show()
    w.view_workspace.tabs.setCurrentIndex(FLOW_VIEW)
    repo=w.workspace.repository
    repo.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':1,'单位':'秒'}),InstructionDraft('时间等待',{'类型':'时间等待','时长':2,'单位':'秒'})])
    commands=repo.list_commands()
    manager=w.view_workspace.docking
    first,second=commands[0].id,commands[1].id
    w.workspace.edit_command(first)
    app.processEvents()
    key='parameters_'+str(first)
    manager.float_panel(key,False)
    app.processEvents()
    dock=manager.docks[key]
    # Move the pinned editor to a non-default area before replacement.
    assert manager.move_panel(key,'left')
    app.processEvents()
    area=manager.host.dockWidgetArea(dock)
    geometry=dock.geometry()
    before=repo.snapshot()
    old=manager.parameters[key]
    rejected=[]
    old.rejected.connect(lambda:rejected.append(True))
    for command_id in (second,first,second):
        w.workspace.edit_command(command_id)
        app.processEvents()
        key='parameters_'+str(command_id)
        assert list(manager.parameters)==[key],list(manager.parameters)
        assert manager.docks[key] is dock
        assert not dock.isFloating()
        assert manager.host.dockWidgetArea(dock)==area
        assert dock.geometry()==geometry,(dock.geometry(),geometry)
        assert repo.snapshot()==before
    assert rejected==[True]
    # Cancel the current editor closes only that shared panel.
    manager.parameters[key].reject()
    app.processEvents()
    assert not manager.parameters
    assert key not in manager.docks
    print('PASS pinned editor replaced in same dock, geometry/area retained, old editor rejected once, drafts not committed, new cancel closes panel',flush=True)
    os._exit(0)
