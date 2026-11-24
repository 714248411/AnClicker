"""V6 edit-mode contract shared by SFT and inference."""
import json
from anclicker._imports import DeferredImports
_imports=DeferredImports(globals(),{
    "schema": ("from","anclicker.domain.agent_protocol",("instruction_schema","obj"),0),
    "planning_schema": ("from","models.draft_planner",("planning_schema",),0),
})

EDIT_SYSTEM='你是AnClicker流程编辑模型。输入包含已有AST和中文修改要求。只输出JSON补丁，不重写整个流程，不执行工具。base_revision必须等于AST.revision。节点按nodes顺序从第1步计数，target和after必须使用真实节点id。add在after后插入，after=null表示最前；delete删除target；update仅修改明确要求的parameters，未提及字段保持；move把target移到after后。不得把删除文件当成删除流程节点，不得把不要删除理解为删除。目标不明确或条件不足时返回{"type":"message","content":"具体追问"}。未指定的节点、参数、连线保持不变。'

def edit_messages(text,ast):
    from models.conversational_contracts import normalize_edit
    text=normalize_edit(text)
    return [{'role':'system','content':EDIT_SYSTEM},{'role':'user','content':json.dumps({'ast':ast,'request':text},ensure_ascii=False,separators=(',',':'))}]


def edit_schema(ast,names,request=""):
    import re
    from models.conversational_contracts import normalize_edit,intent_text,duration,quoted_values,constrain_schema
    request=normalize_edit(request);intent=intent_text(request)
    # Imports are deferred through the module loader below to avoid startup cycles.
    instruction_schema,obj=_imports.load('schema')
    planning_schema=_imports.load('planning_schema')
    ids=[n['id'] for n in ast['nodes']]
    target={'type':'string','enum':ids}
    after={'enum':[None,*ids]}
    choices=[obj({'op':{'const':'delete'},'target':target},['op','target']),obj({'op':{'const':'move'},'target':target,'after':after},['op','target','after'])]
    for node in ast['nodes']:
        params=instruction_schema(node['type_id'])['parameters'];params=dict(params,required=[],minProperties=1)
        choices.append(obj({'op':{'const':'update'},'target':{'const':node['id']},'parameters':params},['op','target','parameters']))
    additions=planning_schema(names,(),text=request)['oneOf'][0]['properties']['arguments']['properties']['instructions']['items']
    additions['oneOf']=constrain_schema(request,additions['oneOf'])
    choices.append(obj({'op':{'const':'add'},'after':after,'node':additions},['op','after','node']))
    # Constrain to the operation actually requested; a duration edit cannot delete a node.
    kind=('add' if re.search(r'插入|后面加|之后加|前面加',intent) else 'move' if re.search(r'移到|移动|最前面|最后面',intent) else 'delete' if re.search(r'删除|去掉|删掉',intent) else 'update' if re.search(r'改成|改为|换成|修改|调整',intent) else None)
    rows=[int(x) for x in re.findall(r'第([0-9]+)步',intent)]
    valid=bool(rows) and all(1<=n<=len(ids) for n in rows)
    grounded=False
    if kind:
        choices=[c for c in choices if c['properties']['op']['const']==kind]
    if valid and kind in ('delete','update') and len(set(rows))==1:
        node=ast['nodes'][rows[0]-1];target_id=node['id']
        choices=[c for c in choices if kind!='update' or c['properties']['target'].get('const')==target_id]
        for c in choices:c['properties']['target']={'const':target_id}
        grounded=kind=='delete'
        if kind=='update':
            vals=duration(request);quoted=quoted_values(request);urls=re.findall(r'https?://[^\s，。；;]+',request)
            values=vals if node['type_id']=='时间等待' and vals else {'内容':quoted[0]} if node['type_id']=='文本输入' and len(quoted)==1 else {'url':urls[0]} if node['type_id']=='打开网页' and len(urls)==1 else None
            if values:
                for c in choices:
                    required=[k for k in values if k!='单位' or node['parameters'].get('单位')!=values[k]]
                    c['properties']['parameters']=obj({k:{'const':v} for k,v in values.items()},required)
                grounded=True
    elif valid and kind=='add' and len(set(rows))==1 and duration(request) and '等待' in intent:
        for c in choices:c['properties']['after']={'const':(None if rows[0]==1 else ids[rows[0]-2]) if '前面加' in intent else ids[rows[0]-1]}
        # More complex insert locations still permit clarification.
        grounded='前面加' not in intent
    if valid and kind=='move' and len(rows)==2:
        target_id=ids[rows[0]-1]
        destination=rows[1]-1
        if re.search(r'第[0-9]+步前面',intent):
            predecessors=[x for x in ids[:destination] if x!=target_id]
            after_id=predecessors[-1] if predecessors else None
        elif re.search(r'第[0-9]+步后面',intent):after_id=ids[destination]
        else:after_id='__unknown__'
        if after_id!='__unknown__' and after_id!=target_id:
            for c in choices:
                c['properties']['target']={'const':target_id};c['properties']['after']={'const':after_id}
            grounded=True
    operation_schema={'type':'array','items':{'oneOf':choices},'minItems':1,'maxItems':1 if kind else 30}
    patch=obj({'base_revision':{'const':ast['revision']},'operations':operation_schema},['base_revision','operations'])
    message=obj({'type':{'const':'message'},'content':{'type':'string','minLength':1}},['type','content'])
    return {'oneOf':[patch] if grounded else [patch,message]}


def prompt_ast(ast):
    instruction_schema,_=_imports.load('schema')
    nodes=[]
    for node in ast['nodes']:
        schema=instruction_schema(node['type_id']);defaults=schema['defaults']
        params={k:v for k,v in node['parameters'].items() if v!=defaults.get(k) or k in schema['required_fields'] or k in ('时长','单位','内容','url','源路径','目标路径','操作')}
        nodes.append({'id':node['id'],'type_id':node['type_id'],'parameters':params})
    return {'version':1,'revision':ast['revision'],'nodes':nodes}
