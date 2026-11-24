"""Deterministic Chinese numbered-step boundaries and unambiguous primitives."""
import re

DIGITS=dict(zip('零一二三四五六七八九',range(10)));DIGITS['两']=2

def chinese_number(text):
    if re.fullmatch(r'\d+(?:\.\d+)?',text):return float(text)
    if not text or any(c not in DIGITS and c not in '十百' for c in text):raise ValueError('无法解析数字')
    total=0;value=0
    for c in text:
        if c in DIGITS:value=DIGITS[c]
        else:total+=(value or 1)*{'十':10,'百':100}[c];value=0
    return total+value

MARKER=re.compile(r'(?<![^\s；;])(?:第(?P<word>[一二三四五六七八九十百两\d]+)步\s*[:：、.]?|[（(](?P<bracket>[一二三四五六七八九十百两\d]+)[）)]|(?P<digit>\d{1,2})[.．、)）](?!\d)|(?P<han>[一二三四五六七八九十]+)、)\s*')

def split_numbered_steps(text):
    matches=list(MARKER.finditer(text))
    if not matches:return None
    # A bare numeric line is a list only if it has at least two markers;
    # explicit 第一步 remains useful as a single numbered request.
    if len(matches)==1 and not matches[0].group('word'):return None
    intro=text[:matches[0].start()].strip()
    if intro and not re.fullmatch(r'(?:请)?(?:按以下步骤|按下面步骤|执行以下步骤|执行下面步骤|分步骤|步骤如下|按顺序执行|请执行|请按顺序执行)[:：]?',intro):
        # Context introductions may contain values; preserve them for every step.
        if len(intro)>1000:raise ValueError('步骤前的说明过长，请缩短')
    if re.fullmatch(r'(?:请)?(?:按以下步骤|按下面步骤|执行以下步骤|执行下面步骤|分步骤|步骤如下|按顺序执行|请执行|请按顺序执行)[:：]?',intro):intro=''
    numbers=[int(chinese_number(next(v for v in m.groupdict().values() if v))) for m in matches]
    if numbers!=list(range(1,len(numbers)+1)):raise ValueError('步骤编号应从1开始连续递增，不能重复或缺号')
    if len(matches)>30:raise ValueError('每次最多30个编号步骤，请拆分任务')
    steps=[]
    for i,m in enumerate(matches):
        body=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip().rstrip('；;')
        if not body:raise ValueError('第'+str(i+1)+'步没有操作内容')
        steps.append(body)
    return intro,steps

def primitive_step(text):
    text=re.sub(r'^(?:请|然后|接着|再|最后|先)\s*','',text.strip()).rstrip('。！')
    match=re.fullmatch(r'(?:等待|等|停留|暂停)\s*([零一二三四五六七八九十百两\d.]+)\s*(毫秒|秒|分钟)(?:钟)?',text)
    if match:return {'type_id':'时间等待','parameters':{'时长':chinese_number(match[1]),'单位':match[2]}}
    if re.fullmatch(r'(?:按|按下)(?:一次)?(?:回车|回车键)',text):return {'type_id':'按下键盘','parameters':{'按键':'enter'}}
    return None

def resolve_previous_file(text,drafts):
    """Resolve only an explicit reference to the most recently opened file."""
    if not re.search(r'刚才打开的文件|刚刚打开的文件|上述打开的文件',text):return text
    for draft in reversed(drafts):
        p=draft.parameters
        source=p.get('源路径') if draft.type_id=='快速文件操作' and p.get('操作')=='打开' else p.get('文件路径') if draft.type_id=='运行外部文件' else None
        if source:return re.sub(r'刚才打开的文件|刚刚打开的文件|上述打开的文件',lambda _: '“'+source+'”',text)
    return text
