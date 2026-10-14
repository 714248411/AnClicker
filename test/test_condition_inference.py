from types import SimpleNamespace
import pytest
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from instructions.流程.控制节点 import _condition_value
from flow_condition_context import condition_hint, replace_condition_variable
from test.test_control_priority import Graph
from test.test_background_presets import app


def test_neighbors_prefer_shared_variable_and_do_not_guess_ambiguity(tmp_path):
    g = Graph(tmp_path/'g.db')
    before = g.add('before', 变量='状态', 内容='{{其他}}')
    cond = g.add('condition', '条件判断', 条件='True')
    after = g.add('after', 内容='{{状态}}')
    g.link(before, cond)
    g.link(cond, after, 1)
    ident = next(i for i, name in g.names.items() if name == 'condition')
    assert condition_hint(g.repo.snapshot(), ident)['variable'] == '状态'
    g.repo.delete_connection(cond, after)
    g.repo.delete_commands([next(i for i, name in g.names.items() if name == 'after')], preserve_flow=False)
    hint = condition_hint(g.repo.snapshot(), ident)
    assert hint['variable'] == '' and set(hint['candidates']) == {'状态', '其他'}


def test_expression_replacement_preserves_operator():
    assert replace_condition_variable('old >= 10', '计数') == '计数 >= 10'


@pytest.mark.parametrize('type_id', ['条件判断', '循环', '条件循环'])
def test_new_editor_prefills_manual_edit_is_preserved_and_button_refreshes(app, type_id):
    context = ExecutionContext(metadata={'condition_hint': lambda: {'variable': '计数', 'candidates': ['计数']}})
    editor = get_instruction_spec(type_id).create_editor(context=context)
    try:
        assert editor.condition_edit.text() == '计数'
        editor.load_draft(InstructionDraft(type_id, {'条件': '自定 >= 10', '方式': '条件', '次数': 4}))
        editor._infer_condition(replace=False)
        assert editor.condition_edit.text() == '自定 >= 10'
        editor.infer_condition_button.click()
        assert editor.get_draft().parameters['条件'] == '计数 >= 10'
    finally:
        editor.deleteLater()


@pytest.mark.parametrize('expression,result', [('False and missing > 0', False), ('True or missing > 0', True),
                                               ('n > 2 and n < 5', True), ('n == 0 or n == 3', True)])
def test_condition_operator_precedence_and_short_circuit(expression, result):
    assert _condition_value(expression, {'n': 3}) is result


def test_compare_editor_infers_only_variable_and_preserves_manual_draft(app):
    context = ExecutionContext(metadata={'condition_hint': lambda: {'variable': '识别结果', 'candidates': ['识别结果']}})
    editor = get_instruction_spec('变量比较').create_editor(context=context)
    try:
        assert editor._controls['变量'].currentText() == '识别结果'
        editor.load_draft(InstructionDraft('变量比较', {'变量': '手动', '比较条件': '大于', '比较值': '10'}))
        editor._infer_condition(replace=False)
        assert editor._controls['变量'].currentText() == '手动'
        editor.infer_condition_button.click()
        draft = editor.get_draft()
        assert draft.parameters['变量'] == '识别结果'
        assert draft.parameters['比较条件'] == '大于' and draft.parameters['比较值'] == '10'
    finally:
        editor.deleteLater()


def test_inference_does_not_discard_complex_manual_condition():
    expression = 'a > 2 and b < 5'
    assert replace_condition_variable(expression, '计数') == expression
