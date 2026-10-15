"""Instruction execution implementation."""
from __future__ import annotations
import time
from anclicker.instructions.common import actions
import os
import math
from anclicker.execution.instruction_helpers.image_wait import normalize_image_wait
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '图像等待'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'图像等待执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        if context.stop_requested:
            return None
        p_ = normalize_image_wait(command.parameters)
        timeout_ = float(actions.parameter(p_, '超时时间', default=10))
        if not math.isfinite(timeout_) or not 0 <= timeout_ <= 86400:
            raise ValueError('图像等待超时时间必须为 0–86400 秒')
        mode_ = actions.parameter(p_, '等待类型', default='等待出现')
        if mode_ not in ('等待出现', '等待消失'):
            raise ValueError(f'未知图像等待类型：{mode_}')
        image_ = actions.resolve_image_path(p_, context)
        if not os.path.isfile(image_):
            raise FileNotFoundError(f'图像文件不存在：{image_}')
        p_['图像路径'] = image_
        wait_disappear_ = mode_ == '等待消失'
        deadline_ = time.monotonic() + timeout_ if timeout_ else None
        context.emit(f"正在等待指定图像{('消失' if wait_disappear_ else '出现')}…")
        while not context.stop_requested:
            wait_ = getattr(getattr(context, 'runtime', None), 'wait', None) or context.metadata.get('wait_interruptibly')
            if wait_ is not None and (not wait_(0, context)):
                return None
            found_ = actions.locate_image(p_, context) is not None
            if context.stop_requested:
                return None
            if found_ != wait_disappear_:
                context.emit('图像等待完成')
                return found_
            if deadline_ is not None and time.monotonic() >= deadline_:
                raise TimeoutError('图像等待超时')
            if wait_ is not None:
                if not wait_(0.1, context):
                    return None
            else:
                actions.wait_seconds(0.1)
        return None
