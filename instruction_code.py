"""Read editable instruction text as data; never execute user code."""
import ast
import io
import re
import tokenize
from copy import deepcopy
from instructions.models import InstructionDraft
from instructions.registry import iter_instruction_specs


def _literal(node):
    # Generated parameter objects use JSON booleans and null.
    class JsonNames(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in ('true', 'false', 'null'):
                return ast.copy_location(ast.Constant({'true': True, 'false': False, 'null': None}[node.id]), node)
            return node
    return ast.literal_eval(JsonNames().visit(node))


def parse_instruction_code(text):
    specs = sorted(iter_instruction_specs(), key=lambda s: len(s.type_id), reverse=True)
    entries, pending_id, seen = [], None, set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#'):
            marker = re.match(r'# \[\d+\] #(\d+) ', line)
            if marker:
                pending_id = int(marker[1])
            continue
        try:
            spec = next((s for s in specs if line == s.type_id or line.startswith(s.type_id + '(')), None)
            if spec is None:
                raise ValueError('无法识别指令名称，请从左侧或输入提示中选择')
            suffix = line[len(spec.type_id):] or '()'
            call = ast.parse('command' + suffix, mode='eval').body
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != 'command':
                raise ValueError('只能填写指令和参数')
            if len(call.args) > 1:
                raise ValueError('参数应放在一个 {} 对象内')
            supplied = _literal(call.args[0]) if call.args else {}
            if not isinstance(supplied, dict):
                raise ValueError('指令参数必须是 {} 对象')
            params = deepcopy({f.key: f.default for f in spec.load_editor_class().FIELDS})
            params.update(supplied)
            options = {}
            for keyword in call.keywords:
                if keyword.arg not in ('重复次数', '异常处理', '备注') or keyword.arg in options:
                    raise ValueError('不支持或重复的选项：' + str(keyword.arg))
                options[keyword.arg] = _literal(keyword.value)
            repeat = options.get('重复次数', 1)
            if type(repeat) is not int or repeat < 1:
                raise ValueError('重复次数必须是正整数')
            policy = options.get('异常处理', '提示异常并暂停')
            if not isinstance(policy, str):
                raise ValueError('异常处理必须是文字')
            comments = [t.string[1:].strip() for t in tokenize.generate_tokens(io.StringIO('command' + suffix).readline) if t.type == tokenize.COMMENT]
            note = options.get('备注', comments[0] if comments else '')
            if not isinstance(note, str):
                raise ValueError('备注必须是文字')
            if pending_id is not None and pending_id in seen:
                raise ValueError('指令编号重复，请删除复制指令上方的编号注释')
            seen.add(pending_id)
            entries.append((pending_id, InstructionDraft(spec.type_id, params, repeat, policy, note)))
            pending_id = None
        except Exception as error:
            raise ValueError(f'第 {number} 行：{error}') from error
    if not entries:
        raise ValueError('没有可写入的指令，请先输入或选择指令。')
    return entries


from dataclasses import dataclass, field
import json


@dataclass
class ConversionPlan:
    entries: list = field(default_factory=list)
    notices: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def _complete_delimiters(text):
    """Finish an unfinished literal, retaining every character already entered."""
    stack, quote, escaped, comment = [], None, False, False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == '#':
            comment = True
            break
        elif char in '({[':
            stack.append({'(': ')', '{': '}', '[': ']'}[char])
        elif char in ')}]':
            if not stack or stack.pop() != char:
                raise ValueError('括号不匹配，请先修改')
    position = index if comment else len(text)
    prefix, tail = text[:position], text[position:]
    if quote:
        if escaped:
            raise ValueError('字符串末尾的转义符尚未完成，请先补充文字')
        prefix += quote
    return prefix + ''.join(reversed(stack)) + (' ' if tail else '') + tail


def prepare_instruction_conversion(text):
    plan = ConversionPlan()
    specs = sorted(iter_instruction_specs(), key=lambda s: len(s.type_id), reverse=True)
    repaired_lines = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            repaired_lines.append(raw)
            continue
        indent = len(raw) - len(raw.lstrip())
        spec = next((s for s in specs if line == s.type_id or line.startswith(s.type_id + '(') or line.startswith(s.type_id + ' (')), None)
        if spec is None:
            plan.errors.append(f'第 {number} 行，第 {indent} 个字符后：需要填写有效的指令名称。')
            repaired_lines.append(raw)
            continue
        kind = spec.type_id
        suffix = line[len(kind):].strip()
        try:
            completed = _complete_delimiters(suffix or '()')
            # Omitted values are represented by None until field defaults are applied.
            completed = _fill_missing_values(completed)
            expression = ast.parse('command' + completed, mode='eval').body
            if not isinstance(expression, ast.Call) or len(expression.args) > 1:
                raise ValueError('参数应放在一个 {} 对象内')
            supplied = _literal(expression.args[0]) if expression.args else {}
            if not isinstance(supplied, dict):
                raise ValueError('参数应是 {} 对象')
            fields = spec.load_editor_class().FIELDS
            filled = []
            for setting in fields:
                if setting.key not in supplied or (supplied[setting.key] is None and setting.default is not None):
                    supplied[setting.key] = deepcopy(setting.default)
                    filled.append(setting.key + '=' + json.dumps(setting.default, ensure_ascii=False))
            pending = []
            for setting in fields:
                value = supplied.get(setting.key)
                invalid = False
                if setting.kind == 'choice' and setting.choices and value not in setting.choices:
                    invalid = True
                elif setting.kind in ('int', 'float'):
                    invalid = (type(value) not in (int, float) or not setting.minimum <= value <= setting.maximum)
                if invalid:
                    supplied[setting.key] = deepcopy(setting.default)
                    filled.append(setting.key + '=' + json.dumps(setting.default, ensure_ascii=False))
                if setting.required and not str(supplied.get(setting.key) or '').strip():
                    pending.append(setting.label)
            # RPA fields predate the native required flag.
            for key in ('selector', 'xpath'):
                if key in supplied and not str(supplied[key] or '').strip():
                    pending.append('网页元素 ' + key)
            if kind == '打开网页':
                from web_urls import normalize_web_url
                try:
                    supplied['url'] = normalize_web_url(supplied.get('url'))
                except ValueError:
                    pending.append('网页地址')
            if kind == '打开Excel' and not str(supplied.get('path') or '').strip():
                pending.append('Excel 文件路径')
            if kind == '时间等待' and supplied.get('类型') == '定时等待' and not supplied.get('时间'):
                supplied['类型'] = '时间等待'
                filled.append('类型="时间等待"（未填写定时时间）')
            supplied.pop('_待补充参数', None)
            if pending:
                supplied['_待补充参数'] = list(dict.fromkeys(pending))
                plan.notices.append(f'第 {number} 行，第 {len(raw)} 个字符后：需要补充' + '、'.join(pending) + '。无法推断实际目标，将保留指令并标记待补充，运行时跳过；在表格补齐并保存后恢复执行。')
            options = []
            for kw in expression.keywords:
                value = _literal(kw.value)
                if kw.arg == '重复次数' and (value is None or type(value) is not int or value < 1):
                    value = 1
                    filled.append('重复次数=1')
                elif kw.arg == '异常处理' and not value:
                    value = '提示异常并暂停'
                    filled.append('异常处理="提示异常并暂停"')
                options.append((kw.arg, value))
            present = {key for key, _ in options}
            if '重复次数' not in present:
                filled.append('重复次数=1')
            if '异常处理' not in present:
                filled.append('异常处理="提示异常并暂停"')
            notes = [t.string for t in tokenize.generate_tokens(io.StringIO('command' + completed).readline) if t.type == tokenize.COMMENT]
            repaired = kind + '(' + json.dumps(supplied, ensure_ascii=False)
            for key, value in options:
                if key not in ('重复次数', '异常处理', '备注'):
                    raise ValueError('不支持的选项：' + str(key))
                repaired += ', ' + key + '=' + repr(value)
            repaired += ')' + ('  ' + notes[0] if notes else '')
            # Validate the repaired command before offering a conversion.
            parse_instruction_code(repaired)
            if completed != suffix:
                plan.notices.append(f'第 {number} 行，第 {len(raw)} 个字符后：需要补充未完成的参数、引号或括号。')
            if filled:
                brace = raw.find('{')
                position = brace + 1 if brace >= 0 else len(raw)
                plan.notices.append(f'第 {number} 行，第 {position} 个字符后：需要补充参数；继续转换将填写：' + '，'.join(filled))
            repaired_lines.append(repaired)
        except Exception as error:
            offset = getattr(error, 'offset', None)
            position = min(len(raw), max(indent + len(kind), indent + len(kind) + (offset or len(suffix)) - 8))
            plan.errors.append(f'第 {number} 行，第 {position} 个字符后：需要补充或修改参数（{error}）。')
            repaired_lines.append(raw)
    if not plan.errors:
        try:
            plan.entries = parse_instruction_code('\n'.join(repaired_lines))
        except ValueError as error:
            plan.errors.append(str(error))
    return plan


def _fill_missing_values(text):
    result, quote, escaped = [], None, False
    for index, char in enumerate(text):
        result.append(char)
        if quote:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == '#':
            result.append(text[index + 1:])
            break
        elif char in ':=' and text[index + 1:].lstrip().startswith((',', '}', ')')):
            result.append(' None')
    return ''.join(result)
