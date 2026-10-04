"""按键等待：独立参数编辑器与执行器。"""

from __future__ import annotations

import sys

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .按键等待_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "按键等待"
    DISPLAY_NAME = "按键等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("按键", "等待按键", "text", "enter", required=True),
        FieldSpec("等待类型", "等待类型", "choice", "按键等待", ("按键等待",)),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "按键等待"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"按键等待执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        wait_type_ = str(actions.parameter(command.parameters, "等待类型", default="按键等待"))
        if wait_type_ != "按键等待":
            raise ValueError(f"不支持的按键等待类型：{wait_type_}")
        key_ = str(actions.parameter(command.parameters, "按键", default="enter"))
        if sys.platform == "darwin":
            from pynput import keyboard as pynput_keyboard

            expected_ = getattr(pynput_keyboard.Key, key_.lower(), None)

            def on_press(pressed_):
                if expected_ is not None and pressed_ == expected_:
                    return False
                if getattr(pressed_, "char", None) == key_:
                    return False
                return None

            with pynput_keyboard.Listener(on_press=on_press) as listener_:
                listener_.join()
        else:
            import keyboard

            keyboard.wait(key_)
        context.emit(f"检测到按键：{key_}")
        return key_
