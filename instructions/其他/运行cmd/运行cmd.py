"""运行cmd：独立参数编辑器与执行器。"""

from __future__ import annotations

import subprocess
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .运行cmd_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "运行cmd"
    DISPLAY_NAME = "运行cmd"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("命令", "CMD命令", "multiline", "", required=True),
        FieldSpec("等待完成", "等待命令完成", "bool", True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "运行cmd"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"运行cmd执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        command_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, "命令", "内容", default="")))
        if actions.parameter(command.parameters, "等待完成", default=True):
            result_ = actions.run_process(command_, shell_=True)
            context.emit(result_.stdout.rstrip())
            return result_.returncode
        process_ = subprocess.Popen(command_, shell=True)
        context.emit(f"运行cmd：PID {process_.pid}")
        return process_.pid
