"""中键激活：独立参数编辑器与执行器。"""

from __future__ import annotations

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
        if context.stop_requested:
            return None
        count_ = int(actions.parameter(command.parameters, "次数", default=1))
        mode_ = actions.parameter(command.parameters, "类型", default="模拟点击")
        if not 1 <= count_ <= 9999 or mode_ not in ('模拟点击', '结束等待'):
            raise ValueError('中键激活参数无效')
        from instructions.common.middle_wait import wait_for_middle
        if not wait_for_middle(context):
            context.emit('中键激活已取消')
            return None
        if mode_ == '模拟点击':
            for _ in range(count_):
                checkpoint_ = context.metadata.get('wait_interruptibly')
                if context.stop_requested or (checkpoint_ is not None and not checkpoint_(0, context)):
                    return None
                actions.pyautogui_module().click(button='left')
        context.emit(f"中键激活：{count_}次")
        return count_
