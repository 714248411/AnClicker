"""信息录入：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .信息录入_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "信息录入"
    DISPLAY_NAME = "信息录入"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "输入位置图像", "path", "", required=True),
        FieldSpec("工作簿", "工作簿路径", "path", "", required=True),
        FieldSpec("工作表", "工作表"),
        FieldSpec("单元格", "单元格", "text", "A1", required=True),
        FieldSpec("递增", "按循环次数递增行", "bool", False),
        FieldSpec("模拟输入", "逐字符模拟输入", "bool", False),
        FieldSpec("异常", "图像查找超时", "text", "自动略过"),
        FieldSpec("空值处理", "Excel空值处理", "choice", "抛出异常", ("抛出异常", "自动跳过")),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "信息录入"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"信息录入执行器不能执行{command.type_id}")
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
        if value_ in (None, ""):
            if actions.parameter(p_, "空值处理", default="抛出异常") == "自动跳过":
                return False
            raise ValueError(f"Excel 单元格 {cell_} 的值为空")
        point_, skip_ = actions.locate_image_with_policy(p_, context)
        if point_ is None:
            if skip_:
                return False
            raise FileNotFoundError("未找到信息录入位置图像")
        actions.mouse_action("左键三击", int(point_.x), int(point_.y))
        gui_ = actions.pyautogui_module()
        if actions.parameter(p_, "模拟输入", default=False):
            gui_.write(str(value_), interval=0.03)
        else:
            import pyperclip

            pyperclip.copy(str(value_))
            gui_.hotkey("ctrl", "v")
        context.emit(f"信息录入：{value_}")
        return value_
