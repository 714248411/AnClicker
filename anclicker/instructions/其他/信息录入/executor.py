"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pyperclip': ('import', 'pyperclip', (), False),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '信息录入'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'信息录入执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        cell_ = actions.resolve_increment(str(actions.parameter(p_, '单元格', default='A1')), bool(actions.parameter(p_, '递增', default=False)), context.iteration)
        (workbook_, _, cell_object_) = actions.workbook_cell(str(actions.parameter(p_, '工作簿', default='')), str(actions.parameter(p_, '工作表', default='')), cell_)
        try:
            value_ = cell_object_.value
        finally:
            workbook_.close()
        if value_ in (None, ''):
            if actions.parameter(p_, '空值处理', default='抛出异常') == '自动跳过':
                return False
            raise ValueError(f'Excel 单元格 {cell_} 的值为空')
        (skip_, timeout_) = actions.image_error_timeout(p_)
        position_ = actions.click_image(dict(p_, 动作='左键三击'), context, min_search_time=timeout_)
        if context.stop_requested:
            return False
        if position_ is None:
            if skip_:
                return False
            raise FileNotFoundError('未找到信息录入位置图像')
        gui_ = actions.pyautogui_module()
        if actions.parameter(p_, '模拟输入', default=False):
            gui_.write(str(value_), interval=0.03)
        else:
            pyperclip = _module_imports.load('pyperclip')
            pyperclip.copy(str(value_))
            gui_.hotkey('ctrl', 'v')
        context.emit(f'信息录入：{value_}')
        return value_
