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
from anclicker.platform.qt_compat.QtWidgets import QMainWindow
from anclicker.ui.workspace_constants import FLOW_VIEW
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.resize(1400,900);w.show()
    v=w.view_workspace;v.tabs.setCurrentIndex(FLOW_VIEW)
    v.palette_collapsed=False;v.set_controls_visible(True)
    d=v.docking;d.sync_visibility()
    d.host.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks)
    app.processEvents()
    original_size=w.size()
    for mode in ('horizontal','vertical','tabs','horizontal','tabs','vertical')*3:
        assert d.move_panel('palette','right','controls',mode)
        app.processEvents()
        left=d.docks['controls'];right=d.docks['palette']
        assert w.size()==original_size,(mode,w.size(),original_size)
        tabbed=right in d.host.tabifiedDockWidgets(left)
        if mode=='tabs':assert tabbed
        else:
            assert not tabbed,mode
            a,b=left.geometry(),right.geometry()
            assert (b.left()>=a.right() if mode=='horizontal' else b.top()>=a.bottom()),(mode,a,b)
    from anclicker.platform.qt_compat.QtWidgets import QMenu
    for title,mode in [('横向并排','horizontal'),('纵向堆叠','vertical'),('合为标签','tabs')]:
        d.float_panel('palette',True)
        app.processEvents()
        assert d.docks['palette'].isFloating()
        def choose(menu,point):
            submenu=next(a.menu() for a in menu.actions() if a.text()==title)
            action=next(a for a in submenu.actions() if a.text()==d.docks['controls'].windowTitle())
            action.trigger()
        with patch.object(QMenu,'exec',choose):
            d.panel_menu('palette',w.pos())
        app.processEvents()
        assert not d.docks['palette'].isFloating()
        assert w.size()==original_size
        tabbed=d.docks['palette'] in d.host.tabifiedDockWidgets(d.docks['controls'])
        assert tabbed==(mode=='tabs')
    d.save()
    print('PASS 18 arrangement transitions, stable window size, horizontal/vertical geometry, tab grouping, actual menu callbacks from floating panels, layout save',flush=True)
os._exit(0)
