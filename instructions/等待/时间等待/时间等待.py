"""时间等待：独立参数编辑器与执行器。"""

from __future__ import annotations

from datetime import datetime, timedelta
import random
import time
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

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        from PySide6.QtWidgets import QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QWidget
        holder = QWidget(self)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        for value, label in (('时间等待', '等待时长'), ('定时等待', '等待到目标时间'), ('随机等待', '随机等待')):
            button = QCheckBox(label, holder)
            self.mode_group.addButton(button)
            self.mode_buttons[value] = button
            button.toggled.connect(lambda checked, mode=value: self._controls['类型'].setCurrentText(mode) if checked else None)
            layout.addWidget(button)
        self.ui.parameterFormLayout.insertRow(0, '等待模式', holder)
        self.ui.parameterFormLayout.setRowVisible(1, False)
        self.mode_hint = QLabel(self)
        self.mode_hint.setWordWrap(True)
        self.ui.parameterFormLayout.addRow(self.mode_hint)
        self._controls['类型'].currentTextChanged.connect(self._update_mode)
        self._update_mode()

    def _update_mode(self, *_):
        from PySide6.QtCore import QSignalBlocker
        mode = self._controls['类型'].currentText()
        for value, button in self.mode_buttons.items():
            with QSignalBlocker(button):
                button.setChecked(value == mode)
        active = {'时间等待': {'时长', '单位'}, '定时等待': {'时间', '检测频率'},
                  '随机等待': {'最小', '最小单位', '最大', '最大单位'}}[mode]
        for index, field in enumerate(self.FIELDS[1:], 1):
            enabled = field.key in active
            self.ui.parameterFormLayout.setRowVisible(index + 1, enabled)
            self._controls[field.key].setEnabled(enabled)
        hints = {'时间等待': '例如设置 5 秒：执行到本指令 → 等待 5 秒 → 执行下一条。目标时间不参与此模式。',
                 '定时等待': '等待到指定的时钟时间后继续；如果今天的时间已经过去，则等待到明天。',
                 '随机等待': '在最小和最大时长之间随机等待一次，结束后执行下一条。'}
        self.mode_hint.setText(hints[mode])

    def _validate_parameters(self, parameters):
        active = dict(parameters)
        if active.get('类型') != '定时等待':
            active['时间'] = ''
        elif not str(active.get('时间', '')).strip():
            raise ValueError('请选择目标时间，格式为 HH:MM:SS')
        super()._validate_parameters(active)


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
            context.emit(f'等待到目标时间：{target_dt_:%Y-%m-%d %H:%M:%S}')
            while not context.stop_requested:
                remaining_ = (target_dt_ - datetime.now()).total_seconds()
                if remaining_ <= 0:
                    break
                wait_ = context.metadata.get('wait_interruptibly')
                if wait_ is not None:
                    if not wait_(min(interval_, remaining_), context):
                        break
                else:
                    if not self._wait(min(interval_, remaining_), context):
                        break
            seconds_ = max(0.0, (target_dt_ - now_).total_seconds())
        elif type_ == '时间等待':
            seconds_ = self._duration_seconds(
                actions.parameter(p_, "时长", default=1),
                str(actions.parameter(p_, "单位", default="秒")),
            )
        else:
            raise ValueError(f'未知等待类型：{type_}')
        if type_ != "定时等待":
            context.emit(f'开始等待：{seconds_:.3f}秒')
            wait_ = context.metadata.get('wait_interruptibly')
            if wait_ is not None:
                wait_(seconds_, context)
            else:
                self._wait(seconds_, context)
        if context.stop_requested:
            context.emit('时间等待已中止')
            return None
        context.emit(f"时间等待完成：{seconds_:.3f}秒，继续下一条")
        return seconds_

    @staticmethod
    def _wait(seconds, context):
        deadline = time.monotonic() + max(0.0, seconds)
        while not context.stop_requested:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            actions.wait_seconds(min(0.05, remaining))
        return False

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
