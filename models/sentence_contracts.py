"""Keep action arguments across punctuation without changing quoted source text."""
import re
PREFIX=r'^(?:(?:请先|请|麻烦|劳驾|帮我|我想要|我想|我要|想要|接下来|接着|然后|随后|之后|最后|完了|先|再)\s*)+'
def clean_action(text):return re.sub(PREFIX,'',text.strip())

def starts_action(text):
    from models.conversational_contracts import intent_text
    t=clean_action(intent_text(text))
    # A located web operation is a new action; quoted text has already been masked.
    if re.match(r'在(?:当前)?(?:网页|页面)(?:上|里|中)?\s*(?:CSS|XPath)\b.*?(?:输入|填入|键入|写上|点击|获取|提取)',t,re.I):return True
    return bool(re.match(r'(?:打开|访问|进入|计算|读取|运行|查找|统计|截屏|截图|找到|匹配|切到|切换到|往上滚|往下滚|(?:把|将)(?:桌面|下载|文档)|在桌面|全选|粘贴|撤销|用键盘|按|敲|单击|双击|右键|左键|鼠标|向上滚|向下滚|等待|等|暂停|停留|输入|写上|填入|打上|键入|复制|拷贝|按一下|按下|敲一下|点击|点|搜索|搜一下|搜|(?:其中|在其中|在里面|在网页中|在网页里|在页面中|在页面里)(?:搜索|搜)|在搜索框.*输入)',t))

def grouped_boundaries(parts,cuts):
    from models.conversational_contracts import intent_text,quoted_values,duration
    from models.web_contracts import url_argument,URL
    result=list(cuts);group=parts[0]
    for i,part in enumerate(parts[1:]):
        previous=clean_action(intent_text(group)).strip(' ，,');current=clean_action(intent_text(part))
        attach=False
        if re.search(r'打开|访问|进入|^上',previous) and not URL.search(group) and url_argument(part):attach=True
        elif re.fullmatch(r'(?:等待|等|暂停|停留)(?:一下|一会儿|一会)?',previous) and duration(part) and not starts_action(part):attach=True
        elif re.fullmatch(r'(?:输入|写上|填入|打上|键入)(?:文字|文本|内容)?',previous) and not starts_action(part):attach=True
        elif re.fullmatch(r'(?:其中|在其中|在里面|在网页中|在网页里|在页面中|在页面里)?(?:搜索|搜一下|搜)',previous) and not starts_action(part):attach=True
        elif re.match(r'复制|拷贝',previous):
            paths=[x for x in quoted_values(group) if re.match(r'^[A-Za-z]:[/\\]',x)]
            if len(paths)<2 and (re.fullmatch(r'(?:到|复制到|放到|目标是)',current) or (quoted_values(part) and not starts_action(part))):attach=True
        if re.match(r'(?:输入|写上|填入|打上|键入)',previous) and not quoted_values(group) and not starts_action(part):attach=True
        if re.search(r'图片|图像',previous) and quoted_values(group) and re.fullmatch(r'(?:左键|右键)?(?:单击|双击)(?:左键|右键)?',current):attach=True
        if re.match(r'读取',previous) and re.fullmatch(r'(?:计算|统计)(?:行数|字数|字符数|长度)',current) and not quoted_values(part):attach=True
        if attach:result[i]=False
        elif starts_action(part) and not re.match(r'^(?:哦不|不对|改成|改为)',current):result[i]=True
        if result[i]:group=part
        else:group+='，'+part
    return result

def explicit_native_type(text):
    from models.conversational_contracts import intent_text,duration,quoted_values
    from models.web_contracts import URL
    t=clean_action(intent_text(text))
    if re.match(r'(?:等待|等|暂停|停留)',t) and duration(text):return '时间等待'
    if re.match(r'(?:打开|访问|进入|上)',t) and len(URL.findall(text))==1:return '打开网页'
    if input_text_value(text) is not None and not re.search(r'网页|CSS|搜索框|文件|编码',t,re.I):return '文本输入'
    if re.match(r'复制|拷贝',t) and len([x for x in quoted_values(text) if re.match(r'^[A-Za-z]:[/\\]',x)])==2:return '快速文件操作'
    return None


def payload_value(text):
    from models.conversational_contracts import QUOTED
    value=text.strip(' ，,:：')
    masked=QUOTED.sub(lambda m:' '*(m.end()-m.start()),value)
    corrections=list(re.finditer(r'[，,]\s*(?:改成|改为)',masked))
    if corrections:value=value[corrections[-1].end():].strip()
    value=re.sub(r'[，,]\s*(?:先)?(?:不要|不用|无需|不需要|别|不)(?:再|先)?(?:按|敲)?(?:下)?(?:回车|提交)[吧啊。！!]*$','',value).strip()
    quoted=QUOTED.fullmatch(value)
    if quoted:return next(v for v in quoted.groups() if v is not None)
    if QUOTED.search(value):return None
    return value or None

def input_text_value(text):
    t=clean_action(text)
    m=re.match(r'^(?:输入|写上|填入|打上|键入)(?:文本|文字|内容)?\s*[，,:：]?\s*(.+)$',t)
    if not m:return None
    from models.conversational_contracts import quoted_values
    values=quoted_values(t)
    result=payload_value(m[1])
    if result is not None:return result
    return values[0] if len(values)==1 else None
