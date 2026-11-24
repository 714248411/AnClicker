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
from anclicker.platform.qt_compat.QtWidgets import QDockWidget,QMenu
from anclicker.platform.qt_compat.QtCore import QPoint
from anclicker.platform.qt_compat.QtGui import QMouseEvent
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.show();app.processEvents()
    manager=w.view_workspace.docking
    manager.ensure_dock('log')
    dock=manager.docks['palette']
    for key in ('palette','controls','log'):
        dock=manager.docks[key]
        manager.set_editable(False)
        assert not dock.features() & QDockWidget.DockWidgetFloatable
        assert not dock.features() & QDockWidget.DockWidgetMovable
        event=QMouseEvent(QEvent.MouseButtonDblClick,QPointF(5,5),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
        assert dock._title_drag_filter.eventFilter(dock._embedded_title,event)
        assert not dock.isFloating()
        def choose(menu,point):
            next(a for a in menu.actions() if a.text()=='窗口化').trigger()
        with patch.object(QMenu,'exec',choose):manager.panel_menu(key,QPoint())
        assert dock.isFloating()
        assert not dock.features() & QDockWidget.DockWidgetFloatable
        manager.float_panel(key,False)
        assert not dock.isFloating()
        manager.set_editable(True)
        assert dock.features() & QDockWidget.DockWidgetFloatable
        event=QMouseEvent(QEvent.MouseButtonDblClick,QPointF(5,5),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
        assert dock._title_drag_filter.eventFilter(dock._embedded_title,event)
        assert dock.isFloating()
        manager.float_panel(key,False)
    manager.set_editable(False)
    print('PASS palette/controls/log locked: double-click blocked, native drag disabled, right-click floats; editable double-click works',flush=True)
    os._exit(0)
