"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import sys
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'Windows': ('from', 'anclicker.platform.background_runtime', ('Windows',), 0),
    'win32gui_win32con': ('from', 'anclicker.platform.window_zorder', ('set_window_zorder',), 0),
    'window_backend_': ('import', 'pygetwindow', (), True),
    'window_backend__2': ('import', 'pywinctl', (), True),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口控制'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'窗口控制执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        if sys.platform == 'win32':
            window_backend_ = _module_imports.load('window_backend_')
        else:
            window_backend_ = _module_imports.load('window_backend__2')
        p_ = command.parameters
        title_ = str(actions.parameter(p_, '标题包含', default=''))
        if not title_.strip():
            raise ValueError('请填写窗口标题或使用鼠标点选窗口')
        picked_ = p_.get('窗口定位')
        if sys.platform == 'win32' and isinstance(picked_, dict) and picked_:
            Windows = _module_imports.load('Windows')
            try:
                target_ = Windows().resolve(picked_)
                windows_ = [window_backend_.Win32Window(int(target_['窗口句柄']))]
            except RuntimeError:
                if actions.parameter(p_, '报错', default=True):
                    raise
                return False
        else:
            windows_ = window_backend_.getWindowsWithTitle(title_)
        if not windows_:
            if actions.parameter(p_, '报错', default=True):
                raise RuntimeError(f'未找到窗口：{title_}')
            return False
        window_ = windows_[0]
        operation_ = str(actions.parameter(p_, '操作', default='激活'))
        if operation_ in ('窗口移动', '窗口大小'):
            adjust_geometry(window_, operation_, p_)
        elif operation_ in ('置顶','置底'):
            if sys.platform == 'win32':
                set_window_zorder = _module_imports.load('win32gui_win32con')
                set_window_zorder(window_._hWnd, operation_)
            else:
                method_ = 'alwaysOnTop' if operation_ == '置顶' else 'alwaysOnBottom'
                method = getattr(window_,method_,None)
                if method is None or method(True) is False:
                    raise RuntimeError('当前系统或窗口不支持'+operation_)
        else:
            methods_ = {'激活':'activate','最小化':'minimize','最大化':'maximize','还原':'restore','关闭':'close'}
            if operation_ not in methods_:
                raise ValueError('未知窗口操作：'+operation_)
            getattr(window_, methods_[operation_])()
        context.emit(f'窗口控制：{operation_}')
        return True


def adjust_geometry(window, operation, parameters):
    """Use outer-window screen coordinates; negative coordinates support extra monitors."""
    def integer(key, default, minimum, maximum):
        value = float(actions.parameter(parameters, key, default=default))
        if not minimum <= value <= maximum or not value.is_integer():
            raise ValueError(key + '必须为范围内的整数')
        return int(value)

    if operation == '窗口移动':
        mode = str(actions.parameter(parameters, '移动方式', default='左上角坐标'))
        if mode not in ('左上角坐标', '相对当前位置'):
            raise ValueError('未知移动方式：' + mode)
        x, y = integer('X', 0, -100000, 100000), integer('Y', 0, -100000, 100000)
    elif operation == '窗口大小':
        anchor = str(actions.parameter(parameters, '大小锚点', default='左上角'))
        if anchor not in ('左上角', '中心点'):
            raise ValueError('未知大小锚点：' + anchor)
        width = integer('宽度', 800, 1, 100000)
        height = integer('高度', 600, 1, 100000)
    else:
        raise ValueError('未知几何操作：' + operation)
    # Restore before reading bounds so minimized sentinel coordinates are never used.
    if window.isMinimized or window.isMaximized:
        window.restore()
    left, top, old_width, old_height = window.left, window.top, window.width, window.height
    if operation == '窗口移动':
        if mode == '相对当前位置':
            x, y = left + x, top + y
        window.moveTo(x, y)
    else:
        window.resizeTo(width, height)
        if anchor == '中心点':
            # Respect application-enforced minimum sizes when preserving its centre.
            left = round(left + (old_width - window.width) / 2)
            top = round(top + (old_height - window.height) / 2)
        window.moveTo(left, top)
