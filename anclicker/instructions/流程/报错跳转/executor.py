"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '报错跳转'
    CONSUMED_FIELDS = ('跳转方式', '目标行', '项目路径')

    def execute_once(self, context, command):
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        raise ValueError('报错跳转不是普通指令；请从源指令右侧异常接口连接此模块。')
