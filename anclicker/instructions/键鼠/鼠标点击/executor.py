"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'button_event': ('from', 'anclicker.execution.recorded_input', ('button_event',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '鼠标点击'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'鼠标点击执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        gui_ = actions.pyautogui_module()
        button_event = _module_imports.load('button_event')
        button_ = {'左键': 'left', '右键': 'right', '中键': 'middle', '侧键1': 'x1', '侧键2': 'x2'}.get(str(actions.parameter(p_, '鼠标', default='左键')))
        recorded_action_ = p_.get('录制动作')
        if recorded_action_ in {'按下', '松开'}:
            button_ = p_.get('录制鼠标键', button_)
            options_ = actions.recording_options(command)
            if p_.get('录制坐标'):
                gui_.moveTo(*actions.point(p_['录制坐标']), **options_)
            held_ = context.metadata.setdefault('recorded_buttons', set())
            if recorded_action_ == '按下':
                held_.add(button_)
                gui_.failSafeCheck()
                button_event(context, button_, True, gui_)
            else:
                button_event(context, button_, False, gui_)
                held_.discard(button_)
            return True
        if button_ is None:
            raise ValueError('其他鼠标键需通过录制生成，或选择明确的鼠标按键')
        modifier_ = str(actions.parameter(p_, '辅助键', default='')).strip()
        pressed_keys_ = []
        try:
            if not actions.wait_interruptibly(context, 0):
                return False
            if modifier_:
                pressed_keys_.append(modifier_)
                gui_.keyDown(modifier_)
            for index_ in range(int(actions.parameter(p_, '次数', default=1))):
                if not actions.wait_interruptibly(context, 0):
                    return False
                try:
                    if button_ in {'left', 'right', 'middle'}:
                        gui_.mouseDown(button=button_)
                    else:
                        gui_.failSafeCheck()
                        button_event(context, button_, True, gui_)
                    if not actions.wait_interruptibly(context, float(actions.parameter(p_, '按压', default=50)) / 1000):
                        return False
                finally:
                    actions.release_inputs(context, gui_, buttons=[button_])
                if index_ + 1 < int(actions.parameter(p_, '次数', default=1)):
                    if not actions.wait_interruptibly(context, float(actions.parameter(p_, '间隔', default=100)) / 1000):
                        return False
        finally:
            actions.release_inputs(context, gui_, keys=pressed_keys_)
        context.emit('鼠标点击完成')
        return True
