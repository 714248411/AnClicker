"""Persisted jump contracts shared by editors, graph validation and execution."""
from decimal import Decimal, InvalidOperation

ERROR_BIND = 5
ERROR_TARGET = 6
COMPARE_TRUE = 7
COMPARE_FALSE = 8
JUMP_KINDS = frozenset((5, 6, 7, 8))
JUMP_TYPES = frozenset(('报错跳转', '变量比较'))
TARGET_MODES = ('连线节点', '当前项目行', '其他项目行', '继续执行')
OPERATORS = ('等于', '不等于', '大于', '大于等于', '小于', '小于等于', '包含', '不包含')


def target_config(parameters, prefix=''):
    mode = str(parameters.get(prefix+'跳转方式', '连线节点'))
    if mode not in TARGET_MODES:
        raise ValueError('未知跳转方式：'+mode)
    raw_row = parameters.get(prefix+'目标行', 1)
    if isinstance(raw_row, bool):
        raise ValueError('目标行必须是从 1 开始的整数')
    try:
        row = int(raw_row)
    except (TypeError, ValueError):
        raise ValueError('目标行必须是从 1 开始的整数') from None
    if row < 1 or str(raw_row).strip() != str(row):
        raise ValueError('目标行必须是从 1 开始的整数')
    path = str(parameters.get(prefix+'项目路径', '')).strip()
    if mode == '其他项目行' and not path:
        raise ValueError('请选择目标项目文件')
    return mode, row, path


def compare_variables(parameters, variables):
    name = str(parameters.get('变量', '')).strip()
    if name not in variables:
        raise ValueError('比较变量不存在：'+name)
    left = variables[name]
    right = parameters.get('比较值', '')
    if parameters.get('比较对象', '固定值') == '变量':
        if str(right) not in variables:
            raise ValueError('右侧比较变量不存在：'+str(right))
        right = variables[str(right)]
    kind = parameters.get('比较类型', '自动')
    if kind not in ('自动', '数字', '文本'):
        raise ValueError('未知比较类型')
    if kind in ('自动', '数字'):
        try:
            numbers = (Decimal(str(left)), Decimal(str(right)))
            if not all(n.is_finite() for n in numbers):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            if kind == '数字':
                raise ValueError('数字比较的两侧必须为有限数字') from None
            left, right = str(left), str(right)
        else:
            left, right = numbers
    else:
        left, right = str(left), str(right)
    operator = parameters.get('比较条件', '等于')
    if operator == '等于': return left == right
    if operator == '不等于': return left != right
    if operator == '大于': return left > right
    if operator == '大于等于': return left >= right
    if operator == '小于': return left < right
    if operator == '小于等于': return left <= right
    if operator == '包含': return str(right) in str(left)
    if operator == '不包含': return str(right) not in str(left)
    raise ValueError('未知比较条件：'+str(operator))


def row_node(snapshot, row):
    commands = sorted(snapshot.commands, key=lambda command: command.order)
    if not 1 <= row <= len(commands):
        raise ValueError(f'目标行 {row} 超出项目范围（共 {len(commands)} 行）')
    command = commands[row-1]
    if command.type_id == '报错跳转':
        raise ValueError('不能把仅在异常时启用的报错模块作为行跳转目标')
    return next(node.node_id for node in snapshot.nodes if node.command_id == command.id)
