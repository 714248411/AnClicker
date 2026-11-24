"""Ground short follow-up requests in the real active workbook, not guessed paths."""
import re
from anclicker.platform.rpa_bridge import get_bridge

def plan(text,context):
    original,_,answer=text.partition('\n用户补充：')
    t=original.strip().rstrip('。！');answer=answer.strip().rstrip('。！')
    def ask(message):return {'type':'message','content':message}
    def batch(items):return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':items}}
    if re.fullmatch(r'(?:把|将)?(?:这张|那张|当前|刚才那张)(?:表|表格)(?:的内容)?(?:填到|填入)(?:当前)?网页(?:里|中)?[，,]?\s*(?:对着(?:名字|名称)|按(?:名字|名称|表头))(?:对应)?填',t):
        return batch([{'type_id':'表格填入网页','parameters':{'range':'','mode':'按表头对应','header':'首行表头'}}])
    if re.fullmatch(r'(?:剩下的|其他的)(?:也)?照(?:这个|刚才那样)填',t):
        return ask('“剩下的”指表格剩余行，还是网页里尚未填写的字段？')
    if re.fullmatch(r'把网页(?:上)?的结果(?:放回|写回)(?:刚才)?那张表',t):
        return ask('网页上的哪块结果？写回表格时是接在末尾，还是放进某一列？')
    save=bool(re.fullmatch(r'(?:保存|存)(?:一下|起来|好)?(?:表格)?',t))
    match=re.fullmatch(r'(?:把)?(?:(.+?)的)?(?:名字|姓名)(?:改成|改为|换成|填成)(.+?)(?:[，,]\s*(?:编号|号码)(?:别动|不动|不要改))?',t)
    if not match and not save:return None
    try:state=get_bridge().execute({'id':'inspectActiveSheet','params':{}},context=context,timeout=15)['result']
    except Exception as error:return ask('请先在 AnClicker 打开要修改的表格。'+str(error))
    identity={'path':state.get('path'),'sheet':state.get('sheet')}
    previous=context.metadata.get('pending_sheet_target')
    if previous and previous!=identity:return ask('当前表格已切换，请重新指定这次要修改的表格；尚未写入。')
    if save:return batch([{'type_id':'保存Excel','parameters':{}}])
    key,value=match.groups();value=value.strip().strip('“”"')
    if not value or any(c in value for c in '\r\n') or '$'+'{' in value:return ask('请提供要填写的姓名原文。')
    rows=state.get('rows') or []
    if not rows:return ask('当前表格是空的，姓名应放在哪一列？')
    columns=[i for i,v in enumerate(rows[0]) if str(v).strip() in ('姓名','名字')]
    if len(columns)!=1:return ask('当前表头无法唯一确定姓名列，请指出列名。')
    choices=[i for i,row in enumerate(rows[1:],2) if any(str(v).strip() for v in row)]
    selection=answer or (key+'那行' if key else '')
    if selection in ('全部','所有人','所有行','都改','全部都改'):selected=choices
    elif selection:
        rownumber=re.fullmatch(r'第([二三四五六七八九十0-9]+)行',selection)
        if rownumber:
            from models.chinese_planner import chinese_number
            selected=[int(chinese_number(rownumber[1]))] if int(chinese_number(rownumber[1])) in choices else []
        else:
            named=re.fullmatch(r'(?:改|就)?(.+?)(?:那行|那一行)',selection)
            selected=[i for i in choices if named and named[1] in [str(v) for v in rows[i-1]]]
        if len(selected)!=1 and selection not in ('全部','所有人','所有行','都改','全部都改'):selected=[]
    else:selected=choices if len(choices)==1 else []
    if not selected:
        context.metadata['pending_sheet_target']=identity
        return ask('要改哪一行的姓名？可以说“张三那行”“第2行”或“所有行”；编号会保持不动。')
    column=columns[0]+1;letters=''
    while column:column,mod=divmod(column-1,26);letters=chr(65+mod)+letters
    context.metadata['colloquial_sheet_binding']={'target':identity,'rows':selected,'column':letters}
    return batch([{'type_id':'Excel写入单元格','parameters':{'cell':letters+str(row),'value':value}} for row in selected])
