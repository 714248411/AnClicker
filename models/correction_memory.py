"""Reviewed failure memories. Raw failed commands are never executable memories."""
import json,re
from pathlib import Path
from models.conversational_contracts import intent_text
FAMILY_TYPES={'clipboard_read':{'获取剪切板'},'escape':{'按下键盘'},'scroll':{'滚轮滑动'},'web_input':{'输入文本'},'page_capture':{'网页截图'},'sheet_save':{'保存Excel'}}
FAMILIES=set(FAMILY_TYPES)
def cases():
    try:data=json.loads(Path(__file__).with_name('correction_cases.json').read_text(encoding='utf8'))
    except (OSError,ValueError):return []
    if not isinstance(data,list) or len(data)>200:return []
    data=[x for x in data if isinstance(x,dict)]
    from anclicker.domain.agent_protocol import catalog
    known={x['type_id'] for x in catalog()}
    return [x for x in data if x.get('status')=='reviewed' and isinstance(x.get('family'),str) and x['family'] in FAMILIES and isinstance(x.get('expected'),list) and x['expected'] and all(isinstance(n,str) for n in x['expected']) and set(x['expected'])<=known & FAMILY_TYPES[x['family']] and all(isinstance(x.get(k),str) and len(x[k])<400 for k in ('id','query','guidance'))]
def family(text):
    t=intent_text(text)
    from models.web_contracts import page_scroll_parameters
    if page_scroll_parameters(text):return None
    # Quoted payloads are masked. A typed sentence or a negated operation is not an action.
    if re.search(r'不要|别|不必|无需|不用|不准|不许',t):return None
    if re.match(r'^(?:请|帮我|给我)?(?:输入|打字|键入|写上|敲几个字)',t):return None
    if re.search(r'剪[贴切]板',t) and re.search(r'读|读取|取出|看看|查看|给我|拿出来',t) and not re.search(r'写入|放入|放进|复制到|清空|覆盖|粘贴',t):return 'clipboard_read'
    if re.search(r'(?:按|敲)(?:一下|下|个)?\s*(?:escape(?![a-z])|esc(?![a-z])|退出键)',t,re.I):return 'escape'
    if re.search(r'(?:往|向|朝)[上下]|底下|底部|顶部',t) and re.search(r'滚|翻|滑|挪',t) and not re.search(r'文件|单元格|表格|图片|图像|鼠标拖',t):return 'scroll'
    if not re.search(r'表格|这张表|那张表|表里|工作簿|Excel',t,re.I) and re.search(r'网页|页面',t) and re.search(r'框|搜索栏',t) and re.search(r'填|输入|写进|写入|敲',t):return 'web_input'
    if re.search(r'这一页|网页|页面',t) and re.search(r'留.*图|存.*图片|截.*图|图片备份',t):return 'page_capture'
    if re.search(r'表格|表里|这张表|工作簿|Excel',t,re.I) and re.search(r'保存|存起来|存上|存一下|存好',t) and not re.search(r'另存|网页|图片|复制|新文件',t):return 'sheet_save'
    return None

def guidance(text,names):
    matched=family(text)
    return [x for x in cases() if x['family']==matched and set(x['expected'])&set(names)][:2]

def binding(text):
    matched=family(text);t=intent_text(text)
    if matched=='escape':return '按下键盘',{'按键':'esc'}
    if matched=='scroll':
        from models.chinese_planner import chinese_number
        direction='向上' if re.search(r'(?:往|向|朝)上|顶部',t) else '向下'
        amount=re.search(r'([零一二三四五六七八九十百两0-9]+)\s*(?:格|次)',t)
        count=int(chinese_number(amount[1])) if amount else 1
        if not 1<=count<=100:return None
        return '滚轮滑动',{'类型':'滚轮滑动','方向':direction,'距离':count}
    return None
