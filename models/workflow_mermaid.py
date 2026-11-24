"""Lossless Mermaid interchange for AnClicker linear workflow AST v1.
Parameters live in readable JSON comments; unsupported graphs fail explicitly.
"""
import json
import re
from copy import deepcopy
from models.workflow_ast import validate_ast,edges

NODE=re.compile(r'^\s*(n[1-9][0-9]*)\["([^"\n]*)"\]\s*;?\s*$')
EDGE=re.compile(r'^\s*(n[1-9][0-9]*)\s*-->\s*(n[1-9][0-9]*)\s*;?\s*$')

def to_mermaid(ast):
    validate_ast(ast)
    meta={k:v for k,v in ast.items() if k not in ('nodes','edges')}
    lines=['flowchart TD','%% anclicker-workflow '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))]
    for node in ast['nodes']:
        lines.append('%% anclicker-node '+json.dumps(node,ensure_ascii=False,separators=(',',':')))
        label=node['type_id'].replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')
        lines.append('  '+node['id']+'["'+label+'"]')
    for edge in ast['edges']:lines.append('  '+edge['source']+' --> '+edge['target'])
    return '\n'.join(lines)+'\n'

def from_mermaid(text):
    if not isinstance(text,str) or len(text)>2_000_000:raise ValueError('Mermaid内容为空或过大')
    metadata=None;nodes={};labels={};links=[];header=False
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        if line in ('flowchart TD','flowchart LR','graph TD','graph LR'):
            if header:raise ValueError('重复图声明')
            header=True;continue
        if line.startswith('%% anclicker-workflow '):
            if metadata is not None:raise ValueError('重复流程元数据')
            metadata=json.loads(line[len('%% anclicker-workflow '):]);continue
        if line.startswith('%% anclicker-node '):
            node=json.loads(line[len('%% anclicker-node '):])
            if not isinstance(node,dict) or not isinstance(node.get('id'),str) or node['id'] in nodes:raise ValueError('节点元数据无效或重复')
            nodes[node['id']]=node;continue
        if line.startswith('%%'):continue
        match=NODE.fullmatch(line)
        if match:
            key,label=match.groups()
            if key in labels:raise ValueError('重复节点声明')
            labels[key]=label.replace('&quot;','"').replace('&lt;','<').replace('&gt;','>').replace('&amp;','&');continue
        match=EDGE.fullmatch(line)
        if match:links.append(match.groups());continue
        raise ValueError('不支持的Mermaid语法：'+line[:100])
    if not header or not isinstance(metadata,dict):raise ValueError('请导入带AnClicker参数元数据的Mermaid流程')
    if set(metadata)-{'version','revision','next_id'}:raise ValueError('流程元数据包含未知字段')
    if set(labels)!=set(nodes):raise ValueError('节点与参数元数据不一致，不能丢弃参数')
    for key,label in labels.items():
        if label!=nodes[key].get('type_id'):raise ValueError('节点指令名称与元数据不一致')
    incoming={key:0 for key in nodes};outgoing={}
    for a,b in links:
        if a not in nodes or b not in nodes or a in outgoing:raise ValueError('连线悬空、重复或含分支')
        incoming[b]+=1;outgoing[a]=b
        if incoming[b]>1:raise ValueError('暂不支持合流流程')
    if not nodes:
        if links:raise ValueError('空图不能有连线')
        ordered=[]
    else:
        starts=[key for key,value in incoming.items() if value==0]
        if len(starts)!=1:raise ValueError('流程必须是一个完整单链，不能有环或孤立节点')
        ordered=[];seen=set();key=starts[0]
        while key:
            if key in seen:raise ValueError('流程包含环')
            seen.add(key);ordered.append(deepcopy(nodes[key]));key=outgoing.get(key)
        if len(ordered)!=len(nodes):raise ValueError('流程含未连接节点或环')
    return validate_ast({**metadata,'nodes':ordered,'edges':edges(ordered)})
