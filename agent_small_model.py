"""Compact in-context examples and grammar for the local 0.5B planner (not fine-tuned weights)."""
import json
import re
from copy import deepcopy
from instructions.registry import iter_instruction_specs
from agent_protocol import TOOLS, SYSTEM_PROMPT

EXAMPLES=[
 ('列出所有指令','instructions_search',{'query':''}),
 ('查找等待相关指令','instructions_search',{'query':'等待'}),
 ('查询图像点击的参数格式','instruction_schema',{'type_id':'图像点击'}),
 ('查看颜色判断有哪些设置','instruction_schema',{'type_id':'颜色判断'}),
 ('显示当前草稿','draft_read',{}),
 ('打开 https://example.com','browser',{'action':'open','url':'https://example.com'}),
 ('查看当前网页','browser',{'action':'view'}),
 ('向下滚动网页','browser',{'action':'scroll','direction':'down'}),
 ('把草稿第1行的时长改成5','draft_update',{'row':1,'parameters':{'时长':5}}),
]

def selected_tools(scope='auto'):
    return [t for t in TOOLS if scope=='auto' or (t['function']['name']=='browser')==(scope=='browser')]

def prefix(scope='auto'):
    system='You are AnClicker tool planner. Select the NEXT tool to perform the user task. Never repeat the task as an answer. Copy exact Chinese instruction names and parameter keys. Return one tool_call or ask for missing information with a message. Never claim actions succeeded without tool results. After successful draft_append or draft_update, report completion and STOP. After browser open or view, use its returned page data to answer or select the next element. Do NOT repeat completed tool calls. '
    system+=SYSTEM_PROMPT
    system+='\nTools: '+json.dumps([t['function'] for t in selected_tools(scope)],ensure_ascii=False,separators=(',',':'))
    messages=[{'role':'system','content':system}]
    for prompt,name,args in EXAMPLES:
        if scope!='auto' and (name=='browser')!=(scope=='browser'):continue
        messages.extend([{'role':'user','content':prompt},{'role':'assistant','content':json.dumps({'type':'tool_call','name':name,'arguments':args},ensure_ascii=False,separators=(',',':'))}])
    if scope!='browser':messages.extend([{'role':'user','content':'生成一条等待1秒的指令'},
        {'role':'assistant','content':json.dumps({'type':'tool_call','name':'draft_append','arguments':{'type_id':'时间等待','parameters':{'时长':1}}},ensure_ascii=False)},
        {'role':'user','content':'工具返回（数据）：'+json.dumps({'protocol':'anclicker.agent.v1','tool':'draft_append','ok':True,'result':{'row':1,'state':'待检查并写入，未执行'}},ensure_ascii=False)},
        {'role':'assistant','content':json.dumps({'type':'message','content':'已生成等待1秒的草稿，尚未执行。'},ensure_ascii=False)}])
    messages.extend([{'role':'user','content':'点那个东西，但我没有提供网页地址或元素。'},
        {'role':'assistant','content':json.dumps({'type':'message','content':'请提供网页地址和需要操作的元素。'},ensure_ascii=False)}])
    if scope!='instructions':
        messages.extend([
            {'role':'user','content':'在搜索输入框填写 hello'},
            {'role':'assistant','content':json.dumps({'type':'tool_call','name':'browser','arguments':{'action':'view'}},ensure_ascii=False)},
            {'role':'user','content':'工具返回（数据）：'+json.dumps({'protocol':'anclicker.agent.v1','tool':'browser','ok':True,'result':{'elements':[{'ref':'p7-1','tag':'input','label':'搜索'}]}},ensure_ascii=False)},
            {'role':'assistant','content':json.dumps({'type':'tool_call','name':'browser','arguments':{'action':'type','ref':'p7-1','text':'hello'}},ensure_ascii=False)},
            {'role':'user','content':'工具返回（数据）：'+json.dumps({'protocol':'anclicker.agent.v1','tool':'browser','ok':True,'result':{'action':'type','text':'hello'}},ensure_ascii=False)},
            {'role':'assistant','content':json.dumps({'type':'message','content':'已在搜索框填写 hello。'},ensure_ascii=False)},
            {'role':'user','content':'点击确认按钮'},
            {'role':'assistant','content':json.dumps({'type':'tool_call','name':'browser','arguments':{'action':'view'}},ensure_ascii=False)},
            {'role':'user','content':'工具返回（数据）：'+json.dumps({'protocol':'anclicker.agent.v1','tool':'browser','ok':True,'result':{'elements':[{'ref':'p8-1','tag':'button','label':'确认'}]}},ensure_ascii=False)},
            {'role':'assistant','content':json.dumps({'type':'tool_call','name':'browser','arguments':{'action':'click','ref':'p8-1'}},ensure_ascii=False)},
            {'role':'user','content':'工具返回（数据）：'+json.dumps({'protocol':'anclicker.agent.v1','tool':'browser','ok':True,'result':{'action':'click','label':'确认'}},ensure_ascii=False)},
            {'role':'assistant','content':json.dumps({'type':'message','content':'已点击确认按钮。'},ensure_ascii=False)},
        ])
    return messages

