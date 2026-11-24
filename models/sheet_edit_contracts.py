"""Bind literal cell edits without losing coordinates or quoted payloads."""
import re
from models.conversational_contracts import QUOTED

def sheet_edit_plan(text,context):
    if not re.search(r'表格|Excel',text,re.I) or re.search(r'网页|CSS',QUOTED.sub('',text),re.I):return None
    from models.dual_model import clauses
    parts,_=clauses(text)
    items=[];bound=False
    prefix=re.compile(r'^(?:请|帮我)?(?:在|把|将)?(?:当前|这个)?(?:表格|Excel)(?:[“"]([A-Za-z]:[^”"]+\.xlsx)[”"])?(?:工作表[“"]([^”"]+)[”"])?(?:中|里)?(?:的)?',re.I)
    for part in parts:
        part=re.sub(r'^(?:然后|接着|再)','',part.strip()).strip()
        if re.fullmatch(r'保存(?:一下|表格|Excel)?',part,re.I):
            if not bound:return None
            items.append({'type_id':'保存Excel','parameters':{}});continue
        match=prefix.match(part)
        if match:
            path,sheet=match.groups();part=part[match.end():].strip();bound=True
            if path:items.append({'type_id':'打开Excel','parameters':{'path':path,'sheetName':sheet or ''}})
            elif sheet:return {'type':'message','content':'请提供表格文件路径，或使用当前工作表。'}
        if not bound:return None
        match=re.fullmatch(r'(?:在)?([A-Za-z]{1,3}[1-9][0-9]*)(?:单元格)?(?:中|里)?(?:填入|填成|填写|写入|改成|改为)\s*(“[^”]*”|"[^"]*")',part)
        if not match:return None
        address,value=match.groups();address=address.upper();col=0
        for ch in re.match('[A-Z]+',address)[0]:col=col*26+ord(ch)-64
        if col>16384 or int(re.search('[0-9]+',address)[0])>1048576:return {'type':'message','content':'单元格地址超出 Excel 范围。'}
        items.append({'type_id':'Excel写入单元格','parameters':{'cell':address,'value':value[1:-1]}})
    if not items:return None
    context.metadata['sheet_edit_binding']={'request':text,'steps':len(items)}
    return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':items}}
