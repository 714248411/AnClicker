"""Shared contracts for the reference application's parameter schemas."""
from __future__ import annotations
import json
import re
from instructions.common import SchemaInstructionEditor, InstructionExecutorBase
from instructions.common import actions
from instructions.common.rpa_bridge import ROOT, get_bridge
CATALOG = {item['id']: item for item in json.loads((ROOT / 'integrations/yingdao/commands.json').read_text(encoding='utf-8'))}
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
        from qt_compat.QtCore import QEvent
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
        from qt_compat.QtWidgets import QMessageBox
        try:
            self._run_rpa_auxiliary(key)
        except Exception as error:
            QMessageBox.warning(self, '操作未完成', str(error))

    def _run_rpa_auxiliary(self, key):
        from qt_compat.QtWidgets import QFileDialog, QDialog
        control = self._controls[key]
        if key in ('selector', 'anchor'):
            from instructions.registry import get_instruction_spec
            from instructions.models import CommandRecord, ExecutionContext
            from instructions.common.test_runner import run_cancellable_test
            context = ExecutionContext(variables=dict(getattr(self.context, 'variables', {})))
            context.variables.pop('网页元素', None)
            spec = get_instruction_spec('拾取元素')
            run_cancellable_test(spec, CommandRecord(None, spec.type_id, {}), context, self)
            chosen = context.variables.get('网页元素')
            if chosen and not context.stop_requested:
                control.setText(str(chosen))
                if key == 'selector' and 'by' in self._controls:
                    self._set_control_value(self._controls['by'], 'CSS选择器')
        elif key in ('varName', 'data'):
            from WindowControl.变量池窗口 import VariablePool_Win
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
    

class RpaInstructionExecutor(InstructionExecutorBase):
    COMMAND_ID = ''
    def execute_once(self, context, command):
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        definition = CATALOG[self.COMMAND_ID]
        parameters = {p['key']:p.get('default','') for p in definition['params']}
        parameters.update(command.parameters)
        parameters = {k: actions.substitute_variables(context, v) if isinstance(v, str) and k not in {"varName", "data"} else v
                      for k, v in parameters.items()}
        response = get_bridge().execute({'id':self.COMMAND_ID, 'name':definition['name'], 'params':parameters},
                                        context.variables, context=context)
        context.variables.update(response.get('variables', {}))
        result = response.get('result')
        if self.COMMAND_ID == 'pickElement' and result and not result.get('canceled'):
            context.set_variable('网页元素详情', result)
            context.set_variable('网页元素', result.get('css', '') if isinstance(result, dict) else str(result))
        context.emit(definition['name'] + '：完成')
        return result