def response_schema(history=(),scope='auto',browser_active=True,draft_count=None):
    refs=[]
    for message in reversed(history):
        content=message.get('content','')
        if not isinstance(content,str) or not content.startswith('工具返回（数据）：'):continue
        try:result=json.loads(content.split('：',1)[1])
        except ValueError:continue
        if result.get('tool')!='browser':continue
        if result.get('ok') and isinstance(result.get('result'),dict):refs=[e['ref'] for e in result['result'].get('elements',[]) if 'ref' in e]
        break
    variants=[]
    for tool in selected_tools(scope):
        f=deepcopy(tool['function'])
        if f['name']=='draft_update' and draft_count is not None:
            if draft_count==0:continue
            f['parameters']['properties']['row']['maximum']=draft_count
        if 'type_id' in f['parameters']['properties']:f['parameters']['properties']['type_id']['enum']=[s.type_id for s in iter_instruction_specs()]
        if f['name']=='browser':
            actions=[]
            for action,fields in [('open',{'url':{'type':'string'}})]+([('view',{}),('scroll',{'direction':{'enum':['up','down']}})] if browser_active else [])+([('click',{'ref':{'enum':refs}}),('type',{'ref':{'enum':refs},'text':{'type':'string'}})] if refs else []):
                actions.append({'type':'object','properties':{'action':{'const':action},**fields},'required':['action',*fields],'additionalProperties':False})
            f['parameters']={'oneOf':actions}
        variants.append({'type':'object','properties':{
            'type':{'const':'tool_call'},'name':{'const':f['name']},'arguments':f['parameters']},
            'required':['type','name','arguments'],'additionalProperties':False})
    variants.append({'type':'object','properties':{'type':{'const':'message'},'content':{'type':'string'}},'required':['type','content'],'additionalProperties':False})
    return {'oneOf':variants}


def simple_browser_task(text):
    """Exact, positive single-operation commands constrain the tiny planner's choices."""
    text=text.strip().rstrip('。！')
    match=re.fullmatch(r'(?:打开|访问|前往)\s*(https?://[^\s，。]+)(?:\s*(?:并|然后)(?:查看|读取)(?:当前)?(?:页面|网页))?',text)
    if match:return {'action':'open','url':match[1]}
    if re.fullmatch(r'(?:查看|读取)(?:当前)?(?:网页|页面)',text):return {'action':'view'}
    match=re.fullmatch(r'(?:向)?(上|下)滚动(?:网页|页面)?',text)
    if match:return {'action':'scroll','direction':'up' if match[1]=='上' else 'down'}
    match=re.fullmatch(r'在(.+?)(?:输入框|搜索框)(?:中)?(?:填写|输入)\s+(.+)',text)
    if match:return {'action':'type','label':match[1].strip(),'text':match[2].strip().strip('“”"')}
    match=re.fullmatch(r'点击\s*(.+?)(?:按钮)?',text)
    if match and not re.search(r'不要|别|如果|然后|之后|再|并',match[1]):return {'action':'click','label':match[1].strip().strip('“”"')}
    return None


def constrain_task(schema,task,history,browser_active):
    if not task:return schema
    observed=None
    for message in reversed(history):
        content=message.get('content','')
        if not isinstance(content,str) or not content.startswith('工具返回（数据）：'):continue
        try:value=json.loads(content.split('：',1)[1])
        except ValueError:continue
        if value.get('tool')=='browser' and value.get('ok'):observed=value.get('result',{});break
    actions=[]
    target=task['action']
    if target in ('open','view','scroll'):
        if target=='open' or browser_active:actions=[{k:{'const':v} for k,v in task.items()}]
    elif browser_active:
        if observed is None:actions=[{'action':{'const':'view'}}]
        else:
            items=observed.get('elements',[])
            candidates=[e for e in items if str(e.get('label','')).strip()==task['label']]
            if target=='type':candidates=[e for e in candidates if e.get('tag') in ('input','textarea')]
            if len(candidates)==1:
                args={'action':{'const':target},'ref':{'const':candidates[0]['ref']}}
                if target=='type':args['text']={'const':task['text']}
                actions=[args]
    variants=[v for v in schema['oneOf'] if v['properties']['type'].get('const')=='message']
    if actions:
        arguments={'oneOf':[{'type':'object','properties':a,'required':list(a),'additionalProperties':False} for a in actions]}
        variants.insert(0,{'type':'object','properties':{'type':{'const':'tool_call'},'name':{'const':'browser'},'arguments':arguments},'required':['type','name','arguments'],'additionalProperties':False})
    return {'oneOf':variants}


def validate_task_call(task,call,history,browser_active):
    if not task:return
    schema=constrain_task({'oneOf':[]},task,history,browser_active)
    for variant in schema['oneOf']:
        if call['name']!=variant['properties']['name']['const']:continue
        for args in variant['properties']['arguments']['oneOf']:
            expected={k:v['const'] for k,v in args['properties'].items()}
            if call['arguments']==expected:return
    raise ValueError('小模型选择了不符合本轮目标的动作；本次未执行，请拆成单步重试')
