"""Ground every planner choice in the live instruction registry."""
import json
import re
from anclicker.domain.agent_protocol import catalog, instruction_schema, make_draft

ALIASES = {
 '打开文件':'快速文件操作','复制文件':'快速文件操作','拷贝文件':'快速文件操作',
 '打开文件夹':'快速文件操作','启动程序':'运行外部文件','执行命令':'运行cmd',
 '执行脚本':'运行Python','重命名':'重命名文件（白话）','查找文件':'查找文件（白话）',
 '统计文件':'统计文件（白话）','截屏':'屏幕截图','截图':'屏幕截图',
 '剪贴板':'复制到剪贴板','剪切板':'获取剪切板','识别文字':'OCR文字提取',
 '移动光标':'移动鼠标','拖动鼠标':'鼠标拖拽','滚动':'滚轮滑动','按回车':'按下键盘',
 '读取表格':'读取区域','写入表格':'写入区域','保存表格':'保存Excel','打开表格':'打开Excel',
 '循环执行':'循环','如果':'条件判断','后台绑定':'绑定选择窗口',
}

def normalize(text):
    return re.sub(r'[\s（）()·]','',text).casefold()

def select_types(text, drafts=(), hints=()):
    query=normalize(text);items=catalog();selected=[]
    # Exact instruction names win over broad words such as 打开 or 点击.
    for item in items:
        if any(normalize(label) in query for label in (item['type_id'],item['name'])):
            selected.append(item['type_id'])
    for word,name in ALIASES.items():
        if word in text and name not in selected:selected.append(name)
    for name,pattern in hints:
        if re.search(pattern,text,re.I) and name not in selected:selected.append(name)
    if not selected:
        grams={query[i:i+2] for i in range(len(query)-1)}
        scored=[]
        for item in items:
            label=normalize(item['type_id']+' '+item['name'])
            score=sum(g in label for g in grams)
            if score:scored.append((score,item['type_id']))
        selected=[name for _,name in sorted(scored,reverse=True)[:6]]
    for draft in drafts:
        if draft.type_id not in selected:selected.append(draft.type_id)
    return selected

def explicit_plan(text):
    """Unambiguous parameter JSON is validated without asking a model to rewrite it."""
    match=re.fullmatch(r'\s*(?:使用|添加|生成)?[「【]?(.+?)[」】]?\s*参数\s*[:：]?\s*(\{.*\})\s*',text,re.S)
    if not match:return None
    name=match[1].strip();names={item['type_id'] for item in catalog()}
    if name not in names:return None
    params=json.loads(match[2]);make_draft(name,params)
    return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[{'type_id':name,'parameters':params}]}}

def overview():
    groups={}
    for item in catalog():groups.setdefault(item['category'],[]).append(item['type_id'])
    return groups
