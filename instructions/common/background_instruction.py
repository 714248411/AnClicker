"""Typed parameter forms and window selection for isolated background commands."""
import json
from qt_compat.QtCore import Qt, QObject, QEvent
from qt_compat.QtGui import QPalette
from qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFormLayout, QPushButton, QListWidget, QListWidgetItem, QDialogButtonBox, QMessageBox,
    QWidget, QPlainTextEdit, QGroupBox, QFileDialog, QComboBox, QCompleter, QCheckBox)
from instructions.common import SchemaInstructionEditor, InstructionExecutorBase, actions
from background_catalog import METHODS, group_methods, method_name, values_for, label


class _CompletionTheme(QObject):
    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo
        combo.completer().popup().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show:
            source = self.combo.view()
            watched.setPalette(source.palette())
            watched.setFont(self.combo.font())
            palette = source.palette()
            base = palette.color(QPalette.Base)
            bg, text = base.name(), palette.color(QPalette.Text).name()
            accent, selected = palette.color(QPalette.Highlight).name(), palette.color(QPalette.HighlightedText).name()
            line = (base.lighter(145) if base.lightness()<128 else base.darker(112)).name()
            handle = (base.lighter(230) if base.lightness()<128 else base.darker(125)).name()
            watched.setStyleSheet(f'''
                QAbstractItemView {{background:{bg};color:{text};border:1px solid {line};padding:4px;}}
                QAbstractItemView::item {{min-height:24px;padding:2px 6px;border:none;}}
                QAbstractItemView::item:selected {{background:{accent};color:{selected};}}
                QScrollBar:vertical {{background:{bg};width:8px;margin:0;border:none;}}
                QScrollBar::handle:vertical {{background:{handle};min-height:20px;border-radius:4px;}}
                QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{height:0;border:none;}}
                QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{background:{bg};}}
            ''')
        return False


class BackgroundEditor(SchemaInstructionEditor):
    """Keep only template controls that are meaningful in a background editor."""

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent=parent, draft=None, context=context)
        self.ui.commonGroupBox.setTitle('执行与备注')
        # Editor tests create a fresh context. Only binding can be verified there;
        # other operations require the binding established by the running flow.
        self.test_button.setVisible(self.TYPE_ID == '绑定选择窗口')
        if self.TYPE_ID in ('绑定选择窗口', '解除后台绑定'):
            self.repeat_count.valueChanged.connect(self._update_repeat_visibility)
            self._update_repeat_visibility()
        if draft is not None:
            self.load_draft(draft)

    def _update_repeat_visibility(self, value=None):
        # Do not silently change a saved project that already repeats binding.
        legacy_repeat = self.repeat_count.value() > 1
        self.ui.repeatLabel.setText('重复次数（旧配置）')
        self.repeat_count.setToolTip('保留此项目原有的重复设置；改为 1 后按单次执行。')
        self.ui.repeatLabel.setVisible(legacy_repeat)
        self.repeat_count.setVisible(legacy_repeat)


class UnbindingEditor(BackgroundEditor):
    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent=parent, draft=draft, context=context)
        self.ui.parameterGroupBox.hide()
        self.helpLabel = QLabel('解除当前流程的后台窗口绑定，后续普通键鼠指令恢复前台操作。无需填写窗口参数。', self)
        self.helpLabel.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, self.helpLabel)


