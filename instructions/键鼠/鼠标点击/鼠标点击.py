"""鼠标点击：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .鼠标点击_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "鼠标点击"
    DISPLAY_NAME = "鼠标点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("鼠标", "鼠标按键", "choice", "左键", ("左键", "右键", "中键")),
        FieldSpec("次数", "点击次数", "int", 1, minimum=1, maximum=9999),
        FieldSpec("间隔", "点击间隔（毫秒）", "int", 100, minimum=0, maximum=3600000),
        FieldSpec("按压", "按压时长（毫秒）", "int", 50, minimum=0, maximum=3600000),
        FieldSpec("辅助键", "辅助键"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "鼠标点击"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"鼠标点击执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        gui_ = actions.pyautogui_module()
        button_ = {"左键": "left", "右键": "right", "中键": "middle"}.get(str(actions.parameter(p_, "鼠标", default="左键")), "left")
        modifier_ = str(actions.parameter(p_, "辅助键", default="")).strip()
        if modifier_:
            gui_.keyDown(modifier_)
        try:
            for index_ in range(int(actions.parameter(p_, "次数", default=1))):
                gui_.mouseDown(button=button_)
                actions.wait_seconds(float(actions.parameter(p_, "按压", default=50)) / 1000)
                gui_.mouseUp(button=button_)
                if index_ + 1 < int(actions.parameter(p_, "次数", default=1)):
                    actions.wait_seconds(float(actions.parameter(p_, "间隔", default=100)) / 1000)
        finally:
            if modifier_:
                gui_.keyUp(modifier_)
        context.emit("鼠标点击完成")
        return True
