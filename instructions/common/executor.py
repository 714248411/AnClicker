"""执行器公共接口。"""

from __future__ import annotations

from instructions.base import InstructionExecutorInterface
from instructions.models import CommandRecord, ExecutionContext


class InstructionExecutorBase(InstructionExecutorInterface):
    """所有独立执行器的统一接口。"""

    def execute(self, context: ExecutionContext, command: CommandRecord):
        from background_runtime import input_context
        from execution_timing import context_timing, COMMAND_INTERVAL
        from instructions.common.actions import wait_interruptibly
        interval = context_timing(context)[COMMAND_INTERVAL]
        with input_context(context):
            result_ = None
            for _ in range(command.repeat_count):
                if context.stop_requested:
                    break
                if context.metadata.get('_timing_step_completed') and interval > 0:
                    if not wait_interruptibly(context, interval):
                        break
                context.metadata['_timing_step_completed'] = False
                try:
                    result_ = self.execute_once(context, command)
                finally:
                    context.metadata['_timing_step_completed'] = True
                if context.stop_requested:
                    break
            return result_

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        raise NotImplementedError
