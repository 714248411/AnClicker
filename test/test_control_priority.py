"""Loops are atomic regions even when the ordinary continuation edge was added first."""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from graph_repository import GraphRepository
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from flow_control_runtime import execute_control_flow, loop_regions
from 数据库操作 import DatabaseOperation


class Graph:
    def __init__(self, path):
        self.db = DatabaseOperation(str(path))
        self.repo = GraphRepository(str(path))
        self.names = {}
    def add(self, name, kind='时间等待', **parameters):
        command = self.repo.add_command(InstructionDraft(kind, parameters), unconnected=True)
        self.names[command.id] = name
        return next(node.node_id for node in self.repo.snapshot().nodes if node.command_id == command.id)
    def link(self, source, target, kind=0):
        self.repo.connect_nodes(source, target, kind)
    def run(self, callback=None, start=None, single=False, unconnected=True):
        result = []
        context = ExecutionContext(variables={'n': 0})
        def execute(command, context):
            name = self.names[command.id]
            result.append(name)
            if callback:
                value = callback(name, context)
                if value is not None:
                    return value
            if command.type_id in {'循环', '条件循环', '条件判断', '变量比较'}:
                return get_instruction_spec(command.type_id).create_executor().execute(context, command)
            return True
        worker = SimpleNamespace(start_state=True, run_unconnected=unconnected,
                                 check_mutex=lambda: True, _execute_one=execute,
                                 _persist_variables=lambda values: None)
        worker.request_stop = lambda: setattr(worker, 'start_state', False)
        def fail(command, error):
            raise error
        worker._handle_command_error = fail
        execute_control_flow(worker, self.repo.execution_snapshot(), context, start, single)
        return result


@pytest.fixture
def graph(tmp_path):
    return Graph(tmp_path/'flow.db')


def return_loop(g, reverse=False, count=3):
    a = g.add('A')
    b = g.add('B')
    loop = g.add('L', '循环', 次数=count, 方式='次数')
    g.link('start', a)
    for target in ([loop, b] if reverse else [b, loop]):
        g.link(a, target)
    g.link(loop, a, 3)
    return a, b, loop


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('count', [1, 3, 7])
def test_screenshot_loop_finishes_before_ordinary_flow(graph, reverse, count):
    return_loop(graph, reverse, count)
    result = graph.run()
    assert [name for name in result if name != 'L'] == ['A']*count + ['B']


def test_multiple_body_commands_and_shared_completion_run_once(graph):
    a, b, loop = return_loop(graph)
    c = graph.add('C')
    graph.repo.delete_connection(a, loop)
    graph.link(a, c)
    graph.link(c, loop)
    graph.link(loop, b, 4)
    assert [n for n in graph.run() if n != 'L'] == ['A', 'C']*3 + ['B']


def test_nested_loops_complete_inner_before_outer_continuation(graph):
    outer = graph.add('outer', '循环', 次数=2)
    inner = graph.add('inner', '循环', 次数=3)
    body = graph.add('body')
    tail = graph.add('tail')
    after = graph.add('after')
    graph.link('start', outer)
    graph.link(outer, inner, 3)
    graph.link(outer, after, 4)
    graph.link(inner, body, 3)
    graph.link(inner, tail, 4)
    graph.link(body, inner)
    graph.link(tail, outer)
    assert [n for n in graph.run() if n not in {'outer', 'inner'}] == (['body']*3+['tail'])*2+['after']


@pytest.mark.parametrize('condition,expected', [('n < 2', 2), ('n < 6', 6), ('False', 0)])
def test_conditional_loop_uses_current_variable_and_not_count_mode_limit(graph, condition, expected):
    loop = graph.add('L', '条件循环', 次数=4, 条件=condition)
    body = graph.add('body')
    after = graph.add('after')
    graph.link('start', loop)
    graph.link(loop, body, 3)
    graph.link(loop, after, 4)
    graph.link(body, loop)
    def step(name, context):
        if name == 'body':
            context.variables['n'] += 1
    result = graph.run(step)
    assert result.count('body') == expected
    assert result[-1] == 'after'


def test_false_condition_does_not_run_connected_branch_as_unconnected(graph):
    loop = graph.add('L', '循环', 次数=2)
    cond = graph.add('condition', '条件判断', 条件='False')
    yes, no, after = [graph.add(name) for name in ('yes', 'no', 'after')]
    graph.link('start', loop)
    graph.link(loop, cond, 3)
    graph.link(loop, after, 4)
    graph.link(cond, yes, 1)
    graph.link(cond, no, 2)
    graph.link(yes, loop)
    graph.link(no, loop)
    assert [n for n in graph.run() if n not in {'L', 'condition'}] == ['no', 'no', 'after']


def test_comparison_return_to_loop_does_not_restart_counter(graph):
    loop = graph.add('L', '循环', 次数=3)
    compare = graph.add('compare', '变量比较', 变量='n', 比较值='0')
    after = graph.add('after')
    graph.link('start', loop)
    graph.link(loop, compare, 3)
    graph.link(loop, after, 4)
    graph.link(compare, loop, 7)
    graph.link(compare, after, 8)
    assert graph.run().count('compare') == 3
    assert graph.run()[-1] == 'after'


def test_stop_in_loop_never_executes_later_flow(graph):
    return_loop(graph, count=50)
    def stop(name, context):
        if name == 'A':
            context.stop_requested = True
    assert graph.run(stop) == ['A']


def test_single_row_does_not_start_entire_loop(graph):
    a, _, _ = return_loop(graph)
    assert graph.run(start=a, single=True) == ['A']


def test_run_from_body_finishes_loop_and_then_flow(graph):
    a, _, _ = return_loop(graph)
    assert [n for n in graph.run(start=a) if n != 'L'] == ['A']*3 + ['B']


def test_disconnected_loop_respects_run_unconnected_toggle(graph):
    a, _, _ = return_loop(graph)
    graph.repo.delete_connection('start', a)
    assert graph.run(unconnected=False) == []
    assert [n for n in graph.run() if n != 'L'] == ['A']*3 + ['B']


def test_error_return_to_loop_keeps_iteration_budget(graph):
    loop = graph.add('L', '循环', 次数=3)
    body = graph.add('body')
    after = graph.add('after')
    handler = graph.add('error', '报错跳转')
    graph.link('start', loop)
    graph.link(loop, body, 3)
    graph.link(loop, after, 4)
    graph.link(body, loop)
    graph.link(body, handler, 5)
    graph.link(handler, loop, 6)
    def fail(name, context):
        if name == 'body':
            raise RuntimeError('fixture failure')
    result = graph.run(fail)
    assert result.count('body') == 3 and result[-1] == 'after'


def test_nested_implicit_completion_is_in_outer_loop(graph):
    a, b, inner = return_loop(graph, count=3)
    outer = graph.add('outer', '循环', 次数=2)
    after = graph.add('after')
    graph.repo.delete_connection('start', a)
    graph.link('start', outer)
    graph.link(outer, inner, 3)
    graph.link(outer, after, 4)
    graph.link(b, outer)
    assert [n for n in graph.run() if n not in {'L', 'outer'}] == (['A']*3+['B'])*2+['after']
