import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtGui import QFont
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext,InstructionDraft
from anclicker.storage.database import DatabaseOperation
from anclicker.instructions.registry import get_instruction_spec
from anclicker.ui.settings_theme import apply_settings_theme
from anclicker.ui.theme import THEMES
app=QApplication([]);app.setFont(QFont('Microsoft YaHei',10))
with tempfile.TemporaryDirectory() as folder:
    db=DatabaseOperation(str(Path(folder)/'test.db'))
    context=ExecutionContext(metadata={'database':db})
    host=QMainWindow();host.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode='light')
    out=Path('artifacts/validation/parallel');out.mkdir(parents=True,exist_ok=True)
    for name in ('多线程启动','多线程关闭','多线程血量判断'):
        editor=get_instruction_spec(name).create_editor(context=context,draft=InstructionDraft(name,error_policy='自动跳过'))
        assert editor.error_policy.currentText()=='自动跳过'
        for mode in ('light','dark'):
            host.view_workspace.theme_mode=mode;apply_settings_theme(editor,host)
            editor.setAttribute(Qt.WA_DontShowOnScreen,True);editor.show();app.processEvents()
            editor.grab().save(str(out/(name+'-'+mode+'.png')));editor.hide()
        if name=='多线程关闭':
            editor._controls['关闭范围'].setCurrentText('全部线程');editor._controls['线程名称'].clear()
            assert editor.get_draft().parameters['关闭范围']=='全部线程'
        if name=='多线程血量判断':
            editor._controls['操作'].setCurrentText('单次判断');assert editor._controls['冷却'].isHidden()
            editor._controls['操作'].setCurrentText('停止监控');assert editor._controls['区域'].isHidden()
        editor.close();editor.deleteLater()
print('PASS editor option persistence, conditional controls, light/dark rendering')
