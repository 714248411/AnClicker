"""File-menu actions for starting a fresh task without losing its saved copy."""
import os
import re
import openpyxl
from pathlib import Path
from anclicker.app.state import application_state
from anclicker.ui.compact_file_menu import install_compact_file_menus
from anclicker.ui.file_menu_icons import file_menu_icon
from anclicker.platform.qt_compat.QtGui import QAction, QKeySequence
from anclicker.platform.qt_compat.QtWidgets import QMessageBox
from anclicker.ui.workspace_constants import CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING
from anclicker.storage.workbook_codec import write_graph_sheets
from anclicker.domain.graph_models import START_NODE_ID, END_NODE_ID
from anclicker.storage.project_catalog import remember_project


NEW_PROJECT_PATH = '本机新建默认保存路径'
PROJECT_DIRECTORY = '本机项目默认保存目录'


def project_directory(db):
    """Use the last selected/opened project directory instead of a fixed Data path."""
    selected = db.get_setting_value(PROJECT_DIRECTORY)
    if selected:
        return os.path.abspath(selected)
    current = db.get_setting_value('当前文件路径')
    if current and current != 'None':
        return os.path.dirname(os.path.abspath(current))
    suggested = db.get_setting_value(NEW_PROJECT_PATH)
    if suggested:
        return os.path.dirname(os.path.abspath(suggested))
    return os.path.join(os.path.dirname(os.path.abspath(db.db_path)), 'exports')


def remember_project_directory(db, path, *, opened=False):
    """Keep the project root through page creation and Save As; opening elsewhere switches it."""
    selected = db.get_setting_value(PROJECT_DIRECTORY)
    if selected:
        if not opened or Path(path).resolve().is_relative_to(Path(selected).resolve()):
            remember_project(db, selected)
            return
    db.set_setting_value(PROJECT_DIRECTORY, os.path.dirname(os.path.abspath(path)))
    remember_project(db, os.path.dirname(os.path.abspath(path)))

def is_blank_project_path(path):
    return bool(path and re.fullmatch(r'空白页[0-9]+', Path(path).stem))


def next_project_path(path, *, fill_gaps=False):
    source = Path(path)
    match = re.search(r'([0-9]+)$', source.stem)
    prefix = source.stem[:match.start()] if match else source.stem
    number = int(match.group()) + 1 if match and not fill_gaps else 1
    width = len(match.group()) if match and match.group().startswith('0') else 1
    while True:
        candidate = source.with_name(prefix + str(number).zfill(width) + '.xlsx')
        if not candidate.exists():
            return str(candidate)
        number += 1


def latest_blank_page(path):
    directory = Path(path).parent
    try:
        candidates = []
        for item in directory.iterdir():
            match = re.fullmatch(r'空白页([0-9]+)\.xlsx', item.name, re.IGNORECASE)
            if match and int(match.group(1)) > 0 and item.is_file():
                candidates.append((int(match.group(1)), item.name, item))
        return str(max(candidates)[2]) if candidates else None
    except OSError:
        return None


def has_user_code(code):
    # Empty flows generate explanatory comments; these are not executable content.
    return any(line.strip() and not line.lstrip().startswith('#')
               for line in str(code or '').splitlines())


def blank_file_is_empty(window, path):
    workbook = None
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
        window.workspace.repository.validate_workbook(workbook)
        if any(any(value is not None for value in row)
               for row in workbook.worksheets[0].iter_rows(min_row=2, values_only=True)):
            return False
        for row in workbook['设置'].iter_rows(min_row=2, values_only=True):
            if len(row) >= 3 and row[0] == '设置' and row[1] == CODE_SETTING and has_user_code(row[2]):
                return False
        return True
    except Exception:
        return False
    finally:
        if workbook is not None:
            workbook.close()


