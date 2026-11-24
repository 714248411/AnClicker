"""Real main-window import lifecycle, in a disposable Data directory."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if '--common' in sys.argv:
    os.environ['ANCLICKER_TEST_PARTITION']='0'
if '--workspace' in sys.argv:
    os.environ['ANCLICKER_TEST_WORKSPACE']='1'
if '--project' in sys.argv:
    os.environ['ANCLICKER_TEST_PROJECT']='1'
if '--new' in sys.argv:
    os.environ['ANCLICKER_TEST_NEW']='1'
new = os.environ.get('ANCLICKER_TEST_NEW') == '1'
whole = os.environ.get('ANCLICKER_TEST_WORKSPACE') == '1'
if '--child' not in sys.argv:
    with tempfile.TemporaryDirectory() as folder:
        env=dict(os.environ, ANCLICKER_DATA_DIR=str(Path(folder)/'active'/'Data'), ANCLICKER_SINGLETON_KEY='whole-data-transfer-test-'+Path(folder).name, PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-B','-X','utf8',__file__,'--child',folder],env=env,capture_output=True,text=True,encoding='utf-8',timeout=90)
        print(result.stdout);print(result.stderr)
        if result.returncode:
            raise SystemExit(result.returncode)
        env['ANCLICKER_SMOKE_LIGHTWEIGHT']='1'
        choice=json.loads((Path(env['ANCLICKER_DATA_DIR']).parent/'.active-data.json').read_text())['directory']
        env['ANCLICKER_DATA_DIR']=str(Path(env['ANCLICKER_DATA_DIR']).parent/choice)
        restart=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve().parents[1]/'main.py'),'--release-smoke'],env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
        active=Path(env['ANCLICKER_DATA_DIR'])
        assert restart.returncode==0,(restart.returncode,restart.stdout,restart.stderr)
        assert json.loads((active/'startup-ready.json').read_text(encoding='utf-8'))['ready']
        import sqlite3, contextlib
        with contextlib.closing(sqlite3.connect(str(active/'命令集.db'))) as conn:
            assert conn.execute('SELECT 值 FROM 设置 WHERE 设置项=?',('整体数据测试',)).fetchone()[0]==('imported' if whole else 'local')
        print('PASS fresh process started with imported Data after original process exited')
        raise SystemExit(0)
from unittest.mock import patch
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.data_bundle import export_data
root=Path(sys.argv[-1]); source=root/'source'/'Data';source.mkdir(parents=True)
db=DatabaseOperation(str(source/'命令集.db')); db.set_setting_value('整体数据测试','imported')
db.set_global_shortcut(**{'开始运行':['ctrl','alt','shift','f24'],'结束运行':['ctrl','alt','shift','f23'],'暂停和恢复':['ctrl','alt','shift','f22'],'结束运行2':['ctrl','alt','shift','f21']})
archive=export_data(source,root/'整体.zip')
if whole:
    from anclicker.storage.workspace_bundle import export_workspace
    second = source.parent / 'Data2'
    second.mkdir()
    DatabaseOperation(str(second / '命令集.db'))
    db.set_setting_value('本机项目默认保存目录', str(second))
    archive = export_workspace(db, root / 'all.zip')
elif os.environ.get('ANCLICKER_TEST_PROJECT') == '1':
    from anclicker.storage.workspace_bundle import export_project
    archive = export_project(db, source, root / 'project.zip')
import main
from anclicker.app.Start_Win import Main_window
from anclicker.ui.data_transfer import transfer, import_workspace, new_project
from anclicker.platform.qt_compat.QtCore import QTimer
from anclicker.platform.qt_compat.QtWidgets import QMessageBox
original=Main_window.__init__
errors=[]
def initialize(self):
    original(self)
    names=[action.objectName() for action in self.menu.actions()]
    index=names.index('actionImportProjectFolder')
    assert names[index+1:index+5]==['actionImportWholeData','actionExportProject','actionImportWorkspace','actionExportWholeData']
    self.db.set_setting_value('整体数据测试', 'local')
    self.db.set_global_shortcut(**{'开始运行':['ctrl','alt','shift','f24'],'结束运行':['ctrl','alt','shift','f23'],'暂停和恢复':['ctrl','alt','shift','f22'],'结束运行2':['ctrl','alt','shift','f21']})
    page = self.view_workspace.main_page
    assert [page.open_button.text(), page.folder_button.text(), page.bundle_button.text()] == ['打开文件…', '打开文件夹…', '打开项目…']
    assert self.actionf.text() == '导入单文件'
    assert self.action_import_project_folder.text() == '导入文件夹…'
    assert self.action_import_whole_data.text() == '导入项目…'
    with patch.object(self, 'data_import') as single, patch('anclicker.ui.recent_projects.import_project_folder') as folder, patch('anclicker.ui.data_transfer.transfer') as project:
        page.open_button.click()
        single.assert_called_once()
        folder.assert_not_called()
        project.assert_not_called()
        page.folder_button.click()
        folder.assert_called_once_with(self)
        project.assert_not_called()
        page.bundle_button.click()
        project.assert_called_once_with(self, True)
    print('PASS three home entries route to distinct import actions')
    def perform():
        try:
            if new:
                with patch('anclicker.ui.project_changes.is_modified', return_value=False):
                    assert new_project(self)
            else:
                import_workspace(self) if whole else transfer(self, True)
            if not getattr(main.QApplication.instance(), '_whole_workspace_import' if whole else '_whole_data_import', None):
                raise RuntimeError(self.statusBar.currentMessage())
        except BaseException as error:
            errors.append(str(error));main.QApplication.instance().exit(2)
    main.QApplication.instance()._transfer_probe = perform
original_exec=main.QApplication.exec
def execute(app):
    QTimer.singleShot(0, app._transfer_probe)
    QTimer.singleShot(30000, lambda: app.exit(3))
    return original_exec(app)
with patch('anclicker.platform.qt_compat.QtWidgets.QMessageBox.critical',side_effect=lambda *args: (_ for _ in ()).throw(RuntimeError(str(args[1:])))), patch.object(main.QApplication,'exec',execute), patch.object(Main_window,'register_global_shortcut_keys',lambda self:None), patch.object(Main_window,'__init__',initialize), patch.object(Main_window,'_install_updates',lambda self:None), patch('anclicker.ui.data_transfer.QFileDialog.getOpenFileName',return_value=(str(archive),'')), patch('anclicker.ui.data_transfer.QMessageBox.question',side_effect=lambda parent,title,*args: QMessageBox.No if title=='是否分区导入' and os.environ.get('ANCLICKER_TEST_PARTITION')=='0' else QMessageBox.Yes), patch('subprocess.Popen') as launch, patch('anclicker.ui.data_transfer.QMessageBox.warning', side_effect=lambda *args: (_ for _ in ()).throw(RuntimeError(str(args[1:])))):
    # Disable splash subprocess; the real main window and close handler still run.
    class Splash:
        def finish(self,window):pass
        def deleteLater(self):pass
    with patch.object(main,'show_splash_screen',return_value=Splash()):
        import faulthandler
        faulthandler.dump_traceback_later(12)
        code=main.main()
        faulthandler.cancel_dump_traceback_later()
    assert code==0 and not errors,(code,errors)
    assert any(call.args and isinstance(call.args[0],list) and str(Path(main.__file__).resolve()) in call.args[0] for call in launch.call_args_list), launch.call_count
active=Path(os.environ['ANCLICKER_DATA_DIR'])
assert DatabaseOperation(str(active/'命令集.db')).get_setting_value('整体数据测试')==('imported' if whole else 'local')
assert active.name==('Data2' if whole else ('Data' if os.environ.get('ANCLICKER_TEST_PARTITION')=='0' else 'Data1'))
assert (active.parent/'Data'/'命令集.db').is_file()
if active.name=='Data':
    assert list(active.parent.glob('Data-导入前备份-*'))
print('PASS actual UI: menu order, staged import, real close, backup, Data switch, automatic restart request')
