"""Shared schema/runtime for the individually draggable offline OCR commands."""
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import time

from anclicker.instructions.common import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from anclicker.platform.local_ocr import OcrSession, OcrCancelled, validated_rows, find_matches

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'TEXT_TYPES': ('from', 'anclicker.domain.instruction_fields.local_ocr_instruction', ('TEXT_TYPES',), 0),
    'REGION_TYPES': ('from', 'anclicker.domain.instruction_fields.local_ocr_instruction', ('REGION_TYPES',), 0),
    'CLICK_TYPES': ('from', 'anclicker.domain.instruction_fields.local_ocr_instruction', ('CLICK_TYPES',), 0),
    'fields_for': ('from', 'anclicker.domain.instruction_fields.local_ocr_instruction', ('fields_for',), 0),
    'validate': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('validate',), 0),
    'InstructionDraft': ('from', 'anclicker.domain.instructions', ('InstructionDraft',), 0),
    'QLabel_QPushButton_QFormLayout_QWidget': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QLabel', 'QPushButton', 'QFormLayout', 'QWidget'), 0),
    'DownwardExpansion': ('from', 'anclicker.ui.instruction_editors.downward_expansion', ('DownwardExpansion',), 0),
    'QWidget_QHBoxLayout': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QWidget', 'QHBoxLayout'), 0),
    'QTimer': ('from', 'anclicker.platform.qt_compat.QtCore', ('QTimer',), 0),
    'QDialog_QMessageBox': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QMessageBox'), 0),
    'SmartCaptureDialog': ('from', 'anclicker.ui.smart_capture', ('SmartCaptureDialog',), 0),
    '_write_result': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('_write_result',), 0),
    'order_matches': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('order_matches',), 0),
    'paste_text': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('paste_text',), 0),
    'LocalOcrExecutor': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('LocalOcrExecutor',), 0),
})


OCR_TYPES = ('OCR文字提取', 'OCR精准找字点击', 'OCR模糊找字返回坐标',
             'OCR范围找字', 'OCR等待文字出现', 'OCR等待文字消失',
             '截图OCR', 'OCR复制', 'OCR粘贴', 'OCR识别区域返回坐标', 'OCR点击识别区域')
TEXT_TYPES = _module_imports.load('TEXT_TYPES')
REGION_TYPES = _module_imports.load('REGION_TYPES')
CLICK_TYPES = _module_imports.load('CLICK_TYPES')


fields_for = _module_imports.load('fields_for')


validate = _module_imports.load('validate')


