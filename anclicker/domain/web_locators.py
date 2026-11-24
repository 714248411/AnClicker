"""Validated, backwards-compatible anchor rules saved inside web commands."""
import json
import re

ANCHOR_RELATIONS = ('下方', '上方', '右侧', '左侧', '内部', '相邻', '同一行', '同一列', '最近')
LOCATOR_METHODS = ('智能匹配', 'CSS选择器', 'XPath', '文本内容')


def split_legacy_anchors(value):
    parts, token, quote, depth, escaped = [], '', '', 0, False
    for char in str(value or ''):
        if escaped:
            token += char; escaped = False; continue
        if char == '\\':
            token += char; escaped = True; continue
        if quote:
            token += char
            if char == quote: quote = ''
            continue
        if char in ('"', "'"):
            quote = char; token += char; continue
        if char in '[(': depth += 1
        if char in '])': depth -= 1
        if not depth and char in ';；\n':
            if token.strip(): parts.append(token.strip())
            token = ''
        else:
            token += char
    if token.strip(): parts.append(token.strip())
    return parts


def parse_anchor_config(value, relation='下方'):
    raw = str(value or '').strip()
    try:
        parsed = json.loads(raw) if raw.startswith('{') or re.match(r'^\[\s*(?:\{|"|\])',raw) else {'anchors': [
            {'selector': part, 'by': '智能匹配', 'relation': relation} for part in split_legacy_anchors(raw)]}
    except ValueError as error:
        raise ValueError('锚点配置不是有效的 JSON，请通过锚点向导重新设置') from error
    config = {'anchors': parsed} if isinstance(parsed, list) else dict(parsed)
    rules = config.get('anchors')
    if not isinstance(rules, list) or len(rules) > 20:
        raise ValueError('最多支持 20 个锚点')
    normalized = []
    for rule in rules:
        rule = {'selector':rule} if isinstance(rule,str) else dict(rule)
        selector = str(rule.get('selector','')).strip()
        by, direction = rule.get('by','智能匹配'), rule.get('relation',relation)
        if not selector or len(selector)>4096 or by not in LOCATOR_METHODS or direction not in ANCHOR_RELATIONS:
            raise ValueError('锚点内容、定位方式或相对方位无效')
        normalized.append({'selector':selector, 'by':by, 'relation':direction})
    target_by = config.get('targetBy','智能匹配')
    distance, index = config.get('maxDistance',800), config.get('matchIndex',0)
    if target_by not in LOCATOR_METHODS or isinstance(distance,bool) or isinstance(index,bool):
        raise ValueError('目标定位方式或匹配选项无效')
    if not isinstance(distance,(float,int)) or not 0<=distance<=100000 or not isinstance(index,int) or not 0<=index<=10000:
        raise ValueError('最大距离和匹配序号超出范围')
    return {'version':1, 'anchors':normalized, 'targetBy':target_by, 'maxDistance':distance, 'matchIndex':index}


def encode_anchor_config(config):
    value = json.dumps(config,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    parse_anchor_config(value)
    return value
