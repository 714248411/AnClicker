"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'io': ('import', 'io', (), False),
    'win32clipboard': ('import', 'win32clipboard', (), False),
    'win32con': ('import', 'win32con', (), False),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '屏幕截图'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'屏幕截图执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        path_ = actions.substitute_variables(context, str(actions.parameter(p_, '保存路径', '路径', default='')))
        region_ = actions.region(actions.parameter(p_, '区域')) if actions.parameter(p_, '截图类型', default='全屏截图') == '区域截图' else None
        image_ = actions.pyautogui_module().screenshot(region=region_)
        if actions.parameter(p_, '截图后', default='保存到路径') == '写入剪切板':
            io = _module_imports.load('io')
            win32clipboard = _module_imports.load('win32clipboard')
            win32con = _module_imports.load('win32con')
            output_ = io.BytesIO()
            image_.convert('RGB').save(output_, 'BMP')
            data_ = output_.getvalue()[14:]
            output_.close()
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, data_)
            finally:
                win32clipboard.CloseClipboard()
            context.emit('屏幕截图已写入剪切板')
            return 'clipboard'
        if not path_:
            raise ValueError('保存到路径时必须设置保存路径')
        actions.ensure_parent(path_)
        image_.save(path_)
        context.emit(f'屏幕截图：{path_}')
        return path_