class BackgroundMethodEditor(BackgroundEditor):
    def __init__(self, parent=None, draft=None, context=None):
        self._loading = False
        super().__init__(parent=parent, draft=None, context=context)
        self._controls['参数'].hide()
        self.ui.label_1.hide()
        self.argumentBody = QWidget(self)
        self.argumentForm = QFormLayout(self.argumentBody)
        self.argumentForm.setContentsMargins(0, 0, 0, 0)
        self.argumentForm.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.ui.parameterFormLayout.insertRow(1, self.argumentBody)
        self.helpLabel = QLabel(self)
        self.helpLabel.setWordWrap(True)
        self.ui.rootLayout.insertWidget(2,self.helpLabel)
        operation = self._controls['接口']
        operation.setEditable(True);operation.setInsertPolicy(QComboBox.NoInsert)
        operation.lineEdit().setClearButtonEnabled(True)
        operation.lineEdit().setPlaceholderText('输入中文操作名称或接口名查找')
        completer = QCompleter(operation.model(), operation)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        operation.setCompleter(completer)
        operation._completion_theme = _CompletionTheme(operation)
        self._arguments = {}
        self._method_values = {}
        self._active_method = None
        self._controls['接口'].currentTextChanged.connect(self._select_method)
        self._select_method(self._controls['接口'].currentText())
        if draft is not None:
            self.load_draft(draft)

    def _select_method(self, text):
        if self._loading:
            return
        name = method_name(text)
        if name not in group_methods(self.TYPE_ID) or name == self._active_method:
            return
        if self._active_method:
            try:
                self._method_values[self._active_method] = json.loads(self._controls['参数'].toPlainText())
            except ValueError:
                pass
        values = self._method_values.get(name,{})
        self._controls['参数'].setPlainText(json.dumps(values,ensure_ascii=False))
        self._active_method = name
        self._populate(values)

    def _populate(self, values):
        while self.argumentForm.rowCount():
            self.argumentForm.removeRow(0)
        self._arguments = {}
        name = method_name(self._controls['接口'].currentText())
        data = METHODS.get(name)
        if data is None or data['group'] != self.TYPE_ID:
            return
        self._update_method_help(name, data)
        inputs = [item for item in data['args'] if not item['out'] or item.get('inout')]
        self.argumentBody.setVisible(bool(inputs))
        for item in inputs:
            control = QLineEdit(str(values.get(item['name'], item['default'])), self.argumentBody)
            control.setObjectName('dm_argument_' + item['name'])
            control.setMinimumHeight(32)
            if item['name'] in ('pwd', 'password'):
                control.setEchoMode(QLineEdit.Password)
            control.setToolTip(item['label'] + '；支持 {{变量名}}')
            if item['name'] in ('pic_name', 'bmp_name', 'pic', 'dict_name', 'file', 'path'):
                row = QWidget(self.argumentBody);layout = QHBoxLayout(row)
                layout.setContentsMargins(0,0,0,0);layout.addWidget(control,1)
                button = QPushButton('选择…',row);button.setAutoDefault(False)
                button.setToolTip('选择目录' if item['name']=='path' else '选择文件')
                layout.addWidget(button)
                button.clicked.connect(lambda checked=False, n=name, key=item['name'], c=control: self._browse_argument(n,key,c))
                self.argumentForm.addRow(item['label'],row)
            else:
                self.argumentForm.addRow(item['label'], control)
            self._arguments[item['name']] = control
            control.textChanged.connect(self._save_arguments)

    def _update_method_help(self, name, data):
        lines = ['请在流程中先执行“绑定选择窗口”，再运行此操作。']
        inputs = [item for item in data['args'] if not item['out'] or item.get('inout')]
        names = {item['name'] for item in inputs}
        if names & {'x', 'y', 'x1', 'y1', 'x2', 'y2'} and self.TYPE_ID in ('后台文字识别', '后台图色操作', '后台键鼠操作') and name != 'OcrInFile':
            lines.append('坐标以绑定窗口内容区左上角为 0,0。' if name != 'MoveR' else '填写相对于当前位置的移动距离。')
        if 'color' in names and self.TYPE_ID in ('后台文字识别', '后台图色操作'):
            lines.append('RGB 示例：9f2e3f-020202；HSV 示例：20.30.20-0.0.20。')
        elif 'delta_color' in names:
            lines.append('图片偏色为 RGB 三组十六进制数，例如 000000。')
        if inputs:
            lines.append('参数可引用 {{变量名}}；结果变量留空时不保存返回值。')
        else:
            lines.append('此操作无需额外参数；结果变量留空时不保存返回值。')
        self.helpLabel.setText('\n'.join(lines))

    def _browse_argument(self, method, key, control):
        if key == 'path':
            value = QFileDialog.getExistingDirectory(self, '选择目录', control.text())
        elif method.startswith('Capture') or method == 'SaveDict' or (method == 'ImageToBmp' and key == 'bmp_name'):
            suffix = {'CapturePng':'PNG (*.png)', 'CaptureJpg':'JPEG (*.jpg)',
                      'CaptureGif':'GIF (*.gif)', 'SaveDict':'字库文件 (*.txt)'}.get(method,'位图 (*.bmp)')
            value, _ = QFileDialog.getSaveFileName(self, '保存文件', control.text(), suffix + ';;所有文件 (*)')
        elif key == 'pic_name' and method in ('FindPic','FindPicE','FindPicEx','FindPicSim','FindPicSimEx','LoadPic','FreePic'):
            files, _ = QFileDialog.getOpenFileNames(self, '选择图片（可多选）', '', '图片 (*.bmp *.png *.jpg *.jpeg);;所有文件 (*)')
            value = '|'.join(files)
        else:
            kind = '字库文件 (*.txt)' if key == 'dict_name' else '图片 (*.bmp *.png *.jpg *.jpeg)'
            value, _ = QFileDialog.getOpenFileName(self, '选择文件', control.text(), kind + ';;所有文件 (*)')
        if value:
            control.setText(value)

    def _save_arguments(self):
        self._controls['参数'].setPlainText(json.dumps({k: v.text() for k, v in self._arguments.items()},ensure_ascii=False))

    def load_draft(self, draft):
        self._loading = True
        try:
            super().load_draft(draft)
        finally:
            self._loading = False
        try:
            values = json.loads(self._controls['参数'].toPlainText())
        except ValueError:
            values = {}
        self._active_method = method_name(self._controls['接口'].currentText())
        self._method_values.clear()
        self._populate(values if isinstance(values, dict) else {})

    def _validate_parameters(self, parameters):
        name = method_name(parameters['接口'])
        if name not in group_methods(self.TYPE_ID):
            raise ValueError('请选择有效的后台接口')
        parameters['接口'] = label(name)
        super()._validate_parameters(parameters)
        values_for(name, json.loads(parameters['参数']))


