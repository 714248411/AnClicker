"""Project-local run controls, persisted without exporting other project paths."""
import json
import os
from anclicker.platform.qt_compat.QtCore import QSignalBlocker

CACHE_KEY = '本机项目控制设置'
DEFAULTS = {'运行重复次数': '1', '运行未连接模块': 'True', '执行中隐藏主窗口': 'False'}

def project_key(path):
    return os.path.normcase(os.path.abspath(path)) if path and path != 'None' else ''

class ProjectRunControls:
    def __init__(self, window):
        self.window = window
        self.path = project_key(window.db.get_setting_value('当前文件路径'))
        self.restoring = False
        self.restore(self.path)
        window.radioButton.toggled.connect(self.changed)
        window.radioButton_2.toggled.connect(self.changed)
        window.spinBox.valueChanged.connect(self.changed)
        window.run_unconnected_checkbox.toggled.connect(self.changed)
        window.checkBox_2.toggled.connect(self.changed)

    def cache(self):
        try:
            value = json.loads(self.window.db.get_setting_value(CACHE_KEY) or '{}')
            return value if isinstance(value, dict) else {}
        except (ValueError, TypeError):
            return {}

    def values(self):
        w = self.window
        return {'运行重复次数': str(-1 if w.radioButton.isChecked() else w.spinBox.value()),
                '有限重复次数': str(w.spinBox.value()),
                '运行未连接模块': str(w.run_unconnected_checkbox.isChecked()),
                '执行中隐藏主窗口': str(w.checkBox_2.isChecked())}

    def changed(self, *_):
        if self.restoring:
            return
        # Radio buttons emit the old button's toggled(False) before selecting the new one.
        if not (self.window.radioButton.isChecked() or self.window.radioButton_2.isChecked()):
            return
        values = self.values()
        saved = {k: values[k] for k in (*DEFAULTS, '有限重复次数')}
        if self.path:
            cache = self.cache()
            cache[self.path] = values
            saved[CACHE_KEY] = json.dumps(cache, ensure_ascii=False)
        self.window.db.set_setting_values(saved)

    def restore(self, path, imported=None, *, use_cache=True):
        self.path = project_key(path)
        w = self.window
        values = {k: w.db.get_setting_value(k) or default for k, default in DEFAULTS.items()} if imported is None else dict(DEFAULTS, **imported)
        if imported is None and w.db.get_setting_value('有限重复次数') is not None:
            values['有限重复次数'] = w.db.get_setting_value('有限重复次数')
        cached = self.cache().get(self.path) if use_cache else None
        if isinstance(cached, dict):
            values.update({k: v for k, v in cached.items() if k in (*DEFAULTS, '有限重复次数')})
        try:
            repeat = int(values.get('运行重复次数', 1))
            count = int(values.get('有限重复次数', 1)) if repeat == -1 else repeat
        except (TypeError, ValueError):
            repeat, count = 1, 1
        widgets = (w.radioButton, w.radioButton_2, w.spinBox, w.run_unconnected_checkbox, w.checkBox_2)
        self.restoring = True
        blockers = [QSignalBlocker(widget) for widget in widgets]
        try:
            w.radioButton.setChecked(repeat == -1)
            w.radioButton_2.setChecked(repeat != -1)
            w.spinBox.setValue(max(1, count))
            w.run_unconnected_checkbox.setChecked(str(values['运行未连接模块']).lower() == 'true')
            w.checkBox_2.setChecked(str(values['执行中隐藏主窗口']).lower() == 'true')
        finally:
            del blockers
            self.restoring = False
        self.changed()

    def saved_as(self, path):
        self.changed()
        self.path = project_key(path)
        self.changed()
