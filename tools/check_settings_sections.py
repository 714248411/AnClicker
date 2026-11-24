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
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window()
    assert [a.text() for a in w.settings_sections_menu.actions()]==list(SETTINGS_SECTIONS)
    from anclicker.ui.view_shortcuts import DEFAULT_ENABLED
    actions=w._view_shortcut_actions
    assert DEFAULT_ENABLED.issubset(actions)
    assert {name for name,action in actions.items() if action.property('shortcutEnabled')}==DEFAULT_ENABLED
    assert {'设置','高级设置','启停快捷键','OCR接口设置','其他设置'}.issubset(actions)
    menu=w.menu_4
    labels=[a.text() for a in menu.actions()]
    assert labels[labels.index('设置')+1]=='高级设置',labels
    assert labels[labels.index('高级设置')+1]=='快捷键设置',labels
    assert actions['新建空白页'].shortcut().toString()=='Ctrl+N'
    assert actions['保存'].shortcut().toString()=='Ctrl+S'
    assert not actions['主界面'].shortcut().toString()
    with patch.object(w,'show_windows') as opened:
        for action,label in zip(w.settings_sections_menu.actions(),SETTINGS_SECTIONS):
            action.trigger()
            assert opened.call_args.args==('设置',label)
        controller=w._settings_click_filters[0]
        menu=controller.parent()
        menu.show()
        app.processEvents()
        rect=menu.actionGeometry(w.actions_2)
        def event(kind,point):return QMouseEvent(kind,QPointF(point),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier)
        point=rect.center()
        assert controller.eventFilter(menu,event(QEvent.MouseButtonPress,point))
        assert controller.eventFilter(menu,event(QEvent.MouseButtonRelease,point))
        app.processEvents()
        assert opened.call_args.args==('设置',)
        arrow=rect.topRight();arrow.setX(arrow.x()-4);arrow.setY(rect.center().y())
        assert not controller.eventFilter(menu,event(QEvent.MouseButtonPress,arrow))
    selected=[]
    def execute(dialog):
        selected.append(dialog.tabWidget.tabText(dialog.tabWidget.currentIndex()))
        assert [dialog.tabWidget.tabText(i) for i in range(dialog.tabWidget.count())]==list(SETTINGS_SECTIONS)
        dialog.close()
        return 0
    with patch.object(Setting,'exec',execute):
        for label in SETTINGS_SECTIONS:
            if label!='快捷键设置':
                w.show_windows('设置',label)
                assert selected[-1]==label
    with patch.object(QDialog,'exec',lambda dialog: selected.append(dialog.windowTitle()) or 0):
        w.show_windows('设置','快捷键设置')
        assert selected[-1]=='快捷键设置'
    from anclicker.platform.qt_compat.QtWidgets import QCheckBox,QDialogButtonBox
    from anclicker.platform.qt_compat.QtGui import QKeySequence
    from anclicker.ui.view_shortcuts import ShortcutInput,install_view_shortcuts
    def edit_and_save(dialog):
        dialog.findChild(QCheckBox,'shortcutEnabled_主界面').setChecked(True)
        dialog.findChild(ShortcutInput,'shortcutInput_主界面').sequence=QKeySequence('Ctrl+Alt+9')
        dialog.findChild(QCheckBox,'shortcutEnabled_保存').setChecked(False)
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
        assert dialog.result()==QDialog.Accepted
        return dialog.result()
    with patch.object(QDialog,'exec',edit_and_save):
        w.open_view_shortcut_settings()
    assert actions['主界面'].shortcut().toString()=='Ctrl+Alt+9'
    assert actions['保存'].shortcut().isEmpty()
    # Reload persisted values into the same actions to verify the startup path.
    install_view_shortcuts(w,w.menu_4,actions)
    assert actions['主界面'].shortcut().toString()=='Ctrl+Alt+9'
    assert actions['保存'].shortcut().isEmpty()
    assert actions['保存'].property('configuredShortcut')=='Ctrl+S'
    print('PASS editable shortcuts, persisted enable/disable and keys, menu order, defaults; submenu section names, direct label click, arrow expansion, section navigation, shortcut titles',flush=True)
os._exit(0)
