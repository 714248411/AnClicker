"""Conservative condition-variable hints from actual adjacent commands."""
import ast
import keyword
import re

VARIABLE_KEYS = {'变量', '变量名', '结果变量', '保存变量', '目标变量', '输出变量'}


def identifier(value):
    value = str(value).strip().removeprefix('{{').removesuffix('}}').strip()
    return value if value.isidentifier() and not keyword.iskeyword(value) and value not in {'True', 'False', 'None'} else ''


def variables_in(command):
    names = []
    for key, value in command.parameters.items():
        if key in VARIABLE_KEYS:
            name = identifier(value)
            if name:
                names.append(name)
        if isinstance(value, str):
            names.extend(identifier(name) for name in re.findall(r'\{\{(.*?)\}\}', value))
            if key == '条件':
                try:
                    names.extend(node.id for node in ast.walk(ast.parse(value, mode='eval')) if isinstance(node, ast.Name))
                except (SyntaxError, ValueError):
                    pass
    return list(dict.fromkeys(name for name in names if identifier(name)))


def condition_hint(snapshot, command_id=None):
    commands = sorted(snapshot.commands, key=lambda command: command.order)
    by_id = {command.id: command for command in commands}
    by_node = {node.node_id: node.command_id for node in snapshot.nodes}
    current = next((node.node_id for node in snapshot.nodes if node.command_id == command_id), None)
    position = next((i for i, command in enumerate(commands) if command.id == command_id), len(commands))
    previous = [by_id[by_node[e.source]] for e in snapshot.edges if current and e.target == current
                and e.kind not in {5, 6, 7, 8} and by_node.get(e.source) in by_id]
    following = [by_id[by_node[e.target]] for e in snapshot.edges if current and e.source == current
                 and e.kind not in {5, 6} and by_node.get(e.target) in by_id]
    if not previous and position:
        previous = commands[position-1:position]
    if not following:
        following = commands[position+1:position+2]
    before = list(dict.fromkeys(name for command in previous for name in variables_in(command)))
    after = list(dict.fromkeys(name for command in following for name in variables_in(command)))
    shared = [name for name in before if name in after]
    candidates = shared or before or after
    selected = candidates[0] if len(candidates) == 1 else ''
    return {'variable': selected, 'candidates': list(dict.fromkeys(before + after)),
            'previous': [command.id for command in previous], 'following': [command.id for command in following]}


def replace_condition_variable(expression, variable):
    if not identifier(variable):
        raise ValueError('条件变量名称无效')
    try:
        tree = ast.parse(expression, mode='eval')
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        if len(names) > 1:
            return expression  # A manual multi-variable condition must not be discarded.
        if len(names) == 1:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    node.id = variable
            return ast.unparse(tree)
    except (SyntaxError, ValueError):
        pass
    return variable
