"""图像点击：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .图像点击_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "图像点击"
    DISPLAY_NAME = "图像点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "图像路径", "path", "", required=True),
        FieldSpec("动作", "鼠标动作", "choice", "左键单击", ("左键单击", "左键双击", "左键三击", "右键单击", "右键双击", "仅移动鼠标")),
        FieldSpec("异常", "未找到图像", "text", "自动略过"),
        FieldSpec("区域", "识别区域 x,y,w,h"),
        FieldSpec("灰度", "灰度识别", "bool", False),
        FieldSpec("精度", "识别精度", "float", 0.8, minimum=0.01, maximum=1.0),
        FieldSpec("点击位置", "点击偏移 x,y", "text", "(0,0)"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "图像点击"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"图像点击执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        point_, skip_ = actions.locate_image_with_policy(command.parameters, context)
        if point_ is None:
            if skip_:
                return False
            raise FileNotFoundError("未找到指定图像")
        offset_ = actions.parameter(command.parameters, "点击位置", default="(0,0)")
        if str(offset_).replace(" ", "") in {"(随机,随机)", "随机,随机"}:
            offset_x_, offset_y_ = actions.image_random_offset(command.parameters, context)
        else:
            offset_x_, offset_y_ = actions.point(offset_)
        x_, y_ = int(point_.x) + offset_x_, int(point_.y) + offset_y_
        actions.mouse_action(str(actions.parameter(command.parameters, "动作", default="左键单击")), x_, y_)
        context.emit(f"图像点击：{x_},{y_}")
        return (x_, y_)