def install_new_blank_action(window):
    action=QAction('新建空白页',window)
    action.setObjectName('actionNewBlankPage')
    action.setIcon(file_menu_icon('new'))
    action.setIconVisibleInMenu(True)
    action.setShortcut(QKeySequence('Ctrl+N'))
    action.triggered.connect(lambda:new_blank_page(window))
    window.menu.insertAction(window.menu.actions()[0] if window.menu.actions() else None,action)
    window.action_new_blank=action
    project_action = QAction('新建项目', window)
    project_action.setObjectName('actionNewProject')
    project_action.setIcon(file_menu_icon('folder'))
    project_action.setIconVisibleInMenu(True)
    from anclicker.ui.data_transfer import new_project
    project_action.triggered.connect(lambda: new_project(window))
    actions = window.menu.actions()
    window.menu.insertAction(actions[1] if len(actions) > 1 else None, project_action)
    window.action_new_project = project_action
    install_compact_file_menus(window)


def new_blank_page(window):
    if not application_state(window).can_edit_project():
        window.statusBar.showMessage('请先停止任务、录制或指令测试，再新建空白页。',5000)
        return False
    view=window.view_workspace
    recording=getattr(view,'recording_page',None)
    web_recording=getattr(view,'web_recording_page',None)
    if (recording and recording.drafts and not recording.written) or getattr(web_recording,'unsaved',False):
        QMessageBox.warning(window,'录制尚未写入','请先写入或清空录制内容，再新建空白页。')
        return False
    from anclicker.ui.project_changes import is_modified
    modified = is_modified(window)
    destination_directory = project_directory(window.db)
    current_path = window.db.get_setting_value('当前文件路径') or ''
    if modified:
        save_label = Path(current_path).name if current_path and current_path != 'None' else '编辑中的文件'
        answer=QMessageBox.question(window,'新建空白页',f'是否保存“{save_label}”？',
                                   QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)
        if answer==QMessageBox.Yes:
            if not window.save_data('自动保存'):return False
        elif answer!=QMessageBox.No:
            return False
    controls = getattr(window, 'project_run_controls', None)
    if controls is not None: controls.changed()
    blank_base = Path(destination_directory) / '空白页.xlsx'
    latest = latest_blank_page(blank_base)
    suggested_path = next_project_path(latest or blank_base)
    # Write a fresh page with the current project's parameters before replacing
    # the workspace. An old empty page must never become a settings template.
    workbook = openpyxl.Workbook()
    try:
        write_graph_sheets(workbook, [], [
            (START_NODE_ID, None, 'start', 0.0, 0.0),
            (END_NODE_ID, None, 'end', 320.0, 0.0),
        ], [(START_NODE_ID, END_NODE_ID, 0)])
        window.db.export_settings_to_excel(workbook, project_only=True)
        for row in workbook['设置'].iter_rows(min_row=2):
            if row[0].value == '设置' and row[1].value in (CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING):
                row[2].value = ''
        window.workspace.repository.validate_workbook(workbook)
        os.makedirs(destination_directory, exist_ok=True)
        while True:
            try:
                destination = open(suggested_path, 'xb')
            except FileExistsError:
                suggested_path = next_project_path(suggested_path)
                continue
            try:
                with destination:
                    workbook.save(destination)
            except Exception:
                os.remove(suggested_path)
                raise
            break
    except Exception as error:
        QMessageBox.warning(window, '空白页保存失败', f'{error}\n当前项目及内容未切换。')
        return False
    finally:
        workbook.close()
    window.data_import(suggested_path, use_cached_controls=False)
    loaded = window.db.get_setting_value('当前文件路径') or ''
    if os.path.normcase(os.path.abspath(loaded)) != os.path.normcase(suggested_path):
        window.statusBar.showMessage('空白页文件已保存，但打开失败；当前项目保持不变。', 5000)
        return False
    for page in (recording,web_recording):
        if page is not None:page.clear()
    window.statusBar.showMessage(f'已在当前项目中新建 {Path(suggested_path).name}，沿用项目参数。', 4000)
    return True
