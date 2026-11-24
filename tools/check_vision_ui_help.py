import os,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QMenu
from anclicker.platform.qt_compat.QtGui import QAction, QFont
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.theme import THEMES
from anclicker.ui.view_shortcuts import install_view_shortcuts,active_shortcut_help
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instruction_fields.vision_tools import TYPES
from anclicker.ui.settings_theme import apply_settings_theme
app=QApplication([]);app.setFont(QFont("Microsoft YaHei",10))
output=Path('artifacts/validation/vision-tools');output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
    os.environ['ANCLICKER_DATA_DIR']=temp
    db=DatabaseOperation(str(Path(temp)/'命令集.db'))
    window=QMainWindow();window.db=db;window.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode='light')
    actions={name:QAction(name,window) for name in ('导入单文件','导入文件夹…','导入项目…')}
    db.set_setting_value('视图快捷键',json.dumps({'导入指令':{'key':'Ctrl+D','enabled':True},'导入文件夹内所有表格文件…':{'key':'Ctrl+Shift+D','enabled':False},'导入整体数据…':{'key':'Ctrl+Alt+D','enabled':True}}))
    install_view_shortcuts(window,QMenu(window),actions);window._view_shortcut_actions=actions
    rows=active_shortcut_help(window)
    assert len(rows)==2 and any('导入单文件' in r[1] for r in rows) and any('导入项目' in r[1] for r in rows)
    assert not any('文件夹' in r[1] for r in rows)
    window._registered_shortcut_help={'开始运行':'F10'}
    assert ('F10','开始运行（全局）') in active_shortcut_help(window)
    print('PASS renamed shortcut settings preserved; disabled/unassigned entries omitted from help')
    from anclicker.app.Start_Win import About
    for mode in ('light','dark'):
        window.view_workspace.theme_mode=mode
        about=About(window);about.setAttribute(Qt.WA_DontShowOnScreen,True);about.resize(650,650);about.show();app.processEvents()
        assert about.label_2.openExternalLinks() and 'www.anclicker.com' in about.label_2.text() and 'www.anclicker.eogee.com' in about.label_2.text()
        about.grab().save(str(output/('about-'+mode+'.png')));about.close()
        for name in TYPES:
            editor=get_instruction_spec(name).create_editor(context=ExecutionContext(metadata={'database':db}))
            editor.setAttribute(Qt.WA_DontShowOnScreen,True);apply_settings_theme(editor,window);editor.resize(700,700);editor.show();app.processEvents()
            editor.grab().save(str(output/(name+'-'+mode+'.png')));editor.close()
    print('PASS all vision editors and About render in light/dark themes')
