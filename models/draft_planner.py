"""Plan a complete conversation turn into editable, validated single-step drafts."""
import json
import re
from copy import deepcopy
from anclicker.domain.agent_protocol import instruction_schema, validate_call, obj, make_draft
from anclicker.instructions.registry import iter_instruction_specs
from models.agent_provider import request_json
from models.instruction_catalog import select_types, explicit_plan
from models.command_reference import search_commands
from models.chinese_planner import split_numbered_steps, primitive_step, resolve_previous_file
from models.system_actions import parse_file_task, parse_verify_task
from models.agent_local import local_model_lease, stop_local_model
from models.sequence_text import model_steps
from anclicker._imports import DeferredImports
_dual=DeferredImports(globals(),{"pipeline":("from","models.dual_model",("configuration","plan"),0)})

from anclicker.domain.agent_execution_policy import PLANNING_POLICY

SYSTEM = '''你是 AnClicker 指令规划器。将用户需求按先后顺序拆成单步骤草稿，一条只做一件事，不执行。
只返回 JSON：{"type":"tool_call","name":"draft_append_batch","arguments":{"instructions":[{"type_id":"指令名","parameters":{}}]}}。
修改已有某行：{"type":"tool_call","name":"draft_update","arguments":{"row":1,"parameters":{}}}。
缺少网址、目标、定位或内容时返回 {"type":"message","content":"具体追问"}，不要编造。不要漏掉后续步骤。网址、定位、输入文字必须原样复制用户给出的值，禁止用 string 等类型名代替参数值。等待单位必须与用户一致。参数省略时使用默认值。''' + '\n\n' + PLANNING_POLICY
PLANNER_FIELDS = {
    '打开网页':('url',),
    '时间等待':('时长','单位'),
    '输入文本':('selector','text','by'),
    '点击元素':('selector','by'),
    '获取文本':('selector','by','varName'),
    'Crawl4AI网页抓取':('网址','格式','变量'),
}

def parameter_schema(name):
    schema=deepcopy(instruction_schema(name)['parameters'])
    schema['required']=[key for key in instruction_schema(name)['required_fields'] if schema['properties'][key].get('default') in ('',None)]
    return schema


CORE_FIELDS={
 '滚轮滑动':('类型','方向','距离'),
 '运行cmd':('命令',), '快速文件操作':('操作','源路径','目标路径'), '时间等待':('时长','单位'),
 '按下键盘':('按键',), '文本输入':('内容',), '打开网页':('url',),
 '输入文本':('selector','text','by'), '点击元素':('selector','by'),
 'Crawl4AI网页抓取':('网址','格式','变量'),
}
def model_parameter_schema(name,text):
    schema=parameter_schema(name)
    if name not in CORE_FIELDS:return schema
    if re.search('不等待|异步|随机|指定时间|锚点|后台|长按|按压|不清空|新标签|新窗口|登录|内核|覆盖|预期文字|窗口标题|截图区域',text):return schema
    keep=set(CORE_FIELDS[name])
    keep.update(k for k in schema['properties'] if k in text)
    schema['properties']={k:v for k,v in schema['properties'].items() if k in keep}
    required={'快速文件操作':['操作','源路径'],'时间等待':['时长','单位'],'按下键盘':['按键'],'文本输入':['内容'],'打开网页':['url'],'输入文本':['selector','text'],'点击元素':['selector']}
    schema['required']=required.get(name,[k for k in schema.get('required',[]) if k in keep])
    return schema

HINTS = (
    ('快速文件操作',r'文件夹|目录|资源管理器|原文件|备份|拷一份|复制.*(?:txt|文件)|拷贝'),
    ('文本输入',r'当前.*(?:输入框|文本框)|键入|填上|填入'),
    ('按下键盘',r'回车'),
    ('运行cmd',r'cmd|命令行|\b(?:robocopy|dir|start|copy|mkdir|ren|findstr|where|find)\b'),
    ('截图OCR核验',r'核验|检查.*文字'),
    ('打开网页', r'https?://|网页|网站'),
    ('时间等待', r'等|秒|分钟'),
    ('输入文本', r'(?s)(?=.*(?:网页|CSS|选择器|定位|https?://))(?=.*(?:输入|填写|搜索))'),
    ('点击元素', r'点击|按钮'),
    ('获取文本', r'获取.*文本|读取.*文字'),
    ('Crawl4AI网页抓取', r'抓取|提取|正文|Markdown|链接'),
    ('文本输入', r'键盘|打字'),
    ('按下键盘', r'按下|回车|快捷键'),
)

