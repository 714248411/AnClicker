"""Source-grounding contracts for conversational requests; never invent screen context."""
import re
from models.chinese_planner import chinese_number
QUOTED=re.compile(r'“([^”]*)”|"([^"]*)"|「([^」]*)」|『([^』]*)』')
def quoted_values(text):return [next(v for v in match.groups() if v is not None) for match in QUOTED.finditer(text)]
NUMBER=r'[零一二三四五六七八九十百两\d.]+'
def intent_text(text):return QUOTED.sub('引用内容',text)
def duration(text):
    intent=intent_text(text)
    half=re.search(r'半(分钟|秒)',intent)
    if half and not re.search(NUMBER+r'\s*(分钟|秒)',intent):return {'时长':0.5,'单位':half[1]}
    matches=list(re.finditer('('+NUMBER+r')\s*(毫秒|秒|分钟)(?:钟)?',intent))
    if len(matches)==1 or (matches and re.search(r'哦不|不对|说错|改口|还是|改成|改为',intent)):
        m=matches[-1];return {'时长':chinese_number(m[1]),'单位':m[2]}
    return None
def no_enter(text):return bool(re.search(r'(?:不要|不用|无需|不需要|别|不)(?:再|先)?(?:按|敲)?(?:下)?回车|(?:不要|不用|别|不)(?:先|再)?提交',intent_text(text)))
def clarification(text,ast=None):
    intent=intent_text(text)
    if re.search(r'(?:那|这)(?:个|张)?(?:图|图片|图像)',intent) and re.search(r'找到|点击|点一下',intent) and not quoted_values(text):return '请提供要查找的图片文件路径或截图。'
    if re.search(r'(?:当前|这个|那个)窗口',intent) and re.search(r'关掉|关闭',intent):return '请提供要关闭的窗口标题，避免关闭错误的窗口。'
    for fragment in re.split(r'[，,；;。]|然后|接着|随后',intent):
        if re.search(r'那个|这个|右边|左边|上面|下面',fragment) and re.search(r'按钮|点击|点',fragment) and not re.search(r'CSS\s*#|坐标',fragment,re.I):
            return '请提供目标窗口和按钮文字、截图位置或网页元素定位。'
    if re.search(r'(?:把|将)?(?:那个|这个|它)(?:关掉|关闭|删除)',intent):return '请明确要关闭或删除的是哪个窗口、网页、文件或步骤。'
    if re.search(r'如果|否则|直到|循环|重复',intent):return '请明确条件或循环次数，并在流程图中确认分支。'
    if re.search(r'加载(?:好|完)|等.{0,12}(?:出现|完成|结束|好了)',intent) and not duration(text):return '需要等待哪个窗口或页面的什么状态？请提供可识别的文字或元素。'
    if re.search(r'发给|发送给|传给',intent):return '请明确要发送的内容、收件人和应用。'
    if re.search(r'那个|这个|右边|左边|上面|下面',intent) and not re.search(r'https?://|[A-Za-z]:[/\\]|CSS\s*#',text,re.I):
        if re.search(r'步骤|节点|流程',intent):return '请指出要修改的步骤编号。'
        if re.search(r'文件|目录|文件夹|图片|图像',intent):return '请提供要操作的文件或文件夹完整路径。'
        if re.search(r'按钮|点|点击',intent):return '请提供目标窗口和按钮文字、截图位置或网页元素定位。'
    if re.search(r'(?:打开|访问).*(?:网站|网页)',intent) and not re.search(r'https?://',text):return '请提供要打开的网址。'
    if re.search(r'(?:别|不要|不用|不必)(?:再|先)?(?:删除|去掉|删掉)',intent) and ast:return '已保留原步骤；请说明需要进行的其他修改。'
    return None

def constrain_schema(step,choices):
    intent=intent_text(step);value=duration(step)
    for choice in choices:
        properties=choice.get('properties',{});kind=properties.get('type_id',{}).get('const');params=properties.get('parameters',{})
        fields=params.get('properties',{})
        if kind=='打开网页':
            from models.web_contracts import URL
            urls=URL.findall(step)
            if len(urls)==1:
                fields['url']={'const':urls[0]};params['required']=list(dict.fromkeys(params.get('required',[])+['url']))
        if kind=='时间等待' and value:
            for k,v in value.items():fields[k]={'const':v}
        if kind=='快速文件操作':
            paths=[v for v in quoted_values(step) if re.match(r'^[A-Za-z]:[/\\]',v)]
            if re.search(r'复制|拷|备份',intent) and len(paths)==2:
                fields={k:v for k,v in fields.items() if k in ('操作','源路径','目标路径','覆盖') or k in intent};params['properties']=fields
                fields['操作']={'const':'复制'};fields['源路径']={'const':paths[0]};fields['目标路径']={'const':paths[1]}
                params['required']=list(dict.fromkeys(params.get('required',[])+['操作','源路径','目标路径']))
        if kind=='文本输入':
            from models.sentence_contracts import input_text_value
            literal=input_text_value(step)
            values=quoted_values(step)
            if literal is not None:fields['内容']={'const':literal}
            elif len(values)==1:fields['内容']={'const':values[0]}
    return choices