class BindingEditor(BackgroundEditor):
    def __init__(self, parent=None, draft=None, context=None):
        from background_binding import AUTO, CUSTOM
        super().__init__(parent=parent, draft=None, context=context)
        self.ui.parameterGroupBox.setTitle('选择窗口与绑定方案')
        self._controls['窗口句柄'].setPlaceholderText('点选窗口后自动填写，也可手动输入句柄')
        self._controls['窗口标题'].setPlaceholderText('选择后显示窗口名称，也可填写标题定位窗口')
        self.ui.label_1.setText('窗口名称')
        self.ui.auxiliary_0.setText('窗口列表…')
        self.pickWindowButton = QPushButton('鼠标点选窗口', self)
        self.pickWindowButton.setObjectName('pickBackgroundWindowButton')
        self.pickWindowButton.setToolTip('点击后选择目标应用窗口；按住 Ctrl 可选择子窗口，Esc 取消')
        self.pickWindowButton.setAutoDefault(False)
        self.ui.fieldLayout_0.addWidget(self.pickWindowButton)
        self.pickWindowButton.clicked.connect(self._pick_window)
        self.advanced_panel = QGroupBox('窗口信息与高级选项', self)
        advanced = QFormLayout(self.advanced_panel)
        advanced.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        advanced.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form = self.ui.parameterFormLayout
        for index, field in enumerate(self.FIELDS):
            if field.key in ('窗口句柄', '窗口标题', '绑定方案'):
                continue
            label = getattr(self.ui, 'label_' + str(index))
            control = self._controls[field.key]
            row = form.getWidgetPosition(control)[0]
            form.removeWidget(label);form.removeWidget(control)
            form.removeRow(row)
            advanced.addRow(label, control)
        self._controls['进程路径'].setToolTip('点选或从窗口列表选择后自动填写，用于再次定位同一程序')
        self._controls['绑定模式'].setToolTip('0 为通用绑定；遇到兼容问题时可尝试 2')
        self._controls['绑定等待'].setToolTip('绑定成功后等待画面准备完成，单位为秒')
        component = QPushButton('大漠组件设置…', self.advanced_panel)
        component.setAutoDefault(False);component.clicked.connect(self._configure)
        component.setToolTip('默认首次绑定时自动配置；可查看进度、重新检查或改用手动组件')
        advanced.addRow(component)
        self.preset_hint = QLabel(self)
        self.preset_hint.setWordWrap(True)
        self.advanced_button = QPushButton('高级设置 ▸', self)
        self.advanced_button.setCheckable(True);self.advanced_button.setAutoDefault(False)
        position = self.ui.rootLayout.indexOf(self.ui.parameterGroupBox) + 1
        self.ui.rootLayout.insertWidget(position, self.preset_hint)
        self.ui.rootLayout.insertWidget(position + 1, self.advanced_button)
        self.ui.rootLayout.insertWidget(position + 2, self.advanced_panel)
        self.advanced_panel.hide()
        from instructions.common.downward_expansion import DownwardExpansion
        self._binding_expansion = DownwardExpansion(self, self.advanced_panel)
        self.advanced_button.toggled.connect(self._toggle_advanced)
        self._controls['绑定方案'].currentTextChanged.connect(self._preset_changed)
        self.test_button.setText('测试绑定')
        self.test_button.setToolTip('只验证能否绑定，测试结束后解除绑定；结果显示在运行日志中')
        self._preset_changed()
        if draft is not None:
            self.load_draft(draft)

    def load_draft(self, draft):
        from instructions.models import InstructionDraft
        from background_binding import selected_preset, MODE_KEYS, CUSTOM
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        control = self._controls['绑定方案']
        blocked = control.blockSignals(True)
        try:
            legacy = '绑定方案' not in draft.parameters and selected_preset(draft.parameters) == CUSTOM
            legacy_defaults = dict(zip(MODE_KEYS, ('gdi','windows','windows')))
            for field in self.FIELDS:
                default = legacy_defaults.get(field.key,field.default) if legacy else field.default
                self._set_control_value(self._controls[field.key],default)
            super().load_draft(draft)
            control.setCurrentText(selected_preset(draft.parameters))
        finally:
            control.blockSignals(blocked)
        if hasattr(self, 'preset_hint'):
            self._preset_changed()

    def _preset_changed(self, text=None):
        from background_binding import AUTO, CUSTOM, PROFILES, MODE_KEYS
        preset = self._controls['绑定方案'].currentText()
        custom = preset == CUSTOM
        if not custom and (preset == AUTO or preset in PROFILES):
            profile = PROFILES['DX1' if preset == AUTO else preset]
            for key, value in zip(MODE_KEYS, profile):
                self._set_control_value(self._controls[key], 'dx1' if key == '图像模式' and value == 'dx' else value)
        for index, field in enumerate(self.FIELDS):
            if field.key in MODE_KEYS:
                self._controls[field.key].setEnabled(custom)
                self._controls[field.key].setVisible(custom)
                getattr(self.ui, 'label_' + str(index)).setVisible(custom)
        text = ('先尝试 DX1，绑定或取图异常时自动尝试 DX2。普通应用不兼容时可改选 GDI 兼容。'
                if preset == AUTO else '按高级设置中的图像、鼠标和键盘模式绑定。'
                if custom else '已自动配好图像、鼠标和键盘模式，可直接测试绑定。')
        self.preset_hint.setText(text + '\n后续坐标以目标窗口内容区左上角为 0,0；测试结果可在运行日志查看。')
        if custom and self.isVisible():
            self.advanced_button.setChecked(True)

    def _toggle_advanced(self, expanded):
        self.advanced_button.setText('高级设置 ▾（收起）' if expanded else '高级设置 ▸')
        self._binding_expansion.setExpanded(expanded)

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        from background_binding import binding_attempts
        binding_attempts(parameters)

    def _apply_selected_window(self, entry):
        for key, value in entry.items():
            if key in self._controls:
                self._set_control_value(self._controls[key], value)

    def _pick_window(self):
        from background_window_picker import pick_background_window
        try:
            entry = pick_background_window(self)
            if entry is not None:
                self._apply_selected_window(entry)
        except Exception as error:
            QMessageBox.warning(self, '无法点选窗口', str(error))

    def _configure(self):
        from background_component_settings import ComponentSettings
        dialog = ComponentSettings(self)
        dialog.exec()

    def _run_auxiliary(self, key):
        if key != '窗口句柄':
            return super()._run_auxiliary(key)
        dialog = QDialog(self)
        dialog.setWindowTitle('选择后台窗口')
        dialog.resize(720,420)
        layout = QVBoxLayout(dialog)
        search = QLineEdit(dialog);search.setPlaceholderText('搜索标题、类名或进程路径')
        layout.addWidget(search)
        listing = QListWidget(dialog);layout.addWidget(listing)
        actions_row = QHBoxLayout();layout.addLayout(actions_row)
        children = QCheckBox('包括子窗口',dialog);actions_row.addWidget(children)
        actions_row.addStretch(1)
        refresh = QPushButton('刷新窗口',dialog);actions_row.addWidget(refresh)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.button(QDialogButtonBox.Ok).setText('选择');buttons.button(QDialogButtonBox.Cancel).setText('取消')
        layout.addWidget(buttons)
        def update():
            try:
                from background_runtime import Windows
                entries = Windows().enumerate(children=children.isChecked())
                listing.clear()
                for entry in entries:
                    item = QListWidgetItem(f'{entry["窗口标题"] or "（无标题）"} · {entry["窗口类名"]} · {entry["窗口句柄"]}')
                    item.setData(Qt.UserRole,entry);item.setToolTip(entry['进程路径']);listing.addItem(item)
                filter_items(search.text())
            except Exception as error:
                QMessageBox.warning(dialog,'无法枚举窗口',str(error))
        def filter_items(value):
            for index in range(listing.count()):
                item=listing.item(index)
                item.setHidden(value.casefold() not in (item.text()+' '+item.toolTip()).casefold())
        refresh.clicked.connect(update);children.toggled.connect(update);search.textChanged.connect(filter_items)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        listing.itemDoubleClicked.connect(lambda _: dialog.accept())
        from settings_theme import apply_settings_theme
        owner = getattr(self.context,'metadata',{}).get('main_window')
        if owner:apply_settings_theme(dialog,owner)
        update()
        if dialog.exec() == QDialog.Accepted and listing.currentItem() is not None:
            self._apply_selected_window(listing.currentItem().data(Qt.UserRole))
        dialog.deleteLater()


class BackgroundExecutor(InstructionExecutorBase):
    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('后台执行器指令类型不匹配')
        handled,result = actions.delegated(context,self.TYPE_ID,command)
        if handled:
            return result
        from background_runtime import bind_background, close_background, execute_background_method
        if self.TYPE_ID == '绑定选择窗口':
            return bind_background(context, command.parameters)
        if self.TYPE_ID == '解除后台绑定':
            close_background(context)
            context.emit('后台绑定已解除，后续普通键鼠指令恢复前台模式')
            return True
        return execute_background_method(context,self.TYPE_ID,command.parameters)