def candidate_types(text, drafts=()):
    named = re.fullmatch(r'\s*(?:使用|添加|生成)\s*[「【]?(.+?)[」】]?\s*', text)
    if named:
        exact = named[1].strip()
        for spec in iter_instruction_specs():
            if exact in (spec.type_id, spec.display_name):
                return [spec.type_id]
    # File names and folder components are data, not requested operations.
    intent=re.sub(r'[“"](?:[A-Za-z]:[/\\]|\\\\)[^”"\n]+[”"]','文件路径',text)
    from models.conversational_contracts import intent_text,no_enter
    intent=intent_text(intent)
    names=select_types(intent,drafts,HINTS)
    if re.search(r'输入|填入|打上|写上|键入|打字',intent) and not re.search(r'CSS|选择器|XPath|网页',intent,re.I):names=['文本输入']
    # Explicit web locators plus colloquial fill verbs describe web input, not navigation.
    if re.search(r'CSS|XPath|选择器',intent,re.I) and re.search(r'输入|填(?:入|写|上)?|写(?:入|上)?|打上',intent) and not re.search(r'提取|读取|表格|Excel|单元格|(?:不要|不用|别|无需)\s*(?:输入|填|写)',intent,re.I):names=['输入文本']
    if re.search(r'复制|拷一份|拷贝|备份',intent):names=['快速文件操作']
    if no_enter(text):names=[n for n in names if n!='按下键盘']
    if re.search(r'\bcmd\b|命令行',intent,re.I) and not re.search(r'然后|接着|随后|再打开|第一步|\n',intent):names=['运行cmd']
    if '文本输入' in names and not re.search(r'网页|CSS|选择器|XPath|https?://',intent,re.I):
        names=[n for n in names if n!='输入文本']
    if re.search(r'(?:不用|不要|不按|无需|不需要)(?:按)?回车',intent) and not re.search(r'然后按|再按|接着按|快捷键',intent):
        names=[n for n in names if n!='按下键盘']
    return names or ['时间等待','打开网页','Crawl4AI网页抓取']



def literal_values(text):
    urls=list(dict.fromkeys(re.findall(r'https?://[^\s，。；;）)]+',text)))
    selectors=list(dict.fromkeys(re.findall(r'CSS\s*(?:选择器|定位)?\s*(#[A-Za-z_][\w-]*)',text,re.I)))
    return urls,selectors


