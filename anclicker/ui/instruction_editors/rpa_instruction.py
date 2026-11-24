"""Shared contracts for the reference application's parameter schemas."""
from __future__ import annotations
import json
import re
from anclicker.domain.web_locators import parse_anchor_config, encode_anchor_config
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.web_anchor_editor import WebAnchorDialog
from anclicker.ui.web_window_selector import WebWindowSelector
from anclicker.ui.settings_combo import compact_web_combo_buttons
from anclicker.platform.qt_compat.QtWidgets import QLabel, QPushButton, QDialog
from anclicker.ui.instruction_editors.test_runner import run_cancellable_test
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

class _WebLocatorPreview:
    display_name = '网页定位预览（不执行点击或输入）'

    def create_executor(self):
        return self

    def execute(self, context, command):
        parameters = {key: actions.substitute_variables(context,value) if isinstance(value,str) else value
                      for key,value in command.parameters.items()}
        response = get_bridge().execute({'id':'acPreviewLocator','params':parameters},
                                        context.variables,context=context,timeout=30)
        context.set_variable('网页定位预览',response.get('result'))


class _WebWindowList(_WebLocatorPreview):
    display_name = '获取网页窗口'

    def execute(self, context, command):
        response=get_bridge().execute({'id':'acListBrowserWindows','params':{}},context=context,timeout=30)
        context.set_variable('网页窗口列表',response.get('result'))


