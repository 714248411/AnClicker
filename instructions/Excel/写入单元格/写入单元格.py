"""写入单元格：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .写入单元格_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "写入单元格"
    DISPLAY_NAME = "写入单元格"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("工作簿", "工作簿路径", "path", "", required=True),
        FieldSpec("工作表", "工作表"),
        FieldSpec("单元格", "单元格", "text", "A1", required=True),
        FieldSpec("递增", "按循环次数递增行", "bool", False),
        FieldSpec("文本", "写入文本", "multiline", ""),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "写入单元格"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"写入单元格执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        path_ = str(actions.parameter(p_, "工作簿", default=""))
        cell_ = actions.resolve_increment(str(actions.parameter(p_, "单元格", default="A1")), bool(actions.parameter(p_, "递增", default=False)), context.iteration)
        workbook_, _, cell_object_ = actions.workbook_cell(path_, str(actions.parameter(p_, "工作表", default="")), cell_, data_only=False)
        try:
            value_ = actions.substitute_variables(context, str(actions.parameter(p_, "文本", default="")))
            cell_object_.value = value_
            workbook_.save(path_)
        finally:
            workbook_.close()
        context.emit(f"写入单元格：{cell_}")
        return value_
