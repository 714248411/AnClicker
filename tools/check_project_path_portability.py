"""Run real Excel/project instructions after moving packages away from their author."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from unittest.mock import patch
import zipfile
from openpyxl import Workbook, load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft, CommandRecord, ExecutionContext
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.data_bundle import prepare_import, apply_import
from anclicker.storage.workspace_bundle import export_project
from anclicker.storage.project_paths import (resolve_path, resolve_parameters, relative_parameters,
    save_workbook_paths, rebase_saved_commands)
from anclicker.storage.data_partitions import prepare_project_paths
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices, RuntimeDependencies
from anclicker.instructions.registry import get_instruction_spec
from anclicker.storage.portable_migration import relocate_database
from anclicker.storage.data_bundle import relocate_project_files


def write_page(db, path, drafts):
    repo = GraphRepository(db.db_path, data_folder=Path(db.db_path).parent)
    repo.clear()
    repo.append_recording(drafts)
    db.set_setting_value('当前文件路径', str(path))
    book = Workbook()
    repo.export_to_workbook(book, db)
    save_workbook_paths(book, path, path, path.parents[1])
    book.save(path)
    book.close()
    return repo


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    author = root / 'author' / 'Data2'
    pages = author / 'pages'
    pages.mkdir(parents=True)
    child_folder = pages / 'child'
    child_folder.mkdir()
    table = author / 'inputs' / '表格.xlsx'
    table.parent.mkdir()
    book = Workbook()
    book.active['A1'] = 'before'
    book.save(table)
    book.close()
    db = DatabaseOperation(str(author / '命令集.db'))
    db.set_setting_value('本机项目默认保存目录', str(author))
    child = child_folder / '子项目.xlsm'
    write_page(db, child, [InstructionDraft('写入单元格', {'工作簿': str(table), '单元格': 'A1', '文本': 'after-move'})])
    main = pages / '主项目.xlsx'
    repo = write_page(db, main, [InstructionDraft('运行项目', {'项目路径': str(child)}),
        InstructionDraft('获取Excel', {'工作簿': str(table), '单元格': 'A1', '变量': '迁移结果'})])
    archive = export_project(db, author, root / 'cloud-project.zip')
    with zipfile.ZipFile(archive) as package:
        with package.open('Data/pages/主项目.xlsx') as stream:
            exported = load_workbook(stream)
            values = [json.loads(row[2]) for row in exported['命令'].iter_rows(min_row=2, values_only=True)]
            assert values[0]['项目路径'] == 'child/子项目.xlsm'
            assert values[1]['工作簿'] == '../inputs/表格.xlsx'
            exported.close()
    # Keep the author's data online to prove no instruction accidentally uses it.
    local_parent = root / 'local'
    local_parent.mkdir()
    stage = prepare_import(archive, local_parent)
    local = local_parent / 'Data3'
    apply_import(stage, local)
    restored = DatabaseOperation(str(local / '命令集.db'))
    repository = GraphRepository(restored.db_path, data_folder=local)
    errors = []
    engine = ExecutionEngine(ExecutionServices(restored, error_requested=lambda value: errors.append(value['text'])), repository)
    context = ExecutionContext()
    engine.execute(repository.execution_snapshot(), context)
    assert not errors, errors
    assert context.variables['迁移结果'] == 'after-move'
    book = load_workbook(table)
    assert book.active['A1'].value == 'before'
    book.close()
    assert context.metadata['project_path'] == str(local / 'pages' / main.name)

    # Move the already-imported project again, including a renamed Data partition.
    third = root / 'third' / 'Data8'
    third.parent.mkdir()
    shutil.copytree(local, third)
    relocate_database(third / '命令集.db', third)
    relocate_project_files(third, force=True)
    second_db = DatabaseOperation(str(third / '命令集.db'))
    context = ExecutionContext()
    second_repo = GraphRepository(second_db.db_path, data_folder=third)
    ExecutionEngine(ExecutionServices(second_db), second_repo).execute(second_repo.execution_snapshot(), context)
    assert context.variables['迁移结果'] == 'after-move'
    # Dynamic variables are resolved at execution; the stored expression is unchanged.
    command = CommandRecord(500, '获取Excel', {'工作簿': '{{表格路径}}', '单元格': 'A1', '变量': '动态结果'})
    context.variables['表格路径'] = '../inputs/表格.xlsx'
    get_instruction_spec('获取Excel').create_executor().execute(context, command)
    assert context.variables['动态结果'] == 'after-move'
    assert command.parameters['工作簿'] == '{{表格路径}}'
    # Input/output paths are handled; Python, URLs and arbitrary prose are untouched.
    code = 'print("Z:/old/Data2/example.txt")'
    values = resolve_parameters({'保存路径': 'results/new.png', '代码': code, 'url': 'https://example.test/a'},
                                '屏幕截图', third, base=third / 'pages')
    assert values['保存路径'] == str(third / 'pages' / 'results' / 'new.png')
    assert values['代码'] == code and values['url'] == 'https://example.test/a'

    # A plain legacy/cloud workbook can use an exact DataN-relative counterpart automatically.
    probe = Workbook()
    sheet = probe.active
    sheet.title = '命令'
    sheet.append(['ID', '类型标识', '参数JSON'])
    sheet.append([1, '获取Excel', json.dumps({'工作簿': 'Z:/cloud/job/Data25/inputs/表格.xlsx'})])
    assert prepare_project_paths(probe, third / 'pages' / main.name, third, third.parent,
                                 lambda missing: (_ for _ in ()).throw(AssertionError(missing)))
    assert json.loads(sheet.cell(2, 3).value)['工作簿'] == str(third / 'inputs' / '表格.xlsx')
    probe.close()

    # Generated outputs need not exist during export; downstream reads follow the same path.
    output = root / 'author-output' / 'result.png'
    repo.clear()
    repo.append_recording([InstructionDraft('屏幕截图', {'保存路径': str(output)}),
                          InstructionDraft('图像等待', {'图像路径': '{{截图文件}}'})])
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn, conn:
        row = conn.execute("SELECT ID FROM 命令 WHERE 类型标识='图像等待'").fetchone()
        conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?', (json.dumps({'图像路径': str(output)}), row[0]))
    archive2 = export_project(db, author, root / 'generated.zip')
    staged = prepare_import(archive2, root)
    with contextlib.closing(sqlite3.connect(str(staged / 'Data' / '命令集.db'))) as conn:
        records = [json.loads(row[0]) for row in conn.execute('SELECT 参数JSON FROM 命令 ORDER BY 排序')]
        assert records[0]['保存路径'].startswith('../outputs/')
        assert records[1]['图像路径'] == records[0]['保存路径']
    shutil.rmtree(staged)

    # Runtime creates the output parent only when executing the instruction.
    from PIL import Image
    shot = CommandRecord(600, '屏幕截图', {'保存路径': 'results/deep/shot.png', '截图类型': '全屏截图'})
    fake_gui = type('Gui', (), {'screenshot': lambda self, **kwargs: Image.new('RGB', (2, 2))})()
    with patch('anclicker.execution.actions.pyautogui_module', return_value=fake_gui):
        get_instruction_spec('屏幕截图').create_executor().execute(context, shot)
    assert (third / 'pages' / 'results' / 'deep' / 'shot.png').is_file()
    assert shot.parameters['保存路径'] == 'results/deep/shot.png'

    # Background methods store typed paths in JSON, with pipe-separated image lists.
    nested = {'接口': '查找图片 · FindPic', '参数': json.dumps({'pic_name': '../inputs/a.png|../inputs/b.png', 'delta_color': '000000'})}
    fixed = resolve_parameters(nested, '后台图色操作', third, base=third / 'pages')
    arguments = json.loads(fixed['参数'])
    assert arguments['pic_name'] == f'{third / "inputs" / "a.png"}|{third / "inputs" / "b.png"}'
    assert arguments['delta_color'] == '000000'
    portable = relative_parameters(fixed, '后台图色操作', third, third / 'pages')
    assert json.loads(portable['参数'])['pic_name'] == '../inputs/a.png|../inputs/b.png'
    # An external resource directory may itself contain a project with sibling inputs.
    external = root / 'external-library'
    external.mkdir()
    external_table = external / 'book.xlsx'
    shutil.copy2(table, external_table)
    external_page = external / 'task.xlsx'
    scratch = DatabaseOperation(str(root / 'scratch' / 'commands.db'))
    write_page(scratch, external_page, [InstructionDraft('获取Excel', {'工作簿': 'book.xlsx', '单元格': 'A1'})])
    db.writes_to_resource_folder_path(str(external))
    repo.clear()
    repo.append_recording([InstructionDraft('运行项目', {'项目路径': str(external_page)})])
    ext_archive = export_project(db, author, root / 'external-project.zip')
    external.rename(root / 'external-offline')
    staged = prepare_import(ext_archive, root)
    files = list((staged / 'Data' / 'resources').rglob('task.xlsx'))
    assert len(files) == 1
    book = load_workbook(files[0])
    assert json.loads(book['命令'].cell(2, 3).value)['工作簿'] == 'book.xlsx'
    book.close()
    shutil.rmtree(staged)

print('PASS relative project archives, real Excel read/write, XLSM child projects, author isolation, second migration, variable paths, generated outputs, local output directories, automatic legacy DataN rebasing')
