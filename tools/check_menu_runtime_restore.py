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
from anclicker.platform.qt_compat.QtWidgets import QMenu
from anclicker.platform.qt_compat.QtGui import QPalette
from anclicker.ui.workspace_constants import FLOW_VIEW,TABLE_VIEW
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
    w=Main_window()
    w.show()
    app.processEvents()
    actions=w._view_shortcut_actions
    for label in ('指令栏收起/展开','控制与操作收起/展开'):
        assert label in actions
        assert actions[label].property('shortcutEnabled') is False
    palette_before=w.view_workspace.palette_collapsed
    actions['指令栏收起/展开'].trigger()
    assert w.view_workspace.palette_collapsed != palette_before
    actions['指令栏收起/展开'].trigger()
    controls_before=w.view_workspace.controls_collapsed
    actions['控制与操作收起/展开'].trigger()
    assert w.view_workspace.controls_collapsed != controls_before
    actions['控制与操作收起/展开'].trigger()
    # Every dynamically-created arrangement submenu needs its own background painter.
    checked=[]
    def inspect_menu(menu,point):
        for action in menu.actions():
            sub=action.menu()
            if sub is not None:
                expected='#222225' if w.view_workspace.theme_mode=='dark' else '#ffffff'
                assert sub.palette().color(QPalette.Window).name()==expected
                assert sub._rounded_menu_background.background.name()==expected
                checked.append((w.view_workspace.theme_mode,action.text()))
        return None
    for theme in ('light','dark'):
        w.view_workspace.theme_mode=theme
        with patch.object(QMenu,'exec',inspect_menu):
            w.view_workspace.docking.panel_menu('palette',w.pos())
    assert any(theme=='light' for theme,label in checked)
    assert any(theme=='dark' for theme,label in checked)
    edit=w.recent_project_picker.combo.lineEdit()
    edit.setText('example.xlsx');edit.selectAll()
    menu=edit.createStandardContextMenu()
    labels=[a.text().split('\t')[0] for a in menu.actions() if not a.isSeparator()]
    assert {'撤销','重做','剪切','复制','粘贴','删除','全选'}.issubset(labels),labels
    menu.deleteLater()
    # Exercise the actual runtime finish method with no worker executing.
    for maximized in (False,True):
        w.showNormal()
        w.resize(1100,700)
        if maximized:w.showMaximized()
        w.view_workspace.tabs.setCurrentIndex(FLOW_VIEW)
        app.processEvents()
        size=w.size()
        transform=w.workspace.editor.view.transform()
        collapsed=(w.view_workspace.palette_collapsed,w.view_workspace.controls_collapsed)
        w._capture_run_window_state()
        w.view_workspace.begin_runtime_view()
        w.hide()
        w.view_workspace.tabs.setCurrentIndex(TABLE_VIEW)
        with patch.object(w,'_sync_stop_shortcut'):
            w._runtime_finished()
        app.processEvents()
        assert w.isVisible()
        assert w.isMaximized()==maximized
        assert w.size()==size,(w.size(),size)
        assert w.view_workspace.tabs.currentIndex()==FLOW_VIEW
        assert w.workspace.editor.view.transform()==transform
        assert (w.view_workspace.palette_collapsed,w.view_workspace.controls_collapsed)==collapsed
    w.close();w.ocr_pool.close();app.processEvents()
    print('PASS light/dark submenus, Chinese edit menu, panel toggles, normal/maximized runtime restore, page and zoom preserved',flush=True)
os._exit(0)
