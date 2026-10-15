"""Explicit advanced timing preferences, shared by editors and execution."""
import math

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QtWidgets_QDialog_etc': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QVBoxLayout', 'QFormLayout', 'QLabel', 'QDoubleSpinBox', 'QDialogButtonBox', 'QPushButton'), 0),
    'apply_settings_theme': ('from', 'anclicker.ui.settings_theme', ('apply_settings_theme',), 0),
})


IMAGE_DELAY = '图像识别后点击延迟'
COMMAND_INTERVAL = '统一指令间隔'
AFTER_CLICK = '图像点击后等待'
CLICK_INTERVAL = '图像双击与连击间隔'
PRESS_DURATION = '图像点击按下持续时间'
KEYS = (IMAGE_DELAY, AFTER_CLICK, CLICK_INTERVAL, PRESS_DURATION, COMMAND_INTERVAL)


def read_timing(database):
    values = {}
    for key in KEYS:
        try:
            value = float(database.get_setting_value(key) or 0) if database else 0.0
            values[key] = min(3600.0, max(0.0, value)) if math.isfinite(value) else 0.0
        except (TypeError, ValueError):
            values[key] = 0.0
    return values


def context_timing(context):
    if '_execution_timing' not in context.metadata:
        context.metadata['_execution_timing'] = read_timing(context.metadata.get('database'))
    return context.metadata['_execution_timing']




QDialog, QVBoxLayout, QFormLayout, QLabel, QDoubleSpinBox, QDialogButtonBox, QPushButton = _module_imports.load('QtWidgets_QDialog_etc')


class AdvancedTimingDialog(QDialog):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.db = database
        self.setWindowTitle('高级设置 · 动作延时')
        self.resize(480, 330)
        layout = QVBoxLayout(self)
        hint = QLabel('全局生效，下一次运行或测试使用新设置。0 秒表示不额外等待。', self)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.spins = {}
        values = read_timing(database)
        for key in KEYS:
            spin = QDoubleSpinBox(self)
            spin.setObjectName('imageClickDelay' if key == IMAGE_DELAY else 'commandInterval')
            spin.setRange(0, 3600)
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setSuffix(' 秒')
            spin.setValue(values[key])
            self.spins[key] = spin
            form.addRow(key + '：', spin)
        self.spins[IMAGE_DELAY].setToolTip('识别到图像后等待指定时间，再确认目标并点击；无操作判断不等待。')
        self.spins[COMMAND_INTERVAL].setToolTip('两次指令动作之间的等待时间，包含重复执行；首条指令前不等待。')
        self.spins[AFTER_CLICK].setToolTip('图像点击完成后等待；会与统一指令间隔叠加。')
        self.spins[CLICK_INTERVAL].setToolTip('图像双击或连击中，相邻两次点击之间的等待。')
        self.spins[PRESS_DURATION].setToolTip('鼠标按下到松开的时间；0 表示立即松开。')
        layout.addLayout(form)
        reset = QPushButton('恢复默认：立即执行', self)
        reset.clicked.connect(lambda: [spin.setValue(0) for spin in self.spins.values()])
        layout.addWidget(reset)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Ok).setText('保存')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        apply_settings_theme = _module_imports.load('apply_settings_theme')
        apply_settings_theme(self, parent)

    def accept(self):
        self.db.update_settings(**{key: str(spin.value()) for key, spin in self.spins.items()})
        super().accept()
