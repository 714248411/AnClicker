"""运行外部文件：独立参数编辑器与执行器。"""

from __future__ import annotations

import os
import shlex
import subprocess
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .运行外部文件_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "运行外部文件"
    DISPLAY_NAME = "运行外部文件"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("文件路径", "文件路径", "path", "", required=True),
        FieldSpec("参数", "启动参数"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "运行外部文件"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"运行外部文件执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        path_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, "文件路径", "路径", default="")))
        arguments_ = str(actions.parameter(command.parameters, "参数", default="")).strip()
        if arguments_:
            process_ = subprocess.Popen([path_, *shlex.split(arguments_)])
            result_ = process_.pid
        else:
            os.startfile(path_)
            result_ = path_
        context.emit(f"运行外部文件：{path_}")
        return result_
