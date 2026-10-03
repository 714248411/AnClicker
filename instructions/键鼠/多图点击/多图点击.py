"""多图点击：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .多图点击_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "多图点击"
    DISPLAY_NAME = "多图点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "图像路径（每行一个）", "multiline", "", required=True),
        FieldSpec("动作", "鼠标动作", "choice", "左键单击", ("左键单击", "左键双击", "右键单击", "右键双击", "仅移动鼠标")),
        FieldSpec("异常", "全部未找到", "text", "自动略过"),
        FieldSpec("区域", "识别区域 x,y,w,h"),
        FieldSpec("灰度", "灰度识别", "bool", False),
        FieldSpec("精度", "识别精度", "float", 0.8, minimum=0.01, maximum=1.0),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "多图点击"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"多图点击执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        paths_ = str(actions.parameter(command.parameters, "图像路径", default="")).replace(";", "\n").replace("、", "\n").splitlines()
        for path_ in (item_.strip() for item_ in paths_ if item_.strip()):
            parameters_ = dict(command.parameters)
            parameters_["图像路径"] = path_
            point_ = actions.locate_image(parameters_, context)
            if point_ is not None:
                x_, y_ = int(point_.x), int(point_.y)
                actions.mouse_action(str(actions.parameter(parameters_, "动作", default="左键单击")), x_, y_)
                context.emit(f"多图点击命中：{path_}")
                return path_
        if actions.parameter(command.parameters, "异常", default="自动略过") in {"自动跳过", "自动略过"}:
            return False
        raise FileNotFoundError("未找到任一指定图像")