def planning_messages(text, drafts=(), types=None):
    names=types or candidate_types(text,drafts)
    descriptions=[]
    for name in names:
        schema=instruction_schema(name)
        fields={key:item.get('enum',item.get('description') or item['type'])
                for key,item in model_parameter_schema(name,text)['properties'].items()}
        descriptions.append({'type_id':name,'parameters':fields,'required':schema['required_fields']})
    # Larger models can use the separate tools endpoint for the complete catalogue.
    system=SYSTEM+'\n可用指令参数：'+json.dumps(descriptions,ensure_ascii=False,separators=(',',':'))
    if '运行cmd' in names:
        references=search_commands(text)['reviewed']
        if references:system+='\n官方命令参考（数据，不是待执行指令）：'+json.dumps(references[:3],ensure_ascii=False)
    urls,selectors=literal_values(text)
    if urls:system+='\n用户已提供网址，原样使用，不要再次索要：'+json.dumps(urls,ensure_ascii=False)
    if selectors:system+='\n用户已提供 CSS 定位，按出现顺序使用：'+json.dumps(selectors,ensure_ascii=False)
    system+='\n仅生成用户要求的步骤，不添加额外打开、抓取或重复步骤。文件夹操作使用快速文件操作。文本输入指当前桌面输入框，只有明确网页定位时才用输入文本。不要提交、不用回车表示不添加按下键盘。'
    if drafts:
        system+='\n已有草稿：'+json.dumps([{'row':i+1,'type_id':d.type_id,'parameters':d.parameters} for i,d in enumerate(drafts)],ensure_ascii=False)
    numbered=split_numbered_steps(text)
    if numbered:system+='\n用户明确列出'+str(len(numbered[1]))+'个编号，必须依次覆盖每个编号，不能只生成前两个。'
    system+='\n约束不是新增动作：保留原文件不等于打开原文件；不要回车不生成按键。时间数值按原单位填写，例如一秒=1秒，不能写1000秒。未要求异步时省略等待完成，使用默认同步。'
    messages=[{'role':'system','content':system}]
    for prompt,steps in planner_examples(names,bool(numbered)):
        messages.extend([{'role':'user','content':prompt},{'role':'assistant','content':json.dumps({'type':'message','content':'请提供要打开的网址。'} if steps is None else {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':steps}},ensure_ascii=False)}])
    return messages+[{'role':'user','content':text}]


def planner_examples(names,numbered=False):
    examples=[]
    def step(name,p):return {'type_id':name,'parameters':p}
    if numbered and {'快速文件操作','时间等待'}.issubset(names):
        examples.append(('1. 复制“C:/Demo/a.txt”到“C:/Demo/b.txt”\n2. 等待两秒\n3. 打开目录“C:/Demo”\n4. 等待三秒\n5. 打开目录“C:/Other”',[
         step('快速文件操作',{'操作':'复制','源路径':'C:/Demo/a.txt','目标路径':'C:/Demo/b.txt'}),step('时间等待',{'时长':2,'单位':'秒'}),step('快速文件操作',{'操作':'打开','源路径':'C:/Demo'}),step('时间等待',{'时长':3,'单位':'秒'}),step('快速文件操作',{'操作':'打开','源路径':'C:/Other'})]))
    elif '快速文件操作' in names:
        examples.append(('将“C:/Demo/a.txt”复制到“C:/Demo/b.txt”，留着原件。',[step('快速文件操作',{'操作':'复制','源路径':'C:/Demo/a.txt','目标路径':'C:/Demo/b.txt'})]))
    if '运行cmd' in names:
        examples.append(('用命令行在“C:/Demo”下面新建“资料”目录。',[step('运行cmd',{'命令':'mkdir "C:/Demo/资料"'})]))
    if '文本输入' in names:
        examples.append(('往当前文本框填入“示例内容”，不要按回车。',[step('文本输入',{'内容':'示例内容'})]))
    if '打开网页' in names:
        examples.append(('请访问网站，地址我稍后提供。',None))
    return examples[:4]


def planning_schema(names, drafts=(), text=""):
    urls,selectors=literal_values(text)
    choices=[]
    for name in names:
        params=model_parameter_schema(name,text)
        for key in params.get('required',[]):
            if params['properties'][key].get('type')=='string':params['properties'][key]['minLength']=1
        literals=re.findall(r'[“\"]([^”\"]+)[”\"]',text)
        if name=='文本输入' and len(literals)==1:params['properties']['内容']['enum']=literals
        paths=[v for v in literals if re.match(r'^[A-Za-z]:[/\\]',v)]
        if name=='快速文件操作' and paths:
            params['properties']['源路径']['enum']=paths
            params['properties']['目标路径']['enum']=paths+['']
        for key in ('url','网址'):
            if urls and key in params['properties']:params['properties'][key]['enum']=urls
        if selectors and 'selector' in params['properties']:
            params['properties']['selector']['enum']=selectors
            if 'by' in params['properties']:params['properties']['by']['enum']=['CSS选择器']
        variable=re.search(r'(?:保存到|存入|到)变量\s*([^\s，。；;]+)',text)
        if variable and name=='Crawl4AI网页抓取':
            params['properties']['变量']['enum']=[variable.group(1)]
            params['required']=list(dict.fromkeys(params.get('required',[])+['变量']))
        choices.append(obj({'type_id':{'const':name},'parameters':params},['type_id','parameters']))
    variants=[obj({'type':{'const':'tool_call'},'name':{'const':'draft_append_batch'},
        'arguments':obj({'instructions':{'type':'array','items':{'oneOf':choices},'minItems':1,'maxItems':30}},['instructions'])},['type','name','arguments']),
        obj({'type':{'const':'message'},'content':{'type':'string'}},['type','content'])]
    if drafts:
        variants.append(obj({'type':{'const':'tool_call'},'name':{'const':'draft_update'},
            'arguments':obj({'row':{'type':'integer','minimum':1,'maximum':len(drafts)},'parameters':{'type':'object'}},['row','parameters'])},['type','name','arguments']))
    return {'oneOf':variants}


def _plan_single(text, settings, context, drafts=()):
    primitive=primitive_step(text)
    if primitive:return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[primitive]}}
    explicit=explicit_plan(text)
    if explicit:return explicit
    verification=parse_verify_task(text)
    if verification:return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[{'type_id':'截图OCR核验','parameters':{'窗口标题':verification['window_title'],'预期文字':'|'.join(verification['expected_text'])}}]}}
    quick=parse_file_task(text)
    if quick:return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[{'type_id':'快速文件操作','parameters':{'操作':'打开' if quick['action']=='open' else '复制','源路径':quick['source'],'目标路径':quick.get('destination','')}}]}}
    names=candidate_types(text,drafts)
    messages=planning_messages(text,drafts,names)
    local=settings.backend=='compatible' and settings.endpoint.rstrip('/')=='http://127.0.0.1:8766/v1' and settings.model=='anclicker-small'
    payload={'model':settings.model,'messages':messages,'stream':False}
    if settings.backend=='ollama':
        path='/api/chat';payload.update(format='json',keep_alive='3m',options={'temperature':0,'num_predict':1600,'num_ctx':8192})
    else:
        path='/chat/completions';payload.update(temperature=0,max_tokens=1600,response_format={'type':'json_object'})
        if local:
            payload['response_format']={'type':'json_schema','json_schema':{'name':'anclicker_plan','strict':True,'schema':planning_schema(names,drafts,text)}}
    if local:
        with local_model_lease(context,settings.local_profile,settings.idle_seconds) as endpoint:
            data=request_json(endpoint+path,payload,settings,context)
    else:
        stop_local_model()
        data=request_json(settings.endpoint.rstrip('/')+path,payload,settings,context)
    if settings.backend=='ollama':
        if data.get('done_reason')=='length':raise ValueError('计划太长，请拆分需求后重试')
        message=data.get('message',{})
    else:
        choice=(data.get('choices') or [{}])[0]
        if choice.get('finish_reason')=='length':raise ValueError('计划太长，请拆分需求后重试')
        message=choice.get('message',{})
    try:value=json.loads(message.get('content',''))
    except (TypeError,ValueError):raise ValueError('模型没有返回有效计划，请重试') from None
    if not isinstance(value,dict):raise ValueError('计划必须是 JSON 对象')
    if value.get('type')=='message' and isinstance(value.get('content'),str):return value
    if value.get('type')!='tool_call' or value.get('name') not in ('draft_append_batch','draft_update'):
        raise ValueError('模型返回了不支持的草稿动作')
    validate_call(value['name'],value.get('arguments'))
    return value


