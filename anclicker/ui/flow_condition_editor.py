"""Ready-to-use predicates with one target field and optional tuning."""
from anclicker.platform.qt_compat.QtWidgets import (QWidget, QFormLayout, QComboBox, QDoubleSpinBox,
    QSpinBox, QLabel, QPushButton, QFileDialog, QSizePolicy, QHBoxLayout, QDialog)
from anclicker.platform.image_paths import store_image_reference
from anclicker.execution.flow_condition_checks import KINDS, condition_kind, validate_parameters
from anclicker.execution.typed_conditions import OPERATIONS, UNARY
from anclicker.ui.condition_value_editor import ConditionValueEditor
from anclicker.platform.qt_compat.QtCore import QDateTime

BASIC_FIELDS = {'表达式': (), '图片存在': ('图像路径',), '图片文件存在': ('图像路径',),
                'OCR文字存在': ('目标文字',), '颜色判断': ('坐标', '颜色'), '坐标存在': ('坐标',)}
EXTRA_FIELDS = {'表达式': (), '图片存在': ('区域',), '图片文件存在': ('满足条件',),
                'OCR文字存在': ('区域', '匹配方式', '满足条件'),
                '颜色判断': ('满足条件',), '坐标存在': ('满足条件',)}
for _kind in OPERATIONS:
    BASIC_FIELDS[_kind] = ('判断值', '比较方式', '比较值') + (('窗口匹配',) if _kind == '窗口存在' else ())
    EXTRA_FIELDS[_kind] = ()

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
        self._operation_kind = None
        self.value_editors = {}
        self._value_kind = None
        self._value_cache = {}
        self._operation_cache = {}
        fields = [('判断值', '判断值 / 变量', ['']), ('比较方式', '比较方式', []),
                  ('比较值', '比较值 / 变量', ['']), ('窗口匹配', '标题匹配', ['包含', '精准']),
                  ('图像路径', '目标图片', ['{{图片}}']), ('坐标', '坐标 / 变量', ['{{坐标}}']),
                  ('颜色', '目标颜色', ['#FFFFFF', '#000000']),
                  ('目标文字', '目标文字', ['{{文字}}']), ('区域', '区域 x,y,w,h', ['']),
                  ('匹配方式', '文字匹配', ['包含', '精准', '模糊']),
                  ('满足条件', '判断方向', ['存在 / 相等', '不存在 / 不相等'])]
        for key, label, options in fields:
            advanced = key in ('区域', '匹配方式', '满足条件')
            host, layout = (self.advanced_panel, self.extra_form) if advanced else (self.details, self.detail_form)
            combo = QComboBox(host)
            combo.setEditable(key not in ('满足条件', '匹配方式', '比较方式', '窗口匹配'))
            combo.addItems(options)
            if combo.isEditable():
                combo.setInsertPolicy(QComboBox.NoInsert)
            self.controls[key] = combo
            self.labels[key] = QLabel(label, host)
            row = combo
            if key in ('判断值', '比较值'):
                row = ConditionValueEditor(combo, host)
                self.value_editors[key] = row
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
        self.controls['比较方式'].currentTextChanged.connect(self._update_operand)
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
            self.controls['图像路径'].setCurrentText(store_image_reference(path))

    def _update_operand(self, *_):
        kind = self.kind.currentText()
        if kind in OPERATIONS:
            visible = self.controls['比较方式'].currentText() not in UNARY
            self.rows['比较值'].setVisible(visible)
            self.labels['比较值'].setVisible(visible)
            operation = self.controls['比较方式'].currentText()
            if kind == '列表' and operation.startswith('长度') and not self.controls['比较值'].currentText():
                self.controls['比较值'].setCurrentText('0')
            for key, editor in self.value_editors.items():
                editor.configure(kind, operation, key == '比较值')
            self.labels['比较值'].setText('列表长度' if kind == '列表' and operation.startswith('长度')
                else '目标元素' if kind == '列表' else '比较日期' if kind == '日期' else '比较值')

    def _update(self, *_):
        kind = self.kind.currentText()
        if self._value_kind != kind:
            if self._value_kind in OPERATIONS:
                self._value_cache[self._value_kind] = tuple(self.controls[k].currentText() for k in ('判断值', '比较值'))
                self._operation_cache[self._value_kind] = self.controls['比较方式'].currentText()
            self._value_kind = kind
            if kind in OPERATIONS:
                today = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
                defaults = {'数字': ('0', '0'), '日期': (today, today), '列表': ('[]', ''),
                            '文本': ('', ''), '文件目录': ('', ''), '窗口存在': ('', '')}
                for key, value in zip(('判断值', '比较值'), self._value_cache.get(kind, defaults[kind])):
                    self.controls[key].setCurrentText(value)
        if kind in OPERATIONS and self._operation_kind != kind:
            self._operation_kind = kind
            self.controls['比较方式'].clear()
            self.controls['比较方式'].addItems(OPERATIONS[kind])
            self.controls['比较方式'].setCurrentText(self._operation_cache.get(kind, OPERATIONS[kind][0]))
        visible = BASIC_FIELDS[kind] + EXTRA_FIELDS[kind]
        for key in self.controls:
            self.rows[key].setVisible(key in visible)
            self.labels[key].setVisible(key in visible)
        for widget in (self.precision, self.precision_label):
            widget.setVisible(kind in ('图片存在', 'OCR文字存在'))
        for widget in (self.tolerance, self.tolerance_label):
            widget.setVisible(kind == '颜色判断')
        self.details.setVisible(kind != '表达式')
        self.advanced_button.setVisible(kind not in OPERATIONS)
        self.advanced_panel.setVisible(kind not in OPERATIONS and self.advanced_button.isChecked())
        self.labels['判断值'].setText({'文本': '文本 / 变量', '数字': '数字 / 变量', '日期': '日期 / 变量',
            '列表': '列表 / 变量', '文件目录': '路径 / 变量', '窗口存在': '窗口标题 / 变量'}.get(kind, '判断值 / 变量'))
        self._update_operand()
        self.help_label.setText({
            '文本': '比较文本，支持包含、相等、开头、结尾和空值判断；保留文本首尾空格。',
            '数字': '使用数字框调节数值，选择比较方式即可；切换“变量 / 手动输入”可选择变量。',
            '日期': '点击日历选择日期，调整时分秒，或点击“今天”；也可切换为日期变量。',
            '列表': '点击“逐项编辑列表”添加或删除内容，也可选择列表变量；比较长度时使用数字框。',
            '文件目录': '检查路径存在、不存在、是文件或是目录；相对路径以当前项目目录为基准。支持 {{变量名}}。',
            '窗口存在': '检查窗口标题，支持包含或精准匹配；只检查存在性，不激活窗口。支持 {{变量名}}。',
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
            for key in ('图像路径', '目标文字', '坐标', '颜色', '区域', '判断值', '比较值'):
                combo = self.controls[key]
                if combo.findText(text) < 0:
                    current = combo.currentText()
                    combo.addItem(text)
                    combo.setCurrentText(current)

    def load(self, parameters):
        self.kind.setCurrentText(condition_kind(parameters))
        defaults = dict(TARGET_DEFAULTS, 匹配方式='包含', 满足条件='存在 / 相等', 窗口匹配='包含')
        kind = condition_kind(parameters)
        if kind in OPERATIONS:
            defaults['比较方式'] = OPERATIONS[kind][0]
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
        result.update({key: (self.controls[key].currentText() if key in ('判断值', '比较值')
                             else self.controls[key].currentText().strip())
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
