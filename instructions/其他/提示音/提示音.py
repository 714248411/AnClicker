"""提示音：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .提示音_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "提示音"
    DISPLAY_NAME = "提示音"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("类型", "提示音类型", "choice", "系统提示音", ("系统提示音", "蜂鸣", "TTS")),
        FieldSpec("频率", "蜂鸣频率", "int", 800, minimum=37, maximum=32767),
        FieldSpec("持续", "持续毫秒", "int", 300, minimum=1, maximum=60000),
        FieldSpec("次数", "播放次数", "int", 1, minimum=1, maximum=999),
        FieldSpec("间隔", "播放间隔", "float", 0.1, minimum=0, maximum=60),
        FieldSpec("提示类型", "系统提示类型", "choice", "信息", ("警告", "错误", "询问", "信息", "系统启动", "系统关闭")),
        FieldSpec("内容", "TTS内容", "multiline", ""),
        FieldSpec("语速", "TTS语速", "int", 200, minimum=50, maximum=500),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "提示音"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"提示音执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        type_ = str(actions.parameter(p_, "类型", default="系统提示音"))
        count_ = int(actions.parameter(p_, "次数", default=1))
        if type_ in {"TTS", "播放语音"}:
            import pyttsx4
            engine_ = pyttsx4.init()
            engine_.setProperty("rate", int(actions.parameter(p_, "语速", default=200)))
            engine_.say(str(actions.parameter(p_, "内容", default="")))
            engine_.runAndWait()
        else:
            import winsound
            for index_ in range(count_):
                if type_ in {"蜂鸣", "音频信号"}:
                    winsound.Beep(int(actions.parameter(p_, "频率", default=800)), int(actions.parameter(p_, "持续", default=300)))
                else:
                    sound_type_ = str(actions.parameter(p_, "提示类型", default="信息"))
                    sound_alias_ = {
                        "警告": "SystemAsterisk", "系统警告": "SystemAsterisk",
                        "错误": "SystemExclamation", "系统错误": "SystemExclamation",
                        "询问": "SystemQuestion", "系统询问": "SystemQuestion",
                        "信息": "SystemHand", "系统信息": "SystemHand",
                        "系统启动": "SystemStart", "系统关闭": "SystemExit",
                    }.get(sound_type_)
                    if sound_alias_:
                        winsound.PlaySound(sound_alias_, winsound.SND_ALIAS)
                    else:
                        winsound.MessageBeep()
                if index_ + 1 < count_:
                    actions.wait_seconds(float(actions.parameter(p_, "间隔", default=0.1)))
        context.emit("提示音播放完成")
        return True
