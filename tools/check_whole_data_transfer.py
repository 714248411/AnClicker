"""Data-only cross-machine transfer; no personal data touched."""
import contextlib, json, os, shutil, sqlite3, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.data_bundle import export_data, prepare_import, apply_import, relocate_project_files
from anclicker.storage.portable_migration import relocate_database
from openpyxl import Workbook, load_workbook

with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary); source=root/'电脑一'/'Data'; source.mkdir(parents=True)
    external=root/'外部图片'; external.mkdir()
    image=external/'同名.png'; image.write_bytes(b'image-A')
    image2=source/'images'/'子目录'/'同名.png'; image2.parent.mkdir(parents=True);image2.write_bytes(b'image-B')
    reference=external/'输入.xlsx'; wb=Workbook();wb.active['A1']='input';wb.save(reference);wb.close()
    parameters={'图像路径':str(image), 'fromPath':os.path.relpath(reference,source), 'folder':os.path.relpath(external,source), '保存路径':'Z:/output/not-created.txt'}
    db=DatabaseOperation(str(source/'命令集.db'))
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
        conn.execute('INSERT INTO 命令 (ID,类型标识,参数JSON,重复次数,异常处理,备注,排序) VALUES (1,?,?,?,?,?,0)',('图像点击',json.dumps(parameters),1,'自动跳过','内容不变'))
        conn.execute('INSERT INTO 节点 VALUES (?,1,?,10,20)',('command-1','instruction'))
        conn.commit()
    db.set_value_to_variable_table([('图片变量','',str(image))])
    repository=GraphRepository(db.db_path, data_folder=source)
    project=source/'exports'/'项目.xlsx';project.parent.mkdir()
    db.set_setting_value('当前文件路径',str(project));db.writes_to_recently_opened_files(str(project))
    book=Workbook();repository.export_to_workbook(book,db);book['命令'].cell(2,3).value=json.dumps(parameters);book.save(project);book.close()
    archive=root/'整体.zip';export_data(source,archive)
    target=root/'电脑二'/'Data';target.mkdir(parents=True);(target/'保留.txt').write_text('备份')
    stage=prepare_import(archive,target.parent)
    source.rename(source.with_name('离线Data')); external.rename(external.with_name('离线外部'))
    backup=apply_import(stage,target)
    assert (backup/'保留.txt').read_text()=='备份'
    with contextlib.closing(sqlite3.connect(str(target/'命令集.db'))) as conn:
        row=conn.execute('SELECT 参数JSON,备注 FROM 命令').fetchone()
        fixed=Path(json.loads(row[0])['图像路径']);assert fixed.is_relative_to(target) and fixed.read_bytes()==b'image-A';assert row[1]=='内容不变'
        assert Path(conn.execute('SELECT 值 FROM 变量池 WHERE 变量名称=?',('图片变量',)).fetchone()[0]).is_relative_to(target)
        values=json.loads(row[0]);assert Path(values['fromPath']).is_file();assert Path(values['folder']).is_dir();assert values['保存路径']=='Z:/output/not-created.txt'
        assert dict(conn.execute('SELECT 设置项,值 FROM 设置'))['当前文件路径']==str(target/'exports'/'项目.xlsx')
    book=load_workbook(target/'exports'/'项目.xlsx');assert json.loads(book['命令'].cell(2,3).value)['图像路径']==str(fixed);assert book['节点'].max_row==4;book.close()
    third=root/'电脑三'/'Data';shutil.copytree(target,third);target.rename(target.with_name('离线Data'))
    relocate_database(third/'命令集.db',third);relocate_project_files(third)
    with contextlib.closing(sqlite3.connect(str(third/'命令集.db'))) as conn:
        fixed3=Path(json.loads(conn.execute('SELECT 参数JSON FROM 命令').fetchone()[0])['图像路径']);assert fixed3.is_relative_to(third) and fixed3.read_bytes()==b'image-A'
    assert relocate_project_files(third)==0
    bad=root/'bad.zip'
    with zipfile.ZipFile(bad,'w') as out:out.writestr('Data/../../escape','x')
    try:prepare_import(bad,root)
    except ValueError:pass
    else:raise AssertionError('accepted unsafe archive')
    assert not (root/'escape').exists()
    # Failed post-swap path repair restores the original directory atomically.
    from unittest.mock import patch
    rollback=root/'rollback'/'Data';rollback.mkdir(parents=True)
    (rollback/'original.txt').write_text('untouched')
    prepared=prepare_import(archive,rollback.parent)
    with patch('anclicker.storage.data_bundle.relocate_project_files',side_effect=OSError('injected write failure')):
        try:apply_import(prepared,rollback)
        except OSError:pass
        else:raise AssertionError('expected rollback')
    assert (rollback/'original.txt').read_text()=='untouched'
    assert not (rollback/'命令集.db').exists()
    # Missing inputs must never produce a successful incomplete export.
    fixed3.unlink()
    try:export_data(third,root/'missing.zip')
    except ValueError:pass
    else:raise AssertionError('accepted missing file')
    assert not (root/'missing.zip').exists()
print('PASS whole Data: external directory collection, duplicate basenames, graph preservation, backup, cross-machine copy, idempotence, traversal rejection, missing-resource rejection')
