"""Explicit advanced timing preferences, shared by editors and execution."""
import math
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QHBoxLayout, QScrollArea, QWidget, QFrame

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QtWidgets_QDialog_etc': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QVBoxLayout', 'QFormLayout', 'QLabel', 'QDoubleSpinBox', 'QDialogButtonBox', 'QPushButton'), 0),
    'InformationDialog': ('from', 'anclicker.ui.information_dialogs', ('InformationDialog',), 0),
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


InformationDialog = _module_imports.load('InformationDialog')


class AdvancedTimingDialog(InformationDialog):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.db = database
        self.setWindowTitle('高级设置 · 动作延时')
        self.resize(560, 390)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(12)
        body = QWidget(self)
        body.setObjectName('settingsBody')
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(12)
        scroll = QScrollArea(self)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        hint = QLabel('全局生效，下一次运行或测试使用新设置。0 秒表示不额外等待。', self)
        hint.setWordWrap(True)
        hint.setObjectName("settingsHint")
        content.addWidget(hint)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
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
            form.addRow(key + ':', spin)
        self.spins[IMAGE_DELAY].setToolTip('识别到图像后等待指定时间，再确认目标并点击；无操作判断不等待。')
        self.spins[COMMAND_INTERVAL].setToolTip('两次指令动作之间的等待时间，包含重复执行；首条指令前不等待。')
        self.spins[AFTER_CLICK].setToolTip('图像点击完成后等待；会与统一指令间隔叠加。')
        self.spins[CLICK_INTERVAL].setToolTip('图像双击或连击中，相邻两次点击之间的等待。')
        self.spins[PRESS_DURATION].setToolTip('鼠标按下到松开的时间；0 表示立即松开。')
        content.addLayout(form)
        content.addStretch(1)
        reset = QPushButton('恢复默认', self)
        reset.setToolTip('将所有动作延时恢复为 0 秒')
        reset.setAutoDefault(False)
        self.reset_button = reset
        reset.clicked.connect(lambda: [spin.setValue(0) for spin in self.spins.values()])
        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addWidget(reset)
        footer.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Ok).setText('保存')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        footer.addWidget(buttons)
        layout.addLayout(footer)
        apply_settings_theme = _module_imports.load('apply_settings_theme')
        owner = parent
        while owner is not None and not hasattr(owner, 'view_workspace'):
            owner = owner.parentWidget()
        apply_settings_theme(self, owner)
        self.ensurePolished()
        for button in (reset, buttons.button(QDialogButtonBox.Ok), buttons.button(QDialogButtonBox.Cancel)):
            button.setMinimumHeight(button.sizeHint().height())
        self.setMinimumWidth(420)
        area = self.screen().availableGeometry()
        self.resize(min(560, area.width()), min(max(390, self.sizeHint().height()), area.height()))
        if parent is not None:
            position = parent.window().frameGeometry().center() - self.rect().center()
            position.setX(max(area.left(), min(position.x(), area.right() - self.width() + 1)))
            position.setY(max(area.top(), min(position.y(), area.bottom() - self.height() + 1)))
            self.move(position)

    def accept(self):
        self.db.update_settings(**{key: str(spin.value()) for key, spin in self.spins.items()})
        super().accept()
