"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'key_event': ('from', 'anclicker.execution.recorded_input', ('key_event',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '按下键盘'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'按下键盘执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        keys_ = [item_.strip() for item_ in str(actions.parameter(command.parameters, '按键', default='enter')).split('+') if item_.strip()]
        duration_ = float(actions.parameter(command.parameters, '按压时长', default=50)) / 1000
        gui_ = actions.pyautogui_module()
        recorded_action_ = command.parameters.get('录制动作')
        if recorded_action_ in {'按下', '松开'}:
            key_event = _module_imports.load('key_event')
            key_ = str(command.parameters['按键'])
            held_ = context.metadata.setdefault('recorded_keys', set())
            if recorded_action_ == '按下':
                held_.add(key_)
                gui_.failSafeCheck()
                key_event(context, key_, True, gui_)
            else:
                key_event(context, key_, False, gui_)
                held_.discard(key_)
            return key_
        pressed_ = []
        try:
            for key_ in keys_:
                if not actions.wait_interruptibly(context, 0):
                    return None
                pressed_.append(key_)
                gui_.keyDown(key_)
            if not actions.wait_interruptibly(context, duration_):
                return None
        finally:
            actions.release_inputs(context, gui_, keys=pressed_)
        context.emit(f"按下键盘：{'+'.join(keys_)}")
        return keys_
