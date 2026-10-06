"""Screen pixel comparison with explicit yes/no flow branches."""
from __future__ import annotations

import re
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor, actions
from instructions.models import CommandRecord, ExecutionContext
from .颜色判断_ui import Ui_InstructionEditor


def rgb(value):
    text = str(value).strip()
    if re.fullmatch(r'#[0-9a-fA-F]{6}', text):
        return tuple(int(text[i:i+2], 16) for i in (1, 3, 5))
    if isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        parts = text.strip('()[]').replace('，', ',').split(',')
    if len(parts) != 3 or any(not re.fullmatch(r'\d{1,3}', str(p).strip()) for p in parts):
        raise ValueError('颜色必须为 #RRGGBB 或 R,G,B（三个 0–255 的整数）')
    result = tuple(int(p) for p in parts)
    if any(p > 255 for p in result):
        raise ValueError('RGB 各分量必须在 0–255 之间')
    return result


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '颜色判断'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('坐标', '检测坐标 x,y', default='0,0', required=True),
        FieldSpec('颜色', '目标颜色', default='#FFFFFF', required=True),
        FieldSpec('容差', 'RGB 单通道容差', 'int', 0, minimum=0, maximum=255),
        FieldSpec('比较', '判断方式', 'choice', '相等', ('相等', '不相等')),
        FieldSpec('变量', '结果变量（可选）'),
    )

    def _validate_parameters(self, parameters_):
        super()._validate_parameters(parameters_)
        rgb(parameters_['颜色'])

    def _run_auxiliary(self, key_):
        if key_ == '颜色':
            try:
                initial = QColor(*rgb(self._controls[key_].text()))
            except ValueError:
                initial = QColor('#ffffff')
            color = QColorDialog.getColor(initial, self, '选择目标颜色')
            if color.isValid():
                self._controls[key_].setText(color.name().upper())
            return
        super()._run_auxiliary(key_)


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '颜色判断'
    CONSUMED_FIELDS = ('坐标', '颜色', '容差', '比较', '变量')

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError('颜色判断执行器收到不匹配的指令')
        handled, value = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return value
        if context.stop_requested:
            return None
        parameters = command.parameters
        position = actions.point(parameters.get('坐标', '0,0'))
        target = rgb(parameters.get('颜色', '#FFFFFF'))
        tolerance = parameters.get('容差', 0)
        if isinstance(tolerance, bool) or not str(tolerance).isdigit() or not 0 <= int(tolerance) <= 255:
            raise ValueError('颜色容差必须为 0–255 的整数')
        mode = parameters.get('比较', '相等')
        if mode not in ('相等', '不相等'):
            raise ValueError('颜色判断方式必须为相等或不相等')
        actual = rgb(actions.pyautogui_module().pixel(*position))
        matched = all(abs(a-b) <= int(tolerance) for a, b in zip(actual, target))
        result = matched if mode == '相等' else not matched
        context.metadata[f'flow_condition:{command.id}'] = result
        actions.store_variable(context, parameters, result)
        context.emit(f'颜色判断：坐标 {position}，实际 RGB {actual}，结果：{"是" if result else "否"}')
        return result
