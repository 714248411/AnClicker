"""时间等待：独立参数编辑器与执行器。"""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .时间等待_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "时间等待"
    DISPLAY_NAME = "时间等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("类型", "等待类型", "choice", "时间等待", ("时间等待", "随机等待", "定时等待")),
        FieldSpec("时长", "时长", "float", 1, minimum=0, maximum=86400),
        FieldSpec("单位", "单位", "choice", "秒", ("毫秒", "秒", "分钟")),
        FieldSpec("最小", "随机最小秒数", "float", 1, minimum=0, maximum=86400),
        FieldSpec("最小单位", "随机最小值单位", "choice", "秒", ("毫秒", "秒", "分钟")),
        FieldSpec("最大", "随机最大秒数", "float", 3, minimum=0, maximum=86400),
        FieldSpec("最大单位", "随机最大值单位", "choice", "秒", ("毫秒", "秒", "分钟")),
        FieldSpec("时间", "目标时间 HH:MM:SS"),
        FieldSpec("检测频率", "检测频率", "float", 0.2, minimum=0.01, maximum=60),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "时间等待"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"时间等待执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        type_ = str(actions.parameter(p_, "类型", default="时间等待"))
        if type_ == "随机等待":
            minimum_ = self._duration_seconds(
                actions.parameter(p_, "最小", default=1),
                str(actions.parameter(p_, "最小单位", default="秒")),
            )
            maximum_ = self._duration_seconds(
                actions.parameter(p_, "最大", default=3),
                str(actions.parameter(p_, "最大单位", default="秒")),
            )
            if minimum_ > maximum_:
                raise ValueError("随机等待最小值不能大于最大值")
            seconds_ = random.uniform(minimum_, maximum_)
        elif type_ == "定时等待":
            target_ = datetime.strptime(str(actions.parameter(p_, "时间", default="00:00:00")), "%H:%M:%S").time()
            now_ = datetime.now()
            target_dt_ = datetime.combine(now_.date(), target_)
            if target_dt_ <= now_:
                target_dt_ += timedelta(days=1)
            interval_ = self._duration_seconds(
                actions.parameter(p_, "检测频率", default=0.2),
                str(actions.parameter(p_, "检测频率单位", default="秒")),
            )
            interval_ = max(0.01, interval_)
            while not context.stop_requested:
                remaining_ = (target_dt_ - datetime.now()).total_seconds()
                if remaining_ <= 0:
                    break
                actions.wait_seconds(min(interval_, remaining_))
            seconds_ = max(0.0, (target_dt_ - now_).total_seconds())
        else:
            seconds_ = self._duration_seconds(
                actions.parameter(p_, "时长", default=1),
                str(actions.parameter(p_, "单位", default="秒")),
            )
        if type_ != "定时等待":
            actions.wait_seconds(seconds_)
        context.emit(f"时间等待：{seconds_:.3f}秒")
        return seconds_

    @staticmethod
    def _duration_seconds(value_, default_unit_: str = "秒") -> float:
        unit_ = default_unit_
        number_ = value_
        if isinstance(value_, str) and "-" in value_:
            number_text_, unit_text_ = value_.rsplit("-", maxsplit=1)
            number_, unit_ = number_text_, unit_text_
        factor_ = {"毫秒": 0.001, "秒": 1.0, "分钟": 60.0}.get(str(unit_))
        if factor_ is None:
            raise ValueError(f"不支持的时间单位：{unit_}")
        return max(0.0, float(number_) * factor_)
