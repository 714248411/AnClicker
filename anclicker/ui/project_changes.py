"""Compare persisted project content; navigation and application theme are not edits."""
import hashlib
import json
import openpyxl
from anclicker.ui.project_run_controls import DEFAULTS, project_key

BASELINE_KEY = '本机项目已保存内容'
PROJECT_SETTINGS = set(DEFAULTS) | {'任务名称', '绑定窗口标题', '多功能代码'}

def fingerprint(window):
    workbook = openpyxl.Workbook()
    try:
        window.workspace.repository.export_to_workbook(workbook, window.db)
        rows = {}
        for sheet in workbook:
            values = list(sheet.iter_rows(min_row=2, values_only=True))
            if sheet.title == '设置':
                values = [r for r in values if r[0] == '资源文件夹' or (r[0] == '设置' and r[1] in PROJECT_SETTINGS)]
            rows[sheet.title] = values
        return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str).encode('utf8')).hexdigest()
    finally:
        workbook.close()

def mark_clean(window):
    record = {'path': project_key(window.db.get_setting_value('当前文件路径')), 'digest': fingerprint(window)}
    window.db.set_setting_value(BASELINE_KEY, json.dumps(record))
    window._project_saved_state = record

def is_modified(window):
    controls = getattr(window, 'project_run_controls', None)
    if controls is not None:
        controls.changed()
    view = getattr(window, 'view_workspace', None)
    if view is not None and hasattr(view, '_save_code'):
        view._save_code()
    record = getattr(window, '_project_saved_state', None)
    if record is None:
        try:
            record = json.loads(window.db.get_setting_value(BASELINE_KEY) or '{}')
        except (TypeError, ValueError):
            record = {}
    if not isinstance(record, dict) or record.get('path') != project_key(window.db.get_setting_value('当前文件路径')) or not record.get('digest'):
        return bool(window.workspace.repository.list_commands())
    return fingerprint(window) != record['digest']
