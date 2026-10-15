"""Instruction execution implementation."""
from __future__ import annotations
from datetime import datetime
from anclicker.instructions.common import actions
import time
from datetime import timedelta
import random
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '时间等待'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'时间等待执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        type_ = str(actions.parameter(p_, '类型', default='时间等待'))
        if type_ == '随机等待':
            minimum_ = self._duration_seconds(actions.parameter(p_, '最小', default=1), str(actions.parameter(p_, '最小单位', default='秒')))
            maximum_ = self._duration_seconds(actions.parameter(p_, '最大', default=3), str(actions.parameter(p_, '最大单位', default='秒')))
            if minimum_ > maximum_:
                raise ValueError('随机等待最小值不能大于最大值')
            seconds_ = random.uniform(minimum_, maximum_)
        elif type_ == '定时等待':
            target_ = datetime.strptime(str(actions.parameter(p_, '时间', default='00:00:00')), '%H:%M:%S').time()
            now_ = datetime.now()
            target_dt_ = datetime.combine(now_.date(), target_)
            if target_dt_ <= now_:
                target_dt_ += timedelta(days=1)
            interval_ = self._duration_seconds(actions.parameter(p_, '检测频率', default=0.2), str(actions.parameter(p_, '检测频率单位', default='秒')))
            interval_ = max(0.01, interval_)
            context.emit(f'等待到目标时间：{target_dt_:%Y-%m-%d %H:%M:%S}')
            while not context.stop_requested:
                remaining_ = (target_dt_ - datetime.now()).total_seconds()
                if remaining_ <= 0:
                    break
                wait_ = getattr(getattr(context, 'runtime', None), 'wait', None) or context.metadata.get('wait_interruptibly')
                if wait_ is not None:
                    if not wait_(min(interval_, remaining_), context):
                        break
                elif not self._wait(min(interval_, remaining_), context):
                    break
            seconds_ = max(0.0, (target_dt_ - now_).total_seconds())
        elif type_ == '时间等待':
            seconds_ = self._duration_seconds(actions.parameter(p_, '时长', default=1), str(actions.parameter(p_, '单位', default='秒')))
        else:
            raise ValueError(f'未知等待类型：{type_}')
        if type_ != '定时等待':
            context.emit(f'开始等待：{seconds_:.3f}秒')
            wait_ = getattr(getattr(context, 'runtime', None), 'wait', None) or context.metadata.get('wait_interruptibly')
            if wait_ is not None:
                wait_(seconds_, context)
            else:
                self._wait(seconds_, context)
        if context.stop_requested:
            context.emit('时间等待已中止')
            return None
        context.emit(f'时间等待完成：{seconds_:.3f}秒，继续下一条')
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
    def _duration_seconds(value_, default_unit_: str='秒') -> float:
        unit_ = default_unit_
        number_ = value_
        if isinstance(value_, str) and '-' in value_:
            (number_text_, unit_text_) = value_.rsplit('-', maxsplit=1)
            (number_, unit_) = (number_text_, unit_text_)
        factor_ = {'毫秒': 0.001, '秒': 1.0, '分钟': 60.0}.get(str(unit_))
        if factor_ is None:
            raise ValueError(f'不支持的时间单位：{unit_}')
        return max(0.0, float(number_) * factor_)
