"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'evaluate': ('from', 'anclicker.execution.flow_condition_checks', ('evaluate',), 0),
})


class _ControlExecutor(InstructionExecutorBase):
    TYPE_ID = ''

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'{self.TYPE_ID}执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        return result_ if delegated_ else True

class 循环Executor(_ControlExecutor):
    TYPE_ID = '循环'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        count_ = int(command.parameters.get('次数', 1))
        if str(command.parameters.get('方式', '次数')) == '条件':
            evaluate = _module_imports.load('evaluate')
            result_ = evaluate(context, command.parameters)
            context.metadata[f'flow_condition:{command.id}'] = result_
            context.emit(f"条件循环结果：{('是' if result_ else '否')}")
            return result_
        context.metadata[f'flow_loop_count:{command.id}'] = count_
        context.emit(f'循环节点：{count_} 次')
        return count_

class 条件判断Executor(_ControlExecutor):
    TYPE_ID = '条件判断'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        evaluate = _module_imports.load('evaluate')
        result_ = evaluate(context, command.parameters)
        context.metadata[f'flow_condition:{command.id}'] = result_
        context.emit(f"条件判断结果：{('是' if result_ else '否')}")
        return result_

class 条件循环Executor(条件判断Executor):
    TYPE_ID = '条件循环'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        result_ = super().execute_once(context, command)
        context.metadata[f'flow_loop_count:{command.id}'] = int(command.parameters.get('次数', 1))
        return result_
