import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
folder=tempfile.mkdtemp(prefix='anclicker-new-window-')
os.environ['ANCLICKER_DATA_DIR']=folder
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox
app=QApplication([])
from anclicker.app.Start_Win import Main_window
from anclicker.ui.project_files import new_blank_page
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(QMessageBox,'question',return_value=QMessageBox.No),patch.object(QMessageBox,'warning'),patch.object(QMessageBox,'critical'):
    w=Main_window()
    assert new_blank_page(w)
    path=w.db.get_setting_value('当前文件路径')
    assert Path(path).name=='空白页1.xlsx',path
    assert Path(path).is_file()
    assert w.recent_project_picker.combo.currentData()==path
    assert any(a.data()==path for a in w.menuzv.actions())
    base=Path(path).parent
    old=Path(path)
    # Persist one populated blank page; it must survive cleanup.
    from anclicker.domain.instructions import InstructionDraft
    from anclicker.ui.project_files import NEW_PROJECT_PATH
    w.workspace.repository.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'})])
    w.db.set_setting_value(NEW_PROJECT_PATH,str(base/'空白页2.xlsx'))
    assert w.save_data('保存新空白页')
    populated=base/'空白页2.xlsx'
    original=populated.read_bytes()
    assert new_blank_page(w)
    assert Path(w.db.get_setting_value('当前文件路径')).name=='空白页3.xlsx'
    assert old.exists()
    assert populated.read_bytes()==original
    assert str(old) in w.db.get_recently_opened_file('文件列表')
    for number in (4,5,6):
        previous=Path(w.db.get_setting_value('当前文件路径'))
        identity=previous.stat().st_ino
        original_blank=previous.read_bytes()
        with patch('anclicker.ui.project_files.os.unlink',side_effect=AssertionError('must not delete')):
            assert new_blank_page(w)
        current=w.db.get_setting_value('当前文件路径')
        assert Path(current).name==f'空白页{number}.xlsx'
        assert previous.exists()
        assert previous.stat().st_ino==identity
        assert previous.read_bytes()==original_blank
        assert Path(current).is_file()
        assert populated.read_bytes()==original
        assert w.recent_project_picker.combo.currentData()==current
        assert any(a.data()==current for a in w.menuzv.actions())
        assert str(previous) in w.db.get_recently_opened_file('文件列表')
        app.processEvents()
    from anclicker.platform.qt_compat.QtCore import Qt
    assert w.view_workspace.main_page.recent.currentItem().data(Qt.UserRole)==current
    # Failure to save the new blank must not delete the previous blank.
    previous=Path(current)
    with patch('anclicker.ui.project_files.open',side_effect=PermissionError('locked')):
        assert not new_blank_page(w)
    assert previous.exists()
    print('PASS full window: numbering increases with fresh pages, prior page content and identity preserved, populated file preserved, save failure preserves old blank, all lists synchronized',flush=True)
os._exit(0)
