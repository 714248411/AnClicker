"""Consent, isolation, and partition naming without touching real Data."""
import contextlib, json, os, sqlite3, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from anclicker.storage.data_partitions import *
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.data_bundle import export_data, prepare_import, apply_import

with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary)/'AnClicker';root.mkdir()
    data=root/'Data';data.mkdir();data1=root/'Data1';data1.mkdir()
    assert next_partition(root).name=='Data2'
    (root/'Data2').write_text('collision');assert next_partition(root).name=='Data3'
    image=data1/'images'/'测试.png';image.parent.mkdir();image.write_bytes(b'partition1')
    external=Path(temporary)/'external';external.mkdir();(external/'outside.png').write_bytes(b'outside')
    db=DatabaseOperation(str(data/'命令集.db'))
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        conn.execute('INSERT INTO 命令 VALUES (1,?,?,?,?,?,0)',('图像点击',json.dumps({'图像路径':str(image)}),1,'自动跳过','keep'))
        conn.execute('INSERT INTO 节点 VALUES (?,1,?,0,0)',('node-1','instruction'));conn.commit()
    repo=GraphRepository(db.db_path,data_folder=data)
    book=Workbook();repo.export_to_workbook(book,db)
    book['命令'].cell(2,3).value=json.dumps({'图像路径':str(image)})
    original=book['命令'].cell(2,3).value
    assert prepare_project_paths(book,data1/'项目.xlsx',data,root,lambda _:(_ for _ in ()).throw(AssertionError('unnecessary prompt')))
    repo.import_from_workbook(book,source_path=str(data1/'项目.xlsx'),preserve_paths=True)
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        assert json.loads(conn.execute('SELECT 参数JSON FROM 命令').fetchone()[0])['图像路径']==str(image)
    assert book['命令'].cell(2,3).value==original
    portable='Z:/old/Data2/images/测试.png';book['命令'].cell(2,3).value=json.dumps({'图像路径':portable})
    assert prepare_project_paths(book,data1/'项目.xlsx',data,root,lambda _:(_ for _ in ()).throw(AssertionError('exact relative mapping must be automatic')))
    assert json.loads(book['命令'].cell(2,3).value)['图像路径']==str(image)
    missing='Z:/old/unmapped/测试.png';book['命令'].cell(2,3).value=json.dumps({'图像路径':missing})
    before=book['命令'].cell(2,3).value
    assert not prepare_project_paths(book,data1/'项目.xlsx',data,root,lambda _:False)
    assert book['命令'].cell(2,3).value==before
    assert prepare_project_paths(book,data1/'项目.xlsx',data,root,lambda _:True)
    assert json.loads(book['命令'].cell(2,3).value)['图像路径']==str(image)
    assert find_adaptation(missing,root,data1)==str(image)
    try:find_adaptation('Z:/outside.png',root,data1)
    except ValueError:pass
    else:raise AssertionError('searched outside AnClicker')
    another=root/'Data4';another.mkdir();(another/'dup.png').write_bytes(b'A');(data/'dup.png').write_bytes(b'B')
    try:find_adaptation('Z:/dup.png',root,data1)
    except ValueError:pass
    else:raise AssertionError('ambiguous image chosen')
    select_partition(data);assert selected_partition(root)==data
    (root/SELECTION).write_text(json.dumps({'directory':'../external'}));assert selected_partition(root)==data
    # A restored project asks before running instead of silently switching images.
    from types import SimpleNamespace
    from unittest.mock import patch
    from anclicker.platform.qt_compat.QtWidgets import QMessageBox
    host=SimpleNamespace(db=db,workspace=SimpleNamespace(reload_graph=lambda **kw:None),view_workspace=SimpleNamespace(refresh_all=lambda:None))
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        conn.execute('UPDATE 命令 SET 参数JSON=?',(json.dumps({'图像路径':missing}),));conn.commit()
    with patch.object(QMessageBox,'question',return_value=QMessageBox.No):
        assert not ensure_runtime_paths(host)
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        assert json.loads(conn.execute('SELECT 参数JSON FROM 命令').fetchone()[0])['图像路径']==missing
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
        assert ensure_runtime_paths(host)
    archive=export_data(data,Path(temporary)/'whole.zip')
    stage=prepare_import(archive,root)
    destination=next_partition(root)
    assert apply_import(stage,destination,adapt=False) is None
    assert (data/'命令集.db').is_file() and (destination/'命令集.db').is_file()
    select_partition(destination);assert selected_partition(root)==destination
    # Missing resources are adapted only after the explicit consent stage.
    stage=prepare_import(archive,root,validate_resources=False)
    with contextlib.closing(sqlite3.connect(str(stage/'Data'/'命令集.db'))) as conn:
        conn.execute('UPDATE 命令 SET 参数JSON=?',(json.dumps({'图像路径':'Z:/old/Data/images/测试.png'}),))
        conn.commit()
    DatabaseOperation(str(stage/'Data'/'命令集.db')).set_setting_value('定时运行任务',json.dumps([{'enabled':True,'status':'等待执行'}]))
    assert bundle_needs_adaptation(stage/'Data')
    second=next_partition(root)
    adapt_bundle(stage/'Data',second,root)
    apply_import(stage,second,adapt=False,new_partition=True)
    with contextlib.closing(sqlite3.connect(str(second/'命令集.db'))) as conn:
        chosen=json.loads(conn.execute('SELECT 参数JSON FROM 命令').fetchone()[0])['图像路径']
        assert Path(chosen).is_file() and Path(chosen).is_relative_to(second)
        assert json.loads(conn.execute('SELECT 值 FROM 设置 WHERE 设置项=?',('定时运行任务',)).fetchone()[0])[0]['enabled'] is False
    # Startup selection is remembered, but explicit env overrides still win.
    from unittest.mock import patch
    from anclicker.app.startup_environment import prepare_environment
    with patch.dict(os.environ,{'ANCLICKER_DATA_DIR':''}),patch('anclicker.app.startup_environment.get_install_folder',return_value=str(root)):
        assert prepare_environment()==destination
    from anclicker.platform.image_paths import resolve_image_reference
    assert resolve_image_reference('images/测试.png',project_path=data1/'项目.xlsx',data_folder=data,allow_adaptation=False)==str(image)
    unresolved=resolve_image_reference(missing,project_path=data1/'项目.xlsx',data_folder=data,allow_adaptation=False)
    assert unresolved.replace('\\','/')==missing
    print('PASS partitions: numbering, no overwrite, persistent selection, automatic exact project rebasing, scoped legacy adaptation, ambiguity rejection')
