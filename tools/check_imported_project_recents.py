"""Project imports list every executable workbook in the imported partition."""
import os, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from openpyxl import Workbook
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.data_bundle import export_data, prepare_import, apply_import
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.recent_projects import RecentProjectPicker
app = QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    source = root / 'source' / 'Data'
    source.mkdir(parents=True)
    db = DatabaseOperation(str(source / '命令集.db'))
    repository = GraphRepository(db.db_path, data_folder=source)
    book = Workbook()
    repository.export_to_workbook(book, db)
    for index in range(25):
        path = source / 'projects' / str(index // 5) / f'流程{index:02}.xlsx'
        path.parent.mkdir(parents=True, exist_ok=True)
        book.save(path)
    book.close()
    first = source / 'projects' / '0' / '流程00.xlsx'
    backup = source / 'migration_backups' / '备份.xlsx'
    backup.parent.mkdir()
    shutil.copy2(first, backup)
    shutil.copy2(first, source / '~$临时.xlsx')
    book = Workbook(); book.active['A1'] = '普通数据'; book.save(source / '数据.xlsx'); book.close()
    db.writes_to_recently_opened_files(str(first))
    archive = export_data(source, root / '项目.zip')
    target = root / 'target' / 'Data1'
    target.parent.mkdir()
    stage = prepare_import(archive, target.parent)
    apply_import(stage, target, adapt=False, new_partition=True)
    imported = DatabaseOperation(str(target / '命令集.db'))
    paths = imported.get_recently_opened_file('文件列表')
    assert len(paths) == 25, paths
    assert all(Path(path).is_relative_to(target / 'projects') and Path(path).is_file() for path in paths)
    imported.writes_to_recently_opened_files(paths[-1])
    paths = imported.get_recently_opened_file('文件列表')
    assert len(paths) == 25
    picker = RecentProjectPicker()
    picker.refresh(paths, paths[0])
    assert picker.combo.count() == 25
    assert picker.combo.itemData(24) in paths
    picker.close()
print('PASS imported 25 nested executable files; excludes data, temp and backups; destination paths; reopen preserves all; picker displays all')