class LocalOcrEditor(SchemaInstructionEditor):
    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=draft, context=context)
        if '引擎' in self._controls:
            self._controls['引擎'].currentTextChanged.connect(self._engine_changed)
            self._engine_changed(self._controls['引擎'].currentText())
        self._simplify_settings()
        self._align_match_options()
        if '点击来源' in self._controls:
            self._controls['点击来源'].currentTextChanged.connect(self._click_source_changed)
            self._click_source_changed()

    def load_draft(self, draft):
        super().load_draft(draft)
        if '点击来源' in self._controls:
            InstructionDraft = _module_imports.load('InstructionDraft')
            parsed = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
            self._controls['点击来源'].setCurrentText(parsed.parameters.get('点击来源', '重新识别'))
            if '点击来源' not in parsed.parameters and '变量' not in parsed.parameters:
                self._set_control_value(self._controls['变量'], 'OCR坐标')

    def _click_source_changed(self, *_):
        variable_mode = self._controls['点击来源'].currentText() == '前序OCR变量'
        keep = {'点击来源', '变量', '第几个', '动作', '点击位置'}
        for index, field in enumerate(self.FIELDS):
            if field.key in {'忽略大小写', '忽略空白'}:
                continue
            container = getattr(self.ui, f'parameterContainer_{index}')
            form = container.parentWidget().layout()
            form.setRowVisible(container, not variable_mode or field.key in keep)
        if hasattr(self, 'ocr_match_options'):
            self.ocr_advanced_panel.layout().setRowVisible(self.ocr_match_options, not variable_mode)
        for index, field in enumerate(self.FIELDS):
            if field.key == '变量':
                getattr(self.ui, f'parameterLabel_{index}').setText('读取坐标变量 *' if variable_mode else '保存到变量 *')

    def _simplify_settings(self):
        QLabel, QPushButton, QFormLayout, QWidget = _module_imports.load('QLabel_QPushButton_QFormLayout_QWidget')
        basic = {'引擎', '区域', '目标文字', '匹配方式', '第几个', '识别后',
                 '找到后', '等待超时', '内容来源', '粘贴前等待', '点击来源'}
        if self.TYPE_ID == 'OCR点击识别区域':
            basic.update({'变量', '动作'})
        if self.TYPE_ID in ('OCR文字提取', 'OCR模糊找字返回坐标', 'OCR识别区域返回坐标', 'OCR范围找字'):
            basic.add('变量')
        if self.TYPE_ID == 'OCR文字提取':
            basic.add('图像路径')
        self.ui.parameterGroupBox.setTitle('常用设置')
        tips = ('先运行识别/复制指令，再将最近识别的文字粘贴到当前输入框。'
                if self.TYPE_ID == 'OCR粘贴' else
                '流程：OCR识别 → OCR点击。默认读取最近OCR结果，也可选择指定结果变量；不会重复截图识别。'
                if self.TYPE_ID == 'OCR点击识别区域' else
                '① 框选识别范围  ② 设置文字或操作  ③ 测试指令。离线引擎无需配置目录。')
        hint = QLabel(tips, self)
        hint.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, hint)
        self.ocr_advanced_button = QPushButton('高级设置 ▸', self)
        self.ocr_advanced_button.setCheckable(True)
        self.ocr_advanced_button.setAutoDefault(False)
        self.ocr_advanced_panel = QWidget(self)
        advanced = QFormLayout(self.ocr_advanced_panel)
        advanced.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        advanced.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        labels = {'区域': '识别范围', '目标文字': '要查找的文字', '第几个': '选择第几个结果',
                  '变量': '保存到变量', '图像路径': '识别图片（可选）', '匹配方式': '匹配方式'}
        form = self.ui.parameterFormLayout
        self._ocr_advanced_keys = set()
        for index, field in enumerate(self.FIELDS):
            label = getattr(self.ui, f'parameterLabel_{index}')
            label.setToolTip(field.label)
            if field.key in labels:
                label.setText(labels[field.key] + (' *' if field.required else ''))
            control = self._controls[field.key]
            if field.key == '区域':
                control.setPlaceholderText('点击右侧框选；非必填时留空识别全屏')
                getattr(self.ui, f'auxiliary_{index}').setText('框选范围')
            elif field.key == '目标文字':
                control.setPlaceholderText('例如：确定' if field.required else '留空选择范围内的文字框')
            if field.key not in basic:
                container = getattr(self.ui, f'parameterContainer_{index}')
                # Remove the layout items before removing the empty row: Qt 5
                # has no takeRow, and removeRow alone deletes the controls.
                row_index = form.getWidgetPosition(container)[0]
                form.removeWidget(label)
                form.removeWidget(container)
                form.removeRow(row_index)
                advanced.addRow(label, container)
                self._ocr_advanced_keys.add(field.key)
        position = self.ui.rootLayout.indexOf(self.ui.parameterGroupBox) + 1
        self.ui.rootLayout.insertWidget(position, self.ocr_advanced_button)
        self.ui.rootLayout.insertWidget(position + 1, self.ocr_advanced_panel)
        self.ocr_advanced_panel.hide()
        self.ocr_advanced_button.setVisible(bool(self._ocr_advanced_keys))
        DownwardExpansion = _module_imports.load('DownwardExpansion')
        self._ocr_expansion = DownwardExpansion(self, self.ocr_advanced_panel)
        self.ocr_advanced_button.toggled.connect(self._toggle_advanced)
        changed = any(self._control_value(self._controls[f.key]) != f.default
                      for f in self.FIELDS if f.key in self._ocr_advanced_keys)
        if changed:
            self.ocr_advanced_button.setText('高级设置 ▸（已有自定义配置）')

    def _align_match_options(self):
        if '忽略大小写' not in self._controls:
            return
        QWidget, QHBoxLayout = _module_imports.load('QWidget_QHBoxLayout')
        form = self.ocr_advanced_panel.layout()
        self.ocr_match_options = QWidget(self.ocr_advanced_panel)
        row = QHBoxLayout(self.ocr_match_options)
        row.setContentsMargins(0, 0, 0, 0)
        insert_at = None
        for key, title in (('忽略大小写', '忽略英文大小写'), ('忽略空白', '忽略空白字符')):
            index = next(i for i, f in enumerate(self.FIELDS) if f.key == key)
            container = getattr(self.ui, f'parameterContainer_{index}')
            label = getattr(self.ui, f'parameterLabel_{index}')
            position = form.getWidgetPosition(container)[0]
            if insert_at is None:
                insert_at = position
            form.removeWidget(container)
            form.removeWidget(label)
            form.removeRow(position)
            label.hide()
            control = self._controls[key]
            control.setText(title)
            row.addWidget(container)
            if key == '忽略大小写':
                row.addStretch(1)
        form.insertRow(insert_at, self.ocr_match_options)

    def _toggle_advanced(self, expanded):
        self._ocr_expansion.setExpanded(expanded)
        self.ocr_advanced_button.setText('高级设置 ▾（收起）' if expanded else '高级设置 ▸')

    def _engine_changed(self, engine):
        self._controls['引擎'].setToolTip('自动使用程序目录内的离线组件与模型，无需选择目录。')

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        validate(self.TYPE_ID, parameters)

    def _run_auxiliary(self, key):
        if key == '区域':
            QTimer = _module_imports.load('QTimer')
            QDialog, QMessageBox = _module_imports.load('QDialog_QMessageBox')
            SmartCaptureDialog = _module_imports.load('SmartCaptureDialog')
            owner = self.parentWidget().window() if self.parentWidget() else None
            visible = owner is not None and owner.isVisible()
            # hide() ends QDialog.exec(): the workspace treats the editor as
            # cancelled before the asynchronous region picker can return.
            opacity = self.windowOpacity()
            owner_opacity = owner.windowOpacity() if visible else None
            self.setWindowOpacity(0.0)
            if visible:
                owner.setWindowOpacity(0.0)
            def choose():
                dialog = None
                try:
                    dialog = SmartCaptureDialog()
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        self._set_control_value(self._controls[key], str(dialog.selected_region()))
                except Exception as error:
                    QMessageBox.warning(self, '框选失败', str(error))
                finally:
                    if dialog is not None:
                        dialog.deleteLater()
                    if visible:
                        owner.setWindowOpacity(owner_opacity)
                    self.setWindowOpacity(opacity)
                    self.activateWindow()
            QTimer.singleShot(180, choose)
        else:
            super()._run_auxiliary(key)


_write_result = _module_imports.load('_write_result')


order_matches = _module_imports.load('order_matches')


paste_text = _module_imports.load('paste_text')


LocalOcrExecutor = _module_imports.load('LocalOcrExecutor')
