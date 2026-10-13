"""Typed methods extracted from the user's dm 7.2149 type library."""
import json
from pathlib import Path
METHODS = json.loads(Path(__file__).with_name('background_dm_methods.json').read_text(encoding='utf-8'))
GROUPS = tuple(dict.fromkeys(item['group'] for item in METHODS.values()))

def group_methods(group):
    return {name: data for name, data in METHODS.items() if data['group'] == group}

def label(name):
    text = METHODS[name]['label']
    return name if text == name else f'{text} · {name}'

def method_name(text):
    candidate = str(text).strip().rsplit(' · ', 1)[-1]
    return next((name for name in METHODS if name.casefold() == candidate.casefold()), candidate)

def values_for(name, values):
    definition = METHODS.get(name)
    if definition is None:
        raise ValueError('没有此后台接口')
    allowed = {item['name'] for item in definition['args'] if not item['out'] or item.get('inout')}
    if not isinstance(values, dict) or set(values) - allowed:
        raise ValueError('后台参数不匹配所选接口')
    result = []
    for item in definition['args']:
        value = values.get(item['name'], item['default'])
        if item['out'] and not item.get('inout'):
            value = 0
        elif value == '@窗口' or (isinstance(value, str) and ('{{' in value or '☾' in value)):
            pass
        elif item['type'] in (3, 20) or item.get('inout'):
            try:
                if isinstance(value, str):
                    value = int(value, 16 if value.strip().lower().startswith('0x') else 10)
                elif int(value) == value:
                    value = int(value)
                else:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError(item['label'] + '必须为整数') from None
            bits = 64 if item['type'] == 20 else 32
            if not -(2**(bits-1)) <= value < 2**(bits-1):
                raise ValueError(item['label'] + '超出数值范围')
        elif item['type'] in (4, 5):
            import math
            value = float(value)
            if not math.isfinite(value):
                raise ValueError(item['label'] + '必须为有限数值')
        else:
            value = str(value)
        if item['name'] == 'sim' and not isinstance(value, str):
            maximum = 100 if item['type'] == 3 else 1
            if not 0 <= value <= maximum:
                raise ValueError(f'相似度必须在 0 至 {maximum} 之间')
        result.append(value)
    return result