class RpaInstructionEditor(SchemaInstructionEditor):
    COMMAND_ID = ''
    PATH_KEYS = ('path', 'fromPath', 'toPath', 'folder', 'dst', 'fromBook', 'toBook')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._web_page_prepared = False
        self._prepare_web_locator_controls()
        if CATALOG.get(self.COMMAND_ID,{}).get('category')=='网页自动化':compact_web_combo_buttons(self)

    def _prepare_web_locator_controls(self):
        if 'selector' not in self._controls and self.COMMAND_ID!='pickElement':
            return
        self.web_window=WebWindowSelector(self._list_web_windows,getattr(self,'_saved_web_window',None),self)
        self.ui.parameterFormLayout.insertRow(0,'网页窗口',self.web_window)
        if 'selector' not in self._controls:return
        self.locator_status = QLabel('',self)
        self.locator_status.setWordWrap(True)
        self.ui.parameterFormLayout.addRow(self.locator_status)
        self.locator_preview = QPushButton('预览定位',self)
        self.locator_preview.setToolTip('仅查找并高亮目标，不执行点击或输入')
        self.locator_preview.clicked.connect(self._preview_current_locator)
        self.ui.footerLayout.insertWidget(1,self.locator_preview)
        if 'anchor' not in self._controls:
            return
        self._controls['anchor'].setMaxLength(120000)
        self._controls['anchor'].setPlaceholderText('可通过锚点向导设置，或填写 text=姓名、CSS、XPath')
        for index,field in enumerate(self.FIELDS):
            if field.key=='anchor':
                label=getattr(self.ui,'label_'+str(index),None)
                if label is not None:label.setText('辅助锚点')
                button=getattr(self.ui,'auxiliary_'+str(index),None)
                if button is not None:button.setText('拾取锚点')
                self.anchor_wizard=QPushButton('锚点向导',self)
                self.anchor_wizard.clicked.connect(self._open_anchor_wizard)
                getattr(self.ui,'fieldLayout_'+str(index)).addWidget(self.anchor_wizard)

    def _locator_parameters(self):
        return {key:self._control_value(self._controls[key]) for key in ('selector','by','anchor','anchorRel') if key in self._controls} | {'browserWindow':self.web_window.selection()}

    def _preview_web_locator(self, parameters):
        context=ExecutionContext(variables=dict(getattr(self.context,'variables',{})))
        run_cancellable_test(_WebLocatorPreview(),CommandRecord(None,'网页定位预览',parameters),context,self)
        if context.stop_requested:return None
        result=context.variables.get('网页定位预览')
        if not isinstance(result,dict):raise RuntimeError('定位预览未返回结果，请先打开网页')
        self.locator_status.setText(result.get('reason','')+'；目标候选 '+str(result.get('count',0))+' 个')
        return result

    def _preview_current_locator(self):
        QMessageBox = _module_imports.load('QMessageBox')
        try:self._preview_web_locator(self._locator_parameters())
        except Exception as error:QMessageBox.warning(self,'无法预览定位',str(error))

    def _open_anchor_wizard(self):
        QMessageBox = _module_imports.load('QMessageBox')
        try:
            dialog=WebAnchorDialog(self._locator_parameters(),self._pick_web_element,self._preview_web_locator,self,list_windows=self._list_web_windows)
            try:
                if dialog.exec()==QDialog.DialogCode.Accepted:
                    self.web_window.set_selection(dialog.window_selector.selection())
                    for key,value in dialog.parameters().items():
                        if key in self._controls:self._set_control_value(self._controls[key],value)
                    self.locator_status.setText('已设置多锚点定位；可点击预览确认实际匹配目标。')
            finally:dialog.deleteLater()
        except Exception as error:QMessageBox.warning(self,'锚点设置未完成',str(error))

    def _pick_web_element(self, *window_choice):
        get_instruction_spec = _module_imports.load('get_instruction_spec')
        context = ExecutionContext(variables=dict(getattr(self.context,'variables',{})))
        browser_window=window_choice[0] if window_choice else self.web_window.selection()
        resolve_previous = getattr(self.context,'metadata',{}).get('previous_web_command')
        if not browser_window and callable(resolve_previous) and not self._web_page_prepared:
            previous = dict(resolve_previous())
            url = str(previous.get('url') or '').strip()
            if url in ('','https://','http://'):
                raise ValueError('流程上方最近的“打开网页”尚未填写网址，请先补齐。')
            previous.update({'target':'当前标签页','waitType':'加载完成'})
            spec = get_instruction_spec('打开网页')
            run_cancellable_test(spec,CommandRecord(None,spec.type_id,previous),context,self)
            if context.stop_requested:return None
            self._web_page_prepared = True
        spec=get_instruction_spec('拾取元素')
        run_cancellable_test(spec,CommandRecord(None,spec.type_id,{'browserWindow':browser_window}),context,self)
        self.window().raise_();self.window().activateWindow()
        detail=context.variables.get('网页元素详情')
        return detail if isinstance(detail,dict) and not detail.get('canceled') and not context.stop_requested else None

    def _list_web_windows(self):
        context=ExecutionContext()
        run_cancellable_test(_WebWindowList(),CommandRecord(None,'网页窗口列表',{}),context,self)
        if context.stop_requested:return None
        pages=context.variables.get('网页窗口列表')
        if not isinstance(pages,list):raise RuntimeError('未收到网页窗口列表')
        return pages

    def load_draft(self,draft):
        super().load_draft(draft)
        parameters=draft.parameters if hasattr(draft,'parameters') else draft.get('parameters',{})
        self._saved_web_window=parameters.get('browserWindow')
        if hasattr(self,'web_window'):self.web_window.set_selection(self._saved_web_window)

    def get_draft(self):
        draft=super().get_draft()
        if hasattr(self,'web_window'):draft.parameters['browserWindow']=self.web_window.selection()
        return draft

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
            chosen=self._pick_web_element()
            if chosen:
                selector=str(chosen.get('css') or chosen.get('xpath') or '')
                if key=='anchor':
                    relation=self._control_value(self._controls['anchorRel']) if 'anchorRel' in self._controls else '下方'
                    config=parse_anchor_config(control.text(),relation)
                    if not any(rule['selector']==selector for rule in config['anchors']):
                        config['anchors'].append({'selector':selector,'by':'CSS选择器' if chosen.get('css') else 'XPath','relation':relation})
                    control.setText(encode_anchor_config(config))
                    if 'by' in self._controls:self._set_control_value(self._controls['by'],'锚点定位')
                else:
                    anchor_mode='by' in self._controls and self._control_value(self._controls['by'])=='锚点定位'
                    control.setText(str(chosen.get('anchorSelector') or selector) if anchor_mode else selector)
                    if 'by' in self._controls and not anchor_mode:self._set_control_value(self._controls['by'],'CSS选择器')
                control.setFocus();control.selectAll()
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
