"""执行器公共接口。"""

from __future__ import annotations

from anclicker.domain.instruction_interfaces import InstructionExecutorInterface
from anclicker.domain.instructions import CommandRecord, ExecutionContext

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'input_context': ('from', 'anclicker.platform.background_runtime', ('input_context',), 0),
    'context_timing_COMMAND_INTERVAL': ('from', 'anclicker.execution.execution_timing', ('context_timing', 'COMMAND_INTERVAL'), 0),
    'wait_interruptibly': ('from', 'anclicker.execution.actions', ('wait_interruptibly',), 0),
})



class InstructionExecutorBase(InstructionExecutorInterface):
    """所有独立执行器的统一接口。"""

    def execute(self, context: ExecutionContext, command: CommandRecord):
        input_context = _module_imports.load('input_context')
        context_timing, COMMAND_INTERVAL = _module_imports.load('context_timing_COMMAND_INTERVAL')
        wait_interruptibly = _module_imports.load('wait_interruptibly')
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
