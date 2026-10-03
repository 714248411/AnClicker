"""获取Excel：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .获取Excel_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取Excel"
    DISPLAY_NAME = "获取Excel"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("工作簿", "工作簿路径", "path", "", required=True),
        FieldSpec("工作表", "工作表"),
        FieldSpec("单元格", "单元格", "text", "A1", required=True),
        FieldSpec("变量", "变量名称", "text", "Excel值", required=True),
        FieldSpec("递增", "按循环次数递增行", "bool", False),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "获取Excel"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"获取Excel执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        cell_ = actions.resolve_increment(str(actions.parameter(p_, "单元格", default="A1")), bool(actions.parameter(p_, "递增", default=False)), context.iteration)
        workbook_, _, cell_object_ = actions.workbook_cell(str(actions.parameter(p_, "工作簿", default="")), str(actions.parameter(p_, "工作表", default="")), cell_)
        try:
            value_ = cell_object_.value
        finally:
            workbook_.close()
        actions.store_variable(context, p_, value_)
        context.emit(f"获取Excel：{cell_}={value_}")
        return value_
