"""中键激活：独立参数编辑器与执行器。"""

from __future__ import annotations

import sys

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .中键激活_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "中键激活"
    DISPLAY_NAME = "中键激活"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("类型", "激活类型", "choice", "模拟点击", ("模拟点击", "结束等待")),
        FieldSpec("次数", "次数", "int", 1, minimum=1, maximum=9999),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "中键激活"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"中键激活执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        context.emit("等待按下鼠标中键")
        count_ = int(actions.parameter(command.parameters, "次数", default=1))
        if sys.platform == "darwin":
            from pynput import mouse as pynput_mouse

            def on_click(_x, _y, button_, pressed_):
                if pressed_ and button_ == pynput_mouse.Button.middle:
                    return False
                return None

            with pynput_mouse.Listener(on_click=on_click) as listener_:
                listener_.join()
            if actions.parameter(command.parameters, "类型", default="模拟点击") == "模拟点击":
                controller_ = pynput_mouse.Controller()
                controller_.click(pynput_mouse.Button.left, count_)
        else:
            import mouse

            mouse.wait(button="middle")
            if actions.parameter(command.parameters, "类型", default="模拟点击") == "模拟点击":
                for _ in range(count_):
                    mouse.click(button="left")
        context.emit(f"中键激活：{count_}次")
        return count_
