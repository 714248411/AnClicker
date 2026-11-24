"""Whole Data transfer actions, separate from single-workbook import."""
from pathlib import Path
import shutil
from anclicker.platform.qt_compat.QtGui import QAction
from anclicker.platform.qt_compat.QtWidgets import QFileDialog, QMessageBox, QApplication, QInputDialog
from anclicker.storage.data_bundle import prepare_import, validate_import_data
from anclicker.storage.project_catalog import available_projects
from anclicker.storage.workspace_bundle import (current_project, export_project, export_workspace,
    prepare_workspace_import, read_global_settings, write_global_settings, configure_project)


def new_project(window):
    """Prepare a fresh partition, then restart so every storage service follows it."""
    if busy(window):
        window.statusBar.showMessage('请先停止运行、录制或指令测试，再新建项目。', 6000)
        return False
    view = window.view_workspace
    recording = getattr(view, 'recording_page', None)
    if ((recording and recording.drafts and not recording.written)
            or getattr(getattr(view, 'web_recording_page', None), 'unsaved', False)):
        QMessageBox.warning(window, '录制尚未写入', '请先写入或清空录制内容，再新建项目。')
        return False
    from anclicker.ui.project_changes import is_modified
    if is_modified(window):
        answer = QMessageBox.question(window, '新建项目', '是否保存当前页面？',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        if answer == QMessageBox.Cancel or (answer == QMessageBox.Yes and not window.save_data('自动保存')):
            return False
    import tempfile
    import openpyxl
    from anclicker.storage.database import DatabaseOperation
    from anclicker.storage.data_partitions import next_partition
    from anclicker.storage.workbook_codec import write_graph_sheets
    from anclicker.domain.graph_models import START_NODE_ID, END_NODE_ID
    parent = Path(window.db.db_path).resolve().parent.parent
    destination = next_partition(parent)
    stage = None
    scheduler = getattr(window, 'task_scheduler', None)
    window._update_preparing = True
    if scheduler:
        scheduler.timer.stop()
    try:
        stage = Path(tempfile.mkdtemp(prefix='.anclicker-import-', dir=parent))
        data = stage / 'Data'
        db = DatabaseOperation(str(data / '命令集.db'))
        (data / 'images').mkdir(exist_ok=True)
        write_global_settings(db.db_path, read_global_settings(window.db.db_path))
        configure_project(db.db_path, destination, [*available_projects(window.db), destination])
        book = openpyxl.Workbook()
        try:
            write_graph_sheets(book, [], [(START_NODE_ID, None, 'start', 0., 0.),
                (END_NODE_ID, None, 'end', 320., 0.)], [(START_NODE_ID, END_NODE_ID, 0)])
            db.export_settings_to_excel(book, project_only=True)
            db.import_instruction_workbook(book)
            book.save(data / '空白页1.xlsx')
        finally:
            book.close()
        db.set_setting_value('当前文件路径', str(destination / '空白页1.xlsx'))
        db.writes_to_recently_opened_files(str(destination / '空白页1.xlsx'))
        app = QApplication.instance()
        app._whole_data_import = (str(stage), str(destination), False, True, True)
        if not window.close():
            app._whole_data_import = None
            return False
        stage = None
        app.quit()
        return True
    except Exception as error:
        QMessageBox.warning(window, '新建项目失败', str(error))
        return False
    finally:
        window._update_preparing = False
        if stage:
            shutil.rmtree(stage)
        if scheduler and not getattr(QApplication.instance(), '_whole_data_import', None):
            scheduler.timer.start()


def busy(window):
    view = window.view_workspace
    return (window.command_thread.isRunning()
            or bool(getattr(window, 'task_scheduler', None) and window.task_scheduler.busy)
            or any(bool(getattr(getattr(view, name, None), 'busy', False))
                   for name in ('recording_page', 'web_recording_page', 'agent_page'))
            or getattr(window.workspace, '_instruction_test_active', False)
            or getattr(window, '_update_preparing', False))


def export_selected_project(window):
    if busy(window):
        window.statusBar.showMessage('请先停止运行、录制或指令测试，再导出项目。', 6000)
        return
    projects = available_projects(window.db)
    active = current_project(window.db)
    labels = [f'{path.name} — {path}' for path in projects]
    if not labels:
        QMessageBox.warning(window, '导出项目', '没有可导出的项目目录。')
        return
    choice, accepted = QInputDialog.getItem(window, '导出项目', '选择要导出的项目：', labels,
                                           projects.index(active) if active in projects else 0, False)
    if accepted and choice in labels:
        _export(window, projects[labels.index(choice)])


def _export(window, project=None):
    title = '导出项目' if project is not None else '导出整体数据'
    data = Path(window.db.db_path).parent
    suggested = data.parent / (f'{project.name}-项目.zip' if project is not None else 'AnClicker-整体数据.zip')
    filename, _ = QFileDialog.getSaveFileName(window, title, str(suggested), 'AnClicker 数据包 (*.zip)')
    if not filename:
        return
    if busy(window):
        window.statusBar.showMessage('任务正在运行，请停止后再导出。', 6000)
        return
    scheduler = getattr(window, 'task_scheduler', None)
    window._update_preparing = True
    if scheduler:
        scheduler.timer.stop()
    try:
        window.view_workspace._save_code()
        controls = getattr(window, 'project_run_controls', None)
        if controls is not None:
            controls.changed()
        if project is None:
            export_workspace(window.db, filename)
            message = '整体数据已导出，包含所有项目、引用资源和全局软件设置。'
        else:
            export_project(window.db, project, filename)
            message = f'项目 {project.name} 已导出，包含项目参数和引用资源。'
        window.statusBar.showMessage(message, 10000)
    except Exception as error:
        QMessageBox.warning(window, title + '失败', str(error))
    finally:
        window._update_preparing = False
        if scheduler:
            scheduler.timer.start()


def import_workspace(window):
    if busy(window):
        window.statusBar.showMessage('请先停止运行、录制或指令测试，再导入整体数据。', 6000)
        return
    parent = Path(window.db.db_path).parent.parent
    filename, _ = QFileDialog.getOpenFileName(window, '导入整体数据', str(parent), 'AnClicker 整体数据包 (*.zip)')
    if not filename or busy(window):
        return
    stage = None
    scheduler = getattr(window, 'task_scheduler', None)
    window._update_preparing = True
    if scheduler:
        scheduler.timer.stop()
    try:
        stage, plan = prepare_workspace_import(filename, parent)
        projects = '\n'.join(f"{item['name']} → {item['destination']}" for item in plan['projects'])
        answer = QMessageBox.question(window, '导入整体数据',
            f'将恢复 {len(plan["projects"])} 个项目和全局软件设置：\n{projects}\n\n'
            '同名项目将先备份再替换，其他现有项目保留。完成后软件自动重启。\n是否继续？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        app = QApplication.instance()
        app._whole_workspace_import = (str(stage), str(parent))
        if not window.close():
            app._whole_workspace_import = None
            return
        stage = None
        app.quit()
    except Exception as error:
        QMessageBox.warning(window, '导入整体数据失败', str(error))
    finally:
        window._update_preparing = False
        if stage:
            shutil.rmtree(stage)
        if scheduler and not getattr(QApplication.instance(), '_whole_workspace_import', None):
            scheduler.timer.start()


def transfer(window, importing=False):
    if busy(window):
        window.statusBar.showMessage('请先停止运行、录制或指令测试，再传输整体数据。', 6000)
        return
    data = Path(window.db.db_path).parent
    if not importing:
        _export(window)
        return
    filename, _ = QFileDialog.getOpenFileName(window, '导入项目', str(data.parent), 'AnClicker 项目包 (*.zip)')
    if not filename:
        return
    if busy(window):
        window.statusBar.showMessage('任务正在运行，请停止后再导入。', 6000)
        return
    stage = None
    window._update_preparing = True
    scheduler = getattr(window, 'task_scheduler', None)
    if scheduler:
        scheduler.timer.stop()
    try:
        from anclicker.storage.data_partitions import next_partition
        answer = QMessageBox.question(window, '是否分区导入',
            '是否建立独立分区？\n是：导入 Data1、Data2…，保留已有分区，定时任务需手动开启。\n否：导入 Data，原 Data 自动备份。',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        if answer == QMessageBox.Cancel:
            return
        destination = next_partition(data.parent) if answer == QMessageBox.Yes else data.parent / 'Data'
        stage = prepare_import(filename, data.parent, validate_resources=False)
        portable_project = (stage / 'Data' / 'project-export.json').is_file()
        if portable_project:
            validate_import_data(stage / 'Data')
        from anclicker.storage.data_partitions import bundle_needs_adaptation
        adapt = not portable_project and bundle_needs_adaptation(stage / 'Data')
        if adapt and QMessageBox.question(window, '是否适配资源路径',
                '数据包存在不可用的原路径。是否按目录适配到导入分区？只在当前 AnClicker 的 Data 分区内查找。\n选择否将取消导入。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        if adapt:
            from anclicker.storage.data_partitions import adapt_bundle
            adapt_bundle(stage / 'Data', destination, data.parent)
        # A project carries task parameters; the application's settings remain shared.
        write_global_settings(stage / 'Data' / '命令集.db', read_global_settings(window.db.db_path))
        configure_project(stage / 'Data' / '命令集.db', destination, [*available_projects(window.db), destination])
        app = QApplication.instance()
        app._whole_data_import = (str(stage), str(destination), portable_project, answer == QMessageBox.Yes)
        if not window.close():
            app._whole_data_import = None
            return
        stage = None  # main() owns the prepared directory after successful close.
        app.quit()
    except Exception as error:
        QMessageBox.warning(window, '导入项目失败', str(error))
    finally:
        window._update_preparing = False
        if stage:
            shutil.rmtree(stage)
        if scheduler and not getattr(QApplication.instance(), '_whole_data_import', None):
            scheduler.timer.start()


def install_data_transfer(window):
    anchor = window.action_import_project_folder
    actions = window.menu.actions()
    index = actions.index(anchor) + 1
    before = actions[index] if index < len(actions) else None
    for label, name, callback in (
            ('导入项目…', 'actionImportWholeData', lambda: transfer(window, True)),
            ('导出项目…', 'actionExportProject', lambda: export_selected_project(window)),
            ('导入整体数据…', 'actionImportWorkspace', lambda: import_workspace(window)),
            ('导出整体数据…', 'actionExportWholeData', lambda: transfer(window, False))):
        action = QAction(label, window)
        action.setObjectName(name)
        action.triggered.connect(lambda checked=False, callback=callback: callback())
        window.menu.insertAction(before, action)
        if name == 'actionImportWholeData':
            window.action_import_whole_data = action
            action.setToolTip('导入单个项目包，保留当前软件设置')
        elif name == 'actionImportWorkspace':
            window.action_import_workspace = action
            action.setToolTip('恢复整体数据包中的所有项目和软件设置')
        elif name == 'actionExportProject':
            window.action_export_project = action
        else:
            window.action_export_workspace = action
