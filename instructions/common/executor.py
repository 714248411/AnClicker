"""执行器公共接口。"""

from __future__ import annotations

from instructions.base import InstructionExecutorInterface
from instructions.models import CommandRecord, ExecutionContext


class InstructionExecutorBase(InstructionExecutorInterface):
    """所有独立执行器的统一接口。"""

    def execute(self, context: ExecutionContext, command: CommandRecord):
        result_ = None
        for _ in range(command.repeat_count):
            result_ = self.execute_once(context, command)
            if context.stop_requested:
                break
        return result_

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        raise NotImplementedError
