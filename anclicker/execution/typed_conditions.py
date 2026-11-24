"""Read-only typed predicates for the visual condition editor."""
import ast
from datetime import datetime
from decimal import Decimal, InvalidOperation
import importlib
import json
import re
import sys
from pathlib import Path

OPERATIONS = {
    '文本': ('包含', '不包含', '等于', '不等于', '开头是', '结尾是', '为空', '不为空'),
    '数字': ('等于', '不等于', '大于', '大于等于', '小于', '小于等于'),
    '日期': ('等于', '不等于', '早于', '早于或等于', '晚于', '晚于或等于'),
    '列表': ('包含', '不包含', '为空', '不为空', '长度等于', '长度大于', '长度小于'),
    '文件目录': ('存在', '不存在', '是文件', '是目录'),
    '窗口存在': ('存在', '不存在'),
}
UNARY = {'为空', '不为空', '存在', '不存在', '是文件', '是目录'}


def resolve(context, value):
    if not isinstance(value, str):
        return value
    match = re.fullmatch(r'\s*(?:\{\{([^{}]+)\}\}|☾([^☽]+)☽)\s*', value)
    if match:
        name = (match[1] or match[2]).strip()
        if name not in context.variables:
            raise KeyError('判断变量不存在：' + name)
        return context.variables[name]
    from anclicker.execution.flow_condition_checks import substitute_target
    return substitute_target(context, value)


def number(value):
    try:
        if isinstance(value, bool):
            raise ValueError()
        result = Decimal(str(value).strip())
        if not result.is_finite():
            raise ValueError()
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('数字判断需要有效的有限数字：' + str(value)) from None


def date(value):
    if isinstance(value, datetime):
        return value
    try:
        text = str(value).strip().replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('日期格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS：' + str(value)) from None


def sequence(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                raise ValueError('列表请填写 [1, 2, 3]、["甲", "乙"] 或列表变量。') from None
    if not isinstance(value, (list, tuple)):
        raise ValueError('判断值必须是列表。')
    return value


def list_item(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def window_titles():
    backend = importlib.import_module('pygetwindow' if sys.platform == 'win32' else 'pywinctl')
    return [window.title for window in backend.getAllWindows()]


def validate(parameters):
    from anclicker.execution.flow_condition_checks import has_variable
    kind = parameters['判断类型']
    op = parameters.get('比较方式', OPERATIONS[kind][0])
    if op not in OPERATIONS[kind]:
        raise ValueError('请选择有效的比较方式')
    value = parameters.get('判断值', '')
    other = parameters.get('比较值', '')
    if kind == '窗口存在' and parameters.get('窗口匹配', '包含') not in ('包含', '精准'):
        raise ValueError('请选择有效的窗口标题匹配方式')
    for current in ([value] if op in UNARY else [value, other]):
        if has_variable(current):
            continue
        if kind == '数字':
            number(current)
        elif kind == '日期':
            date(current)
    if kind in ('文件目录', '窗口存在') and not str(value).strip():
        raise ValueError('请填写路径或窗口标题')
    if kind == '列表':
        if not has_variable(value):
            sequence(value)
        if op.startswith('长度') and not has_variable(other):
            length = number(other)
            if length < 0 or length != length.to_integral_value():
                raise ValueError('列表长度必须是非负整数')


def evaluate(context, parameters):
    kind = parameters['判断类型']
    op = parameters.get('比较方式', OPERATIONS[kind][0])
    value = resolve(context, parameters.get('判断值', ''))
    other = resolve(context, parameters.get('比较值', '')) if op not in UNARY else None
    if kind == '文本':
        value = '' if value is None else str(value)
        other = '' if other is None else str(other)
        return {'包含': lambda: other in value, '不包含': lambda: other not in value,
                '等于': lambda: value == other, '不等于': lambda: value != other,
                '开头是': lambda: value.startswith(other), '结尾是': lambda: value.endswith(other),
                '为空': lambda: not value, '不为空': lambda: bool(value)}[op]()
    if kind in ('数字', '日期'):
        convert = number if kind == '数字' else date
        left, right = convert(value), convert(other)
        try:
            return {'等于': lambda: left == right, '不等于': lambda: left != right,
                    '大于': lambda: left > right, '大于等于': lambda: left >= right,
                    '小于': lambda: left < right, '小于等于': lambda: left <= right,
                    '早于': lambda: left < right, '早于或等于': lambda: left <= right,
                    '晚于': lambda: left > right, '晚于或等于': lambda: left >= right}[op]()
        except TypeError:
            raise ValueError('两边日期需使用一致的时区格式。') from None
    if kind == '列表':
        items = sequence(value)
        if op in ('为空', '不为空'):
            return not items if op == '为空' else bool(items)
        if op in ('包含', '不包含'):
            raw = parameters.get('比较值', '')
            variable = isinstance(raw, str) and re.fullmatch(r'\s*(?:\{\{[^{}]+\}\}|☾[^☽]+☽)\s*', raw)
            found = (other if variable else list_item(other)) in items
            return found if op == '包含' else not found
        size = number(other)
        if size < 0 or size != size.to_integral_value():
            raise ValueError('列表长度必须是非负整数')
        return {'长度等于': lambda: len(items) == size, '长度大于': lambda: len(items) > size,
                '长度小于': lambda: len(items) < size}[op]()
    if kind == '文件目录':
        if value is None or not str(value).strip():
            raise ValueError('路径不能为空')
        path = Path(str(value)).expanduser()
        project = context.metadata.get('project_path')
        if not project:
            getter = getattr(context.metadata.get('database'), 'get_setting_value', None)
            project = getter('当前文件路径') if callable(getter) else None
        if not path.is_absolute() and project:
            base = Path(project)
            path = (base if base.is_dir() else base.parent) / path
        return {'存在': path.exists, '不存在': lambda: not path.exists(),
                '是文件': path.is_file, '是目录': path.is_dir}[op]()
    if value is None or not str(value).strip():
        raise ValueError('窗口标题不能为空')
    value = str(value)
    exact = parameters.get('窗口匹配', '包含') == '精准'
    found = any(title == value if exact else value in title for title in window_titles())
    return found if op == '存在' else not found
