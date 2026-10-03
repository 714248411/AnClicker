"""窗口控制：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .窗口控制_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "窗口控制"
    DISPLAY_NAME = "窗口控制"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("标题包含", "窗口标题包含", "text", "", required=True),
        FieldSpec("操作", "窗口操作", "choice", "激活", ("激活", "最小化", "最大化", "还原", "关闭")),
        FieldSpec("报错", "未找到时报错", "bool", True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "窗口控制"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"窗口控制执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        import pygetwindow
        p_ = command.parameters
        title_ = str(actions.parameter(p_, "标题包含", default=""))
        windows_ = pygetwindow.getWindowsWithTitle(title_)
        if not windows_:
            if actions.parameter(p_, "报错", default=True):
                raise RuntimeError(f"未找到窗口：{title_}")
            return False
        window_ = windows_[0]
        operation_ = str(actions.parameter(p_, "操作", default="激活"))
        method_ = {"激活": "activate", "最小化": "minimize", "最大化": "maximize", "还原": "restore", "关闭": "close"}[operation_]
        getattr(window_, method_)()
        context.emit(f"窗口控制：{operation_}")
        return True
