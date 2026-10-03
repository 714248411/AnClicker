"""运行Python：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .运行Python_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "运行Python"
    DISPLAY_NAME = "运行Python"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("代码", "Python代码", "multiline", "", required=True),
        FieldSpec("返回值", "结果变量名", "text", "result"),
        FieldSpec("变量", "写入变量池", "text", "Python返回值"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "运行Python"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"运行Python执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        return_value_ = actions.parameter(p_, "返回值", default="")
        if isinstance(return_value_, bool):
            result_name_ = "result" if return_value_ else ""
            variable_name_ = str(actions.parameter(p_, "变量", default="")) if return_value_ else ""
        else:
            result_name_ = str(return_value_ or "").strip()
            variable_name_ = str(actions.parameter(p_, "变量", default="")).strip() if result_name_ else ""
        result_ = actions.run_python_code(
            context,
            str(actions.parameter(p_, "代码", "内容", default="")),
            result_name_,
            variable_name_,
        )
        context.emit("运行Python完成")
        return result_
