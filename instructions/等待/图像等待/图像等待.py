"""图像等待：独立参数编辑器与执行器。"""

from __future__ import annotations

import time
import math
import os
from dataclasses import replace
from PySide6.QtWidgets import QMessageBox
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.common.image_wait import normalize_image_wait
from .图像等待_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "图像等待"
    DISPLAY_NAME = "图像等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "图像路径", "path", "", required=True),
        FieldSpec("等待类型", "等待类型", "choice", "等待出现", ("等待出现", "等待消失")),
        FieldSpec("超时时间", "超时秒数（0 不限）", "float", 10, minimum=0, maximum=86400),
        FieldSpec("区域", "识别区域 x,y,w,h"),
        FieldSpec("精度", "识别精度", "float", 0.8, minimum=0.01, maximum=1.0),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._controls['等待类型'].setToolTip('兼容旧版：等待到指定图像出现 / 等待到指定图像消失')
        self._controls['超时时间'].setSpecialValueText('不限（可停止）')

    def load_draft(self, draft):
        if not isinstance(draft, InstructionDraft):
            draft = InstructionDraft.from_mapping(draft)
        super().load_draft(replace(draft, parameters=normalize_image_wait(draft.parameters)))

    def _test_if_valid(self):
        # The shared editor test handler runs on the GUI thread. Never start
        # an unlimited wait there; the ordinary worker has stop/Esc handling.
        if self._controls['超时时间'].value() == 0:
            QMessageBox.information(self, '不限时等待测试',
                                    '请保存指令后使用表格单行运行测试，可用停止按钮或 Esc 中断。')
            return
        super()._test_if_valid()


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "图像等待"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"图像等待执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        if context.stop_requested:
            return None
        p_ = normalize_image_wait(command.parameters)
        timeout_ = float(actions.parameter(p_, "超时时间", default=10))
        if not math.isfinite(timeout_) or not 0 <= timeout_ <= 86400:
            raise ValueError('图像等待超时时间必须为 0–86400 秒')
        mode_ = actions.parameter(p_, "等待类型", default="等待出现")
        if mode_ not in ('等待出现', '等待消失'):
            raise ValueError(f'未知图像等待类型：{mode_}')
        image_ = actions.resolve_image_path(p_, context)
        if not os.path.isfile(image_):
            raise FileNotFoundError(f'图像文件不存在：{image_}')
        p_['图像路径'] = image_
        wait_disappear_ = mode_ == "等待消失"
        deadline_ = time.monotonic() + timeout_ if timeout_ else None
        context.emit(f'正在等待指定图像{"消失" if wait_disappear_ else "出现"}…')
        while not context.stop_requested:
            wait_ = context.metadata.get('wait_interruptibly')
            if wait_ is not None and not wait_(0, context):
                return None
            found_ = actions.locate_image(p_, context) is not None
            if context.stop_requested:
                return None
            if found_ != wait_disappear_:
                context.emit("图像等待完成")
                return found_
            if deadline_ is not None and time.monotonic() >= deadline_:
                raise TimeoutError("图像等待超时")
            if wait_ is not None:
                if not wait_(0.1, context):
                    return None
            else:
                actions.wait_seconds(0.1)
        return None
