"""Transactional, revisioned linear workflow AST and strict patch merger."""
import re
from copy import deepcopy
from anclicker.domain.agent_protocol import make_draft,draft_data
from anclicker.domain.instructions import InstructionDraft

ID=re.compile(r'^n[1-9][0-9]*$')

def edges(nodes):return [{'source':a['id'],'target':b['id']} for a,b in zip(nodes,nodes[1:])]

def validate_ast(ast):
    if not isinstance(ast,dict) or ast.get('version')!=1:raise ValueError('不支持的AST版本')
    if type(ast.get('revision')) is not int or ast['revision']<0:raise ValueError('AST修订号无效')
    if set(ast)-{'version','revision','next_id','nodes','edges'}:raise ValueError('AST包含未知字段')
    if 'next_id' in ast and (type(ast['next_id']) is not int or ast['next_id']<1):raise ValueError('AST节点序号无效')
    nodes=ast.get('nodes');seen=set()
    if not isinstance(nodes,list) or len(nodes)>100:raise ValueError('流程最多100步')
    for node in nodes:
        if not isinstance(node,dict) or not isinstance(node.get('id'),str) or not ID.fullmatch(node['id']) or node['id'] in seen:raise ValueError('节点ID无效或重复')
        seen.add(node['id'])
        if set(node)-{'id','type_id','parameters','repeat_count','note','error_policy'}:raise ValueError('节点包含未知字段')
        make_draft(node['type_id'],node['parameters'],node.get('repeat_count',1),node.get('note',''))
        if 'error_policy' in node:InstructionDraft.from_mapping({k:v for k,v in node.items() if k!='id'})
    if ast.get('edges')!=edges(nodes):raise ValueError('目前仅支持单链流程AST；分支和循环不能自动展平')
    return ast

def from_drafts(drafts,revision=0):
    nodes=[{'id':'n'+str(i+1),**draft_data(d)} for i,d in enumerate(drafts)]
    return validate_ast({'version':1,'revision':revision,'next_id':len(nodes)+1,'nodes':nodes,'edges':edges(nodes)})

def to_drafts(ast):
    validate_ast(ast)
    return [InstructionDraft.from_mapping({k:v for k,v in n.items() if k!='id'}) for n in ast['nodes']]

def apply_patch(ast,patch):
    validate_ast(ast)
    if not isinstance(patch,dict) or set(patch)!={'base_revision','operations'}:raise ValueError('补丁字段无效')
    if type(patch['base_revision']) is not int or patch['base_revision']!=ast['revision']:raise ValueError('流程已变化，补丁修订号过期，请重新生成')
    operations=patch['operations']
    if not isinstance(operations,list) or not 1<=len(operations)<=30:raise ValueError('补丁必须包含1至30个操作')
    result=deepcopy(ast);nodes=result['nodes']
    def index(key):
        for i,node in enumerate(nodes):
            if node['id']==key:return i
        raise ValueError('补丁引用不存在的节点：'+str(key))
    for op in operations:
        if not isinstance(op,dict):raise ValueError('补丁操作必须是对象')
        kind=op.get('op')
        fields={'add':{'op','after','node'},'delete':{'op','target'},'update':{'op','target','parameters'},'move':{'op','target','after'}}
        if kind not in fields or set(op)!=fields[kind]:raise ValueError('补丁操作字段无效')
        if kind=='add':
            body=op['node']
            if not isinstance(body,dict) or set(body)!={'type_id','parameters'}:raise ValueError('新增节点字段无效')
            draft=make_draft(body['type_id'],body['parameters'])
            number=max(result.get('next_id',1),max([int(n['id'][1:])+1 for n in nodes] or [1]))
            result['next_id']=number+1
            position=0 if op['after'] is None else index(op['after'])+1
            nodes.insert(position,{'id':'n'+str(number),**draft_data(draft)})
        elif kind=='delete':nodes.pop(index(op['target']))
        elif kind=='update':
            node=nodes[index(op['target'])]
            if not isinstance(op['parameters'],dict) or not op['parameters']:raise ValueError('更新参数不能为空')
            parameters=deepcopy(node['parameters']);parameters.update(op['parameters'])
            make_draft(node['type_id'],parameters,node.get('repeat_count',1),node.get('note',''))
            node['parameters']=parameters
        else:
            if op['after']==op['target']:raise ValueError('不能移动到自身后面')
            source=index(op['target'])
            if op['after'] is not None:index(op['after'])
            node=nodes.pop(source);position=0 if op['after'] is None else index(op['after'])+1;nodes.insert(position,node)
    result['edges']=edges(nodes);result['revision']+=1
    return validate_ast(result)
