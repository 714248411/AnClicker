"""Ready-to-use predicates with one target field and optional tuning."""
from qt_compat.QtWidgets import (QWidget, QFormLayout, QComboBox, QDoubleSpinBox,
    QSpinBox, QLabel, QPushButton, QFileDialog, QSizePolicy, QHBoxLayout, QDialog)
from flow_condition_checks import KINDS, condition_kind, validate_parameters

BASIC_FIELDS = {'表达式': (), '图片存在': ('图像路径',), '图片文件存在': ('图像路径',),
                'OCR文字存在': ('目标文字',), '颜色判断': ('坐标', '颜色'), '坐标存在': ('坐标',)}
EXTRA_FIELDS = {'表达式': (), '图片存在': ('区域',), '图片文件存在': ('满足条件',),
                'OCR文字存在': ('区域', '匹配方式', '满足条件'),
                '颜色判断': ('满足条件',), '坐标存在': ('满足条件',)}
TARGET_DEFAULTS = {'图像路径': '{{图片}}', '目标文字': '{{文字}}', '坐标': '{{坐标}}', '颜色': '#FFFFFF'}


class ConditionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.kind = QComboBox(self)
        self.kind.addItems(KINDS)
        self.form.addRow('判断类型', self.kind)
        self.details = QWidget(self)
        self.detail_form = QFormLayout(self.details)
        self.detail_form.setContentsMargins(0, 0, 0, 0)
        self.form.addRow(self.details)
        self.advanced_panel = QWidget(self)
        self.extra_form = QFormLayout(self.advanced_panel)
        self.extra_form.setContentsMargins(0, 0, 0, 0)
        self.controls, self.labels, self.rows = {}, {}, {}
        fields = [('图像路径', '目标图片', ['{{图片}}']), ('坐标', '坐标 / 变量', ['{{坐标}}']),
                  ('颜色', '目标颜色', ['#FFFFFF', '#000000']),
                  ('目标文字', '目标文字', ['{{文字}}']), ('区域', '区域 x,y,w,h', ['']),
                  ('匹配方式', '文字匹配', ['包含', '精准', '模糊']),
                  ('满足条件', '判断方向', ['存在 / 相等', '不存在 / 不相等'])]
        for key, label, options in fields:
            advanced = key in ('区域', '匹配方式', '满足条件')
            host, layout = (self.advanced_panel, self.extra_form) if advanced else (self.details, self.detail_form)
            combo = QComboBox(host)
            combo.setEditable(key not in ('满足条件', '匹配方式'))
            combo.addItems(options)
            if combo.isEditable():
                combo.setInsertPolicy(QComboBox.NoInsert)
            self.controls[key] = combo
            self.labels[key] = QLabel(label, host)
            row = combo
            if key == '图像路径':
                row = QWidget(host)
                line = QHBoxLayout(row)
                line.setContentsMargins(0, 0, 0, 0)
                line.addWidget(combo, 1)
                self.browse = QPushButton('选择…', row)
                self.browse.setAutoDefault(False)
                self.browse.clicked.connect(self._browse)
                line.addWidget(self.browse)
            self.rows[key] = row
            layout.addRow(self.labels[key], row)
        for key in ('图像路径', '目标文字'):
            self.controls[key].setToolTip('直接输入目标，或填写 {{变量名}}；运行时自动读取变量值。')
        self.controls['区域'].setToolTip('留空识别整个屏幕；也可填写 {{区域变量}}。')
        self.controls['坐标'].setToolTip('颜色判断填写 x,y；坐标存在可填写 {{坐标变量}}，检查有效的 x,y 值。')
        self.help_label = QLabel(self.details)
        self.help_label.setWordWrap(True)
        self.help_label.setObjectName('mutedText')
        self.detail_form.addRow(self.help_label)
        self.advanced_button = QPushButton('判断高级设置 ▸', self.details)
        self.advanced_button.setCheckable(True)
        self.advanced_button.setAutoDefault(False)
        self.detail_form.addRow(self.advanced_button)
        self.detail_form.addRow(self.advanced_panel)
        self.precision = QDoubleSpinBox(self.advanced_panel)
        self.precision.setRange(.01, 1)
        self.precision.setSingleStep(.01)
        self.precision.setValue(.8)
        self.precision_label = QLabel('识别精度 / 相似度', self.advanced_panel)
        self.extra_form.addRow(self.precision_label, self.precision)
        self.tolerance = QSpinBox(self.advanced_panel)
        self.tolerance.setRange(0, 255)
        self.tolerance_label = QLabel('颜色容差', self.advanced_panel)
        self.extra_form.addRow(self.tolerance_label, self.tolerance)
        self._gray = False
        self.advanced_panel.hide()
        self.advanced_button.toggled.connect(self._toggle_advanced)
        self.kind.currentTextChanged.connect(self._update)
        self._update()

    def _toggle_advanced(self, expanded):
        self.advanced_button.setText('判断高级设置 ▾（收起）' if expanded else '判断高级设置 ▸')
        self.advanced_panel.setVisible(expanded)
        self.form.invalidate()
        outer = self.window()
        if isinstance(outer, QDialog) and outer.isVisible():
            outer.layout().activate()
            outer.resize(outer.width(), outer.sizeHint().height())

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择判断图片', '', '图片 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)')
        if path:
            self.controls['图像路径'].setCurrentText(path)

    def _update(self, *_):
        kind = self.kind.currentText()
        visible = BASIC_FIELDS[kind] + EXTRA_FIELDS[kind]
        for key in self.controls:
            self.rows[key].setVisible(key in visible)
            self.labels[key].setVisible(key in visible)
        for widget in (self.precision, self.precision_label):
            widget.setVisible(kind in ('图片存在', 'OCR文字存在'))
        for widget in (self.tolerance, self.tolerance_label):
            widget.setVisible(kind == '颜色判断')
        self.details.setVisible(kind != '表达式')
        self.help_label.setText({
            '表达式': '',
            '图片存在': '在屏幕中查找图片：存在走“是”，不存在走“否”。支持图片路径或 {{图片变量}}。',
            '图片文件存在': '检查本地图片文件是否存在。只需修改路径或 {{图片变量}}，不识别屏幕。',
            'OCR文字存在': '识别屏幕文字并检查是否包含目标。只需修改文字或 {{文字变量}}。',
            '颜色判断': '比较指定坐标的颜色，支持 {{坐标变量}} 和 {{颜色变量}}。',
            '坐标存在': '检查变量是否有有效的 x,y 坐标，未找到或空值走“否”分支。',
        }[kind])
        self.form.invalidate()

    def set_suggestions(self, hint):
        # Adding suggestions must not replace a target the user already typed.
        for suggestion in hint.get('condition_suggestions', []):
            for key, value in suggestion['parameters'].items():
                if key in self.controls and self.controls[key].isEditable() and value is not None:
                    combo = self.controls[key]
                    text = str(value)
                    if combo.findText(text) < 0:
                        current = combo.currentText()
                        combo.addItem(text)
                        combo.setCurrentText(current)
        for variable in hint.get('target_variables', hint.get('candidates', [])):
            text = '{{' + variable + '}}'
            for key in ('图像路径', '目标文字', '坐标', '颜色', '区域'):
                combo = self.controls[key]
                if combo.findText(text) < 0:
                    current = combo.currentText()
                    combo.addItem(text)
                    combo.setCurrentText(current)

    def load(self, parameters):
        self.kind.setCurrentText(condition_kind(parameters))
        defaults = dict(TARGET_DEFAULTS, 匹配方式='包含', 满足条件='存在 / 相等')
        for key, control in self.controls.items():
            control.setCurrentText(str(parameters.get(key, defaults.get(key, ''))))
        if condition_kind(parameters) == '图片存在':
            self.controls['满足条件'].setCurrentText('存在 / 相等')
        self.precision.setValue(float(parameters.get('精度', .8)))
        self.tolerance.setValue(int(parameters.get('容差', 0)))
        self._gray = bool(parameters.get('灰度', False))
        custom = bool(parameters.get('区域')) or self.precision.value() != .8 or self.tolerance.value() != 0
        custom = custom or self.controls['匹配方式'].currentText() != '包含' or self.controls['满足条件'].currentText() != '存在 / 相等'
        self.advanced_button.setChecked(custom)
        self._update()

    def parameters(self):
        kind = self.kind.currentText()
        if kind == '表达式':
            return {}
        result = {'判断类型': kind}
        result.update({key: self.controls[key].currentText().strip()
                       for key in BASIC_FIELDS[kind] + EXTRA_FIELDS[kind]})
        if kind in ('图片存在', 'OCR文字存在'):
            result['精度'] = self.precision.value()
        if kind == '图片存在':
            result['满足条件'] = '存在 / 相等'
            result['灰度'] = self._gray
        if kind == '颜色判断':
            result['容差'] = self.tolerance.value()
        validate_parameters(result)
        return result
