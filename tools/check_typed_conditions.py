"""Typed condition editor round trips and read-only predicate regressions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile
from unittest.mock import patch
from anclicker.domain.instructions import ExecutionContext, InstructionDraft
from anclicker.execution.flow_condition_checks import evaluate, validate_parameters, condition_summary
from anclicker.execution import typed_conditions
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.qt_compat.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
context = ExecutionContext(variables={'文本': '完成 123', '数字': 12.5, '日期': '2026-10-26',
    '列表': ['1', '甲', 2], '元素': '1', '空列表': []})

def p(kind, value, op, other='', **extra):
    return dict(判断类型=kind, 判断值=value, 比较方式=op, 比较值=other, **extra)

cases = [
    (p('文本', '{{文本}}', '包含', '完成'), True),
    (p('文本', ' ab ', '等于', 'ab'), False),
    (p('文本', '', '为空'), True),
    (p('文本', 'abc', '开头是', 'ab'), True),
    (p('数字', '{{数字}}', '大于', '12'), True),
    (p('数字', '10', '小于', '2'), False),
    (p('数字', '-1.50', '等于', '-1.5'), True),
    (p('日期', '{{日期}}', '早于', '2026/10/27'), True),
    (p('日期', '2026-10-26 12:00:00', '晚于', '2026-10-26'), True),
    (p('日期', '2026年10月26日', '等于', '2026-10-26'), True),
    (p('列表', '{{列表}}', '包含', '{{元素}}'), True),
    (p('列表', '{{列表}}', '包含', '1'), False),
    (p('列表', '{{列表}}', '包含', '"1"'), True),
    (p('列表', '{{列表}}', '长度等于', '3'), True),
    (p('列表', '{{空列表}}', '为空'), True),
    (p('列表', '[1, 2, 3]', '不包含', '4'), True),
]
with patch('anclicker.execution.flow_condition_checks.actions.wait_interruptibly', return_value=True):
    for params, expected in cases:
        validate_parameters(params)
        assert evaluate(context, params) == expected, params
        assert condition_summary(params)
    with tempfile.TemporaryDirectory() as folder:
        file = Path(folder) / 'example.txt'
        file.write_text('test', encoding='utf8')
        context.metadata['project_path'] = str(Path(folder) / 'project.db')
        assert evaluate(context, p('文件目录', 'example.txt', '是文件'))
        assert evaluate(context, p('文件目录', folder, '是目录'))
        assert not evaluate(context, p('文件目录', folder, '是文件'))
        assert evaluate(context, p('文件目录', 'missing', '不存在'))
    with patch.object(typed_conditions, 'window_titles', return_value=['记事本 - 测试', '设置']):
        assert evaluate(context, p('窗口存在', '记事本', '存在'))
        assert not evaluate(context, p('窗口存在', '记事本', '存在', 窗口匹配='精准'))
        assert evaluate(context, p('窗口存在', '设置', '存在', 窗口匹配='精准'))
        assert evaluate(context, p('窗口存在', 'missing', '不存在'))
    # Existing expression and coordinate conditions still run.
    assert evaluate(context, {'条件': '1 < 2'})
    assert evaluate(context, {'判断类型': '坐标存在', '坐标': '1,2'})

for params in [p('数字', 'NaN', '等于', '1'), p('数字', 'abc', '等于', '1'),
               p('日期', '2026-02-30', '早于', '2026-03-01'),
               p('列表', '{}', '为空'), p('列表', '[]', '长度等于', '-1'),
               p('文件目录', '', '存在'), p('窗口存在', '', '存在')]:
    try:
        validate_parameters(params)
    except ValueError:
        pass
    else:
        raise AssertionError(params)

# Every new type saves and reloads through the real condition editor.
for kind, operations in typed_conditions.OPERATIONS.items():
    value = {'文本':'  abc  ', '数字':'12', '日期':'2026-10-26',
             '列表':'[1, 2]', '文件目录':'example.txt', '窗口存在':'记事本'}[kind]
    for op in operations:
        other = '2026-10-27' if kind == '日期' else '2'
        params = p(kind, value, op, other)
        editor = get_instruction_spec('条件判断').create_editor(draft=InstructionDraft('条件判断', params))
        saved = editor.get_draft().parameters
        assert saved['判断类型'] == kind
        assert saved['比较方式'] == op
        assert saved['判断值'] == value
        assert editor.condition_panel.rows['比较值'].isHidden() == (op in typed_conditions.UNARY)
        assert editor.condition_edit.isHidden()
        editor.close()
        editor.deleteLater()
for kind, params in (
    ('表达式', {'条件': '1 < 2'}),
    ('图片存在', {'图像路径': '{{图片}}'}),
    ('图片文件存在', {'图像路径': '{{图片}}'}),
    ('OCR文字存在', {'目标文字': '完成'}),
    ('颜色判断', {'坐标': '1,2', '颜色': '#FFFFFF'}),
    ('坐标存在', {'坐标': '{{坐标}}'}),
):
    params['判断类型'] = kind
    editor = get_instruction_spec('条件判断').create_editor(draft=InstructionDraft('条件判断', params))
    assert editor.get_draft().parameters.get('判断类型', '表达式') == kind
    editor.close()
    editor.deleteLater()

for type_id in ('循环', '条件循环'):
    params = p('数字', '{{数字}}', '大于', '10')
    params['方式'] = '条件'
    editor = get_instruction_spec(type_id).create_editor(draft=InstructionDraft(type_id, params))
    assert editor.get_draft().parameters['判断类型'] == '数字'
    editor.close()
    editor.deleteLater()
print('PASS: six types, variable resolution, literal validation, typed comparisons, filesystem, mocked window matching, editor round trips and existing predicates')
