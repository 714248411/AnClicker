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
from anclicker.ui.workspace_constants import FLOW_VIEW
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.show()
    v=w.view_workspace;d=v.docking
    v.tabs.setCurrentIndex(FLOW_VIEW);app.processEvents()
    v.begin_runtime_view();app.processEvents()
    assert v.flow_log_panel.isVisible()
    # Move out during execution: internal log disappears immediately.
    dock=d.ensure_dock('log');app.processEvents()
    assert dock.isVisible() and not v.flow_log_panel.isVisible()
    d.float_panel('log',True);app.processEvents()
    assert dock.isVisible() and not v.flow_log_panel.isVisible()
    v.end_runtime_view();app.processEvents()
    # Start with an existing external log: still only one log.
    v.begin_runtime_view();app.processEvents()
    assert dock.isVisible() and not v.flow_log_panel.isVisible()
    dock.hide();app.processEvents()
    assert v.flow_log_panel.isVisible()
    dock.show();app.processEvents()
    assert not v.flow_log_panel.isVisible()
    assert d.return_center('log');app.processEvents()
    assert v.flow_log_panel.isVisible()
    assert v.flow_log.document() is w.textEdit.document()
    v.end_runtime_view();app.processEvents()
    assert not v.flow_log_panel.isVisible()
    print('PASS one runtime log across docked/floating/hide/show/return-center, before and during execution; shared document preserved',flush=True)
    os._exit(0)
