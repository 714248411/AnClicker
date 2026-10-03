"""按下键盘：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .按下键盘_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "按下键盘"
    DISPLAY_NAME = "按下键盘"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("按键", "按键（用 + 组合）", "text", "enter", required=True),
        FieldSpec("按压时长", "按压时长（毫秒）", "int", 50, minimum=0, maximum=3600000),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "按下键盘"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"按下键盘执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        keys_ = [item_.strip() for item_ in str(actions.parameter(command.parameters, "按键", default="enter")).split("+") if item_.strip()]
        duration_ = float(actions.parameter(command.parameters, "按压时长", default=50)) / 1000
        gui_ = actions.pyautogui_module()
        for key_ in keys_:
            gui_.keyDown(key_)
        actions.wait_seconds(duration_)
        for key_ in reversed(keys_):
            gui_.keyUp(key_)
        context.emit(f"按下键盘：{'+'.join(keys_)}")
        return keys_
