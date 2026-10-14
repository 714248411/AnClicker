"""图像点击：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.common.image_click_editor import ImageClickEditorMixin
from instructions.models import CommandRecord, ExecutionContext
from .图像点击_ui import Ui_InstructionEditor


class InstructionEditor(ImageClickEditorMixin, SchemaInstructionEditor):
    TYPE_ID = "图像点击"
    DISPLAY_NAME = "图像点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "图像路径", "path", "", required=True),
        FieldSpec("动作", "鼠标动作", "choice", "左键单击", ("左键单击", "左键双击", "左键三击", "右键单击", "右键双击", "仅移动鼠标", "无操作")),
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
        detection_only_ = command.parameters.get("动作") == "无操作"
        skip_, timeout_ = actions.image_error_timeout(command.parameters)
        position_ = actions.click_image(command.parameters, context, min_search_time=timeout_)
        if context.stop_requested:
            return False
        if position_ is None:
            # Detection is a gate: a missing image must reach the host error
            # handler/error edge, even in old files with automatic image skip.
            if skip_ and not detection_only_:
                return False
            raise FileNotFoundError("未找到指定图像（图片存在判断未通过）" if detection_only_ else "未找到指定图像")
        x_, y_ = position_
        label_ = "图片存在（无操作）" if detection_only_ else "图像点击"
        context.emit(f"{label_}：{x_},{y_}")
        return (x_, y_)