def normalize_edit(text):
    # Normalize numeric notation outside literals; retain wording and operation semantics.
    def part(value):
        value=re.sub(r'第?('+NUMBER+r')(?:个)?(?:流程)?步骤?',lambda m:'第'+str(int(chinese_number(m[1])))+'步',value)
        value=re.sub('('+NUMBER+r')\s*(毫秒|秒|分钟)',lambda m:str(chinese_number(m[1])).removesuffix('.0')+m[2],value)
        value=re.sub(r'(第[0-9]+步)(?:已经)?(?:不要了|不需要了|用不上了)(?:[，,]?(?:请)?(?:去掉|删掉)(?:吧)?)?',lambda m:'删除'+m[1],value)
        return value
    result=[];start=0
    for m in QUOTED.finditer(text):
        result.extend([part(text[start:m.start()]),m[0]]);start=m.end()
    result.append(part(text[start:]));return ''.join(result)

def boundary_contract(parts,cuts):
    from models.web_contracts import url_argument
    result=list(cuts)
    for i,part in enumerate(parts[1:]):
        intent=intent_text(part).strip()
        constraint=bool(re.match(r'^(?:哦不|不对|(?:刚)?说错|算了|还是|改成|改为|缩进|保留原顺序)',intent)) or no_enter(part) or bool(re.search(r'^(?:保留|留着).*?(?:原|源)|^(?:原|源).*(?:留着|保留|不要动)|^(?:别|不要).*(?:原件|原文件|源文件|覆盖)|^这(?:整)?句.*(?:文字|内容|字|照着写)',intent))
        # Standalone formatting and alignment clauses constrain the prior action.
        constraint = constraint or bool(re.fullmatch(r'(?:按|照)(?:列|行|字段|原顺序|顺序)(?:对应|匹配|填写|填入|来)?|(?:格式|编号|顺序|原文|标点|内容)(?:别改|不要改|保持不变|原样保留)|每(?:人|项|条|个)(?:一|1)(?:行|列)|(?:整句(?:话)?|原文)(?:照抄|原样保留)',intent))
        if url_argument(part) and re.search(r'打开|访问|进入',intent_text(parts[i])):result[i]=False
        elif re.match(r'^(?:其中|在其中|在里面|在网页中|在网页里|在页面中|在页面里)?(?:搜索|搜一下|搜)',intent):result[i]=True
        elif constraint:result[i]=False
        elif re.match(r'^(?:请|再|接着|最后|随后|先)*(?:按一下|按下|敲一下|点击|打开|等待|等(?=[零一二三四五六七八九十百两0-9]))',intent) and not re.search(r'哦不|不对|说错|改为|改成',intent_text(parts[i])):result[i]=True
    return result

def edit_requests(text):
    # Split only explicit new numbered edits, never references such as '之后插入'.
    masked=QUOTED.sub(lambda m:' '*(m.end()-m.start()),text)
    marks=list(re.finditer(r'(?:[，,；;]\s*(?:然后|接着|并且|并|再)?|然后|接着|并且|并|再)(?=(?:把|将|删除|去掉|删掉|修改)?第?[零一二三四五六七八九十百两0-9]+(?:个)?(?:流程)?步)',masked))
    result=[];start=0
    for m in marks:
        result.append(text[start:m.start()].strip(' ，,；;'));start=m.end()
    result.append(text[start:].strip(' ，,；;'))
    return [x for x in result if x]

def validate_model_output(value,schema):
    from anclicker.domain.agent_protocol import validate
    if 'oneOf' in schema:
        count=0
        for option in schema['oneOf']:
            try:validate_model_output(value,option);count+=1
            except (ValueError,TypeError):pass
        if count!=1:raise ValueError('模型输出不符合本次操作约束')
        return
    if 'const' in schema and value!=schema['const']:raise ValueError('模型改变了明确指定的值')
    validate(value,schema)
    if isinstance(value,str) and len(value)<schema.get('minLength',0):raise ValueError('模型返回空值')
    if isinstance(value,dict):
        if len(value)<schema.get('minProperties',0):raise ValueError('模型返回空补丁')
        for k,v in value.items():
            if k in schema.get('properties',{}):validate_model_output(v,schema['properties'][k])
    if isinstance(value,list):
        for v in value:validate_model_output(v,schema.get('items',{}))
