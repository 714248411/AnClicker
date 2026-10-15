"""Multi-point picking and random-offset controls; preserved handwritten UI."""
from anclicker.ui.instruction_editors.rpa_instruction import RpaInstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QtWidgets_QWidget_etc': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QWidget', 'QHBoxLayout', 'QVBoxLayout', 'QFormLayout', 'QComboBox', 'QSpinBox', 'QPushButton', 'QLabel'), 0),
    'DownwardExpansion': ('from', 'anclicker.ui.instruction_editors.downward_expansion', ('DownwardExpansion',), 0),
    'get_instruction_spec': ('from', 'anclicker.instructions.registry', ('get_instruction_spec',), 0),
    'CommandRecord_ExecutionContext': ('from', 'anclicker.domain.instructions', ('CommandRecord', 'ExecutionContext'), 0),
    'run_cancellable_test': ('from', 'anclicker.ui.instruction_editors.test_runner', ('run_cancellable_test',), 0),
})


class CoordinateClickEditor(RpaInstructionEditor):
    def _collect_parameter_controls(self):
        QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, QPushButton, QLabel = _module_imports.load('QtWidgets_QWidget_etc')
        self.ui.label_0.setText('点击坐标')
        self.ui.parameter_0.setToolTip('按顺序执行，可手动修改；多个坐标用分号分隔')
        point_row = QWidget(self)
        point_layout = QHBoxLayout(point_row)
        point_layout.setContentsMargins(0, 0, 0, 0)
        point_layout.setSpacing(6)
        self.ui.parameterFormLayout.removeWidget(self.ui.parameter_0)
        point_layout.addWidget(self.ui.parameter_0, 1)
        self.ui.auxiliary_0 = QPushButton('取点', point_row)
        self.ui.auxiliary_0.setToolTip('在网页上新增取点，或拖动调整已有坐标')
        point_layout.addWidget(self.ui.auxiliary_0)
        self.ui.parameterFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, point_row)
        advanced_section = QWidget(self)
        advanced_layout = QVBoxLayout(advanced_section)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_toggle = QPushButton('▸ 高级设置', advanced_section)
        advanced_toggle.setCheckable(True)
        advanced_toggle.setChecked(False)
        advanced = QWidget(advanced_section)
        advanced.setVisible(False)
        advanced_layout.addWidget(advanced_toggle)
        advanced_layout.addWidget(advanced)
        DownwardExpansion = _module_imports.load('DownwardExpansion')
        self._coordinate_expansion = DownwardExpansion(self, advanced)
        advanced_toggle.toggled.connect(self._coordinate_expansion.setExpanded)
        advanced_toggle.toggled.connect(
            lambda expanded: advanced_toggle.setText('▾ 高级设置' if expanded else '▸ 高级设置'))
        form = QFormLayout(advanced)
        self.ui.parameter_5 = QComboBox(advanced)
        self.ui.parameter_5.addItems(['关闭', '启用'])
        form.addRow('随机偏移（默认关闭）', self.ui.parameter_5)
        for index, label in ((6, '水平偏移范围 ± 像素'), (7, '垂直偏移范围 ± 像素')):
            control = QSpinBox(advanced)
            control.setRange(0, 1000)
            control.setValue(0)
            control.setPrefix('± ')
            control.setSuffix(' 像素')
            control.setToolTip('填写随机偏移最大值；例如 5 表示每次在 -5 到 +5 像素之间随机取值，0 表示此方向不偏移')
            setattr(self.ui, f'parameter_{index}', control)
            form.addRow(label, control)
        self.ui.rootLayout.insertWidget(2, advanced_section)
        self.ui.parameter_5.currentTextChanged.connect(
            lambda value: [getattr(self.ui, f'parameter_{i}').setEnabled(value == '启用') for i in (6, 7)])
        self.ui.parameter_6.setEnabled(False)
        self.ui.parameter_7.setEnabled(False)
        offset_hint = QLabel(advanced)
        offset_hint.setWordWrap(True)
        form.addRow(offset_hint)

        def update_offset_hint(*_):
            x = self.ui.parameter_6.value()
            y = self.ui.parameter_7.value()
            if self.ui.parameter_5.currentText() != '启用':
                offset_hint.setText('随机偏移已关闭：按取点坐标点击。启用后，每个点每次执行都会重新取随机值。')
            else:
                offset_hint.setText(f'每次点击：X 坐标随机加上 -{x}～+{x} 像素，Y 坐标随机加上 -{y}～+{y} 像素。原取点坐标保持不变；范围为 0 时不偏移。')

        self.ui.parameter_5.currentTextChanged.connect(update_offset_hint)
        self.ui.parameter_6.valueChanged.connect(update_offset_hint)
        self.ui.parameter_7.valueChanged.connect(update_offset_hint)
        update_offset_hint()
        return super()._collect_parameter_controls()


    def _run_rpa_auxiliary(self, key):
        if key != 'points':
            return super()._run_rpa_auxiliary(key)
        get_instruction_spec = _module_imports.load('get_instruction_spec')
        CommandRecord, ExecutionContext = _module_imports.load('CommandRecord_ExecutionContext')
        run_cancellable_test = _module_imports.load('run_cancellable_test')
        context = ExecutionContext(variables=dict(getattr(self.context, 'variables', {})))
        context.variables.pop('网页取点结果', None)
        resolve_previous = getattr(self.context, 'metadata', {}).get('previous_web_command')
        if callable(resolve_previous):
            previous = dict(resolve_previous())
            if str(previous.get('url') or '').strip() in ('', 'https://', 'http://'):
                raise ValueError('请先填写流程上方最近的“打开网页”地址')
            previous.update({'target': '当前标签页', 'waitType': '加载完成'})
            spec = get_instruction_spec('打开网页')
            run_cancellable_test(spec, CommandRecord(None, spec.type_id, previous), context, self)
            if context.stop_requested:
                return
        spec = get_instruction_spec(self.TYPE_ID)
        params = {'pickOnly': True, 'points': self._controls['points'].text()}
        run_cancellable_test(spec, CommandRecord(None, self.TYPE_ID, params), context, self)
        self.window().raise_()
        self.window().activateWindow()
        result = context.variables.get('网页取点结果')
        if not context.stop_requested and result and not result.get('canceled'):
            points = result.get('points', [])
            self._controls['points'].setText('; '.join(f"{p['x']},{p['y']}" for p in points))
            if points:
                self._controls['x'].setValue(points[0]['x'])
                self._controls['y'].setValue(points[0]['y'])
            self._controls['points'].setFocus()