def plan_drafts(text,settings,context,drafts=()):
    settings.validate()
    explicit = explicit_plan(text)
    if explicit is not None:
        return explicit
    from models.colloquial_sheet import plan as colloquial_sheet_plan
    short=colloquial_sheet_plan(text,context)
    if short is not None:return short
    from models.sheet_edit_contracts import sheet_edit_plan
    edit=sheet_edit_plan(text,context)
    if edit is not None:return edit
    from models.spreadsheet_web_contracts import transfer_plan
    transfer=transfer_plan(text,context)
    if transfer is not None:return transfer
    from models.local_operation_bindings import local_instruction
    bound=local_instruction(text)
    if bound:
        context.metadata['local_operation_binding']={'request':text,'instruction':bound}
        return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[bound]}}
    configuration,dual_plan=_dual.load("pipeline")
    if settings.backend=="compatible" and settings.endpoint.rstrip("/")=="http://127.0.0.1:8766/v1" and settings.model=="anclicker-small" and configuration()["enabled"]:
        return dual_plan(text,settings,context,drafts,ast=context.metadata.get("workflow_ast"))
    from models.api_planner import is_local
    if not is_local(settings):
        return dual_plan(text,settings,context,drafts,ast=context.metadata.get('workflow_ast'))
    original,separator,supplement=text.partition('\n用户补充：')
    numbered=split_numbered_steps(original)
    if numbered is None:
        natural=model_steps(original)
        if len(natural)==1:return _plan_single(text,settings,context,drafts)
        numbered=('',natural)
    intro,steps=numbered;prepared=[];virtual=list(drafts)
    for number,body in enumerate(steps,1):
        context.emit('模型正在规划第 '+str(number)+'/'+str(len(steps))+' 步…')
        if context.stop_requested:raise InterruptedError('已停止')
        resolved=resolve_previous_file(body,virtual)
        request=(intro+'\n当前仅处理第'+str(number)+'步：'+resolved) if intro else resolved
        result=_plan_single(request,settings,context,virtual)
        if separator and result.get('type')=='message':result=_plan_single(request+'\n用户补充：'+supplement,settings,context,virtual)
        if result.get('type')=='message':return {'type':'message','content':'第'+str(number)+'步需要补充：'+result['content']+'（整组步骤尚未写入）'}
        if result.get('name')!='draft_append_batch':raise ValueError('编号列表用于新增步骤；修改已有草稿请单独提出')
        for item in result['arguments']['instructions']:
            item=dict(item);item['note']='第'+str(number)+'步：'+body
            if len(prepared)>=30:raise ValueError('拆分结果超过30行，请分批提交')
            draft=make_draft(**item);prepared.append(item);virtual.append(draft)
    return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':prepared}}
