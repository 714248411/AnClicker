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
from anclicker.platform.qt_compat.QtWidgets import QLabel,QPushButton,QHBoxLayout
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.show()
    w.view_workspace.show_table()
    manager=w.view_workspace.docking
    manager.ensure_dock('log')
    app.processEvents()
    panel=manager.placeholders['log']
    assert isinstance(panel.layout(),QHBoxLayout)
    label=panel.notice;button=panel.back
    assert abs(label.geometry().center().y()-button.geometry().center().y())<=1
    assert button.width()<200
    assert panel.height()<=button.height()+2,(panel.height(),button.height())
    old_height=panel.height()
    w.view_workspace.interface_scale.change(4);app.processEvents()
    assert panel.height()>old_height
    assert panel.height()==max(panel.notice.sizeHint().height(),panel.back.sizeHint().height())+2
    button.linkActivated.emit('return');app.processEvents()
    assert 'log' not in manager.placeholders
    print('PASS one-row compact log placeholder, content-sized button, return action',flush=True)
    os._exit(0)
