"""Shared contracts for the reference application's parameter schemas."""
from __future__ import annotations
import json
import re
from anclicker.instructions.common import SchemaInstructionEditor, InstructionExecutorBase
from anclicker.instructions.common import actions
from anclicker.platform.rpa_bridge import ROOT, get_bridge
from anclicker.instructions.common.rpa_instruction import CATALOG

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QEvent': ('from', 'anclicker.platform.qt_compat.QtCore', ('QEvent',), 0),
    'QMessageBox': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QMessageBox',), 0),
    'QFileDialog_QDialog': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QFileDialog', 'QDialog'), 0),
    'get_instruction_spec': ('from', 'anclicker.instructions.registry', ('get_instruction_spec',), 0),
    'CommandRecord_ExecutionContext': ('from', 'anclicker.domain.instructions', ('CommandRecord', 'ExecutionContext'), 0),
    'run_cancellable_test': ('from', 'anclicker.ui.instruction_editors.test_runner', ('run_cancellable_test',), 0),
    'VariablePool_Win': ('from', 'anclicker.ui.dialogs.变量池窗口', ('VariablePool_Win',), 0),
    'RpaInstructionExecutor': ('from', 'anclicker.instructions.common.rpa_instruction', ('RpaInstructionExecutor',), 0),
})

class RpaInstructionEditor(SchemaInstructionEditor):
    COMMAND_ID = ''
    PATH_KEYS = ('path', 'fromPath', 'toPath', 'folder', 'dst', 'fromBook', 'toBook')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.PATH_KEYS:
            if key in self._controls:
                self._controls[key].setAcceptDrops(True)
                self._controls[key].installEventFilter(self)

    def eventFilter(self, watched, event):
        QEvent = _module_imports.load('QEvent')
        if watched in [self._controls[k] for k in self.PATH_KEYS if k in self._controls]:
            if event.type() in (QEvent.Type.DragEnter, QEvent.Type.Drop) and event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                if urls and urls[0].isLocalFile():
                    if event.type() == QEvent.Type.Drop:
                        watched.setText(urls[0].toLocalFile())
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(watched, event)

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        for key in ('cell', 'toCell', 'toRange'):
            value = str(parameters.get(key, '')).strip()
            if value and not any(mark in value for mark in (chr(36)+'{', '{{', '☾')) and not re.fullmatch(r'[A-Za-z]{1,3}[1-9][0-9]*', value):
                raise ValueError('单元格必须为 A1、B2 等地址')
        for key in ('row', 'col', 'count', 'startIndex', 'times'):
            if key in parameters and int(parameters[key]) < 1:
                raise ValueError('行列位置和次数必须大于等于 1')
    def _run_auxiliary(self, key):
        QMessageBox = _module_imports.load('QMessageBox')
        try:
            self._run_rpa_auxiliary(key)
        except Exception as error:
            QMessageBox.warning(self, '操作未完成', str(error))

    def _run_rpa_auxiliary(self, key):
        QFileDialog, QDialog = _module_imports.load('QFileDialog_QDialog')
        control = self._controls[key]
        if key in ('selector', 'anchor'):
            get_instruction_spec = _module_imports.load('get_instruction_spec')
            CommandRecord, ExecutionContext = _module_imports.load('CommandRecord_ExecutionContext')
            run_cancellable_test = _module_imports.load('run_cancellable_test')
            context = ExecutionContext(variables=dict(getattr(self.context, 'variables', {})))
            context.variables.pop('网页元素', None)
            context.variables.pop('网页元素详情', None)
            resolve_previous = getattr(self.context, 'metadata', {}).get('previous_web_command')
            if callable(resolve_previous):
                previous = resolve_previous()
                url = str(previous.get('url') or '').strip()
                if url in ('', 'https://', 'http://'):
                    raise ValueError('流程上方最近的“打开网页”尚未填写网址，请先补齐。')
                # Prepare only the upstream page; do not execute intervening actions.
                previous.update({'target': '当前标签页', 'waitType': '加载完成'})
                open_spec = get_instruction_spec('打开网页')
                run_cancellable_test(open_spec, CommandRecord(None, open_spec.type_id, previous), context, self)
                if context.stop_requested:
                    return
            spec = get_instruction_spec('拾取元素')
            run_cancellable_test(spec, CommandRecord(None, spec.type_id, {}), context, self)
            self.window().raise_()
            self.window().activateWindow()
            chosen = context.variables.get('网页元素')
            if chosen and not context.stop_requested:
                control.setText(str(chosen))
                if key == 'selector' and 'by' in self._controls:
                    self._set_control_value(self._controls['by'], 'CSS选择器')
                control.setFocus()
                control.selectAll()
        elif key in ('varName', 'data'):
            VariablePool_Win = _module_imports.load('VariablePool_Win')
            manager = VariablePool_Win(self, database=self._variable_database(), selected_name=control.text())
            if manager.exec() == QDialog.DialogCode.Accepted:
                control.setText(manager.selected_name or control.text())
        elif key in ('folder', 'dst'):
            chosen = QFileDialog.getExistingDirectory(self, '选择文件夹', control.text())
            if chosen:
                control.setText(chosen)
        elif key in ('path','fromPath','toPath','fromBook','toBook'):
            save = self.COMMAND_ID in ('excelNew','excelSave','screenshot') or key == 'toPath'
            chooser = QFileDialog.getSaveFileName if save else QFileDialog.getOpenFileName
            chosen, _ = chooser(self, '选择文件', control.text(), '所有文件 (*)')
            if chosen:
                control.setText(chosen)
        else:
            SchemaInstructionEditor._run_auxiliary(self, key)
    

RpaInstructionExecutor = _module_imports.load('RpaInstructionExecutor')
