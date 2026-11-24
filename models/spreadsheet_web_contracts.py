"""Compile explicitly grounded spreadsheet/web transfers as one atomic native plan."""
import re
from models.conversational_contracts import QUOTED,quoted_values,no_enter
from models.web_contracts import URL

def transfer_plan(text,context):
    simple=simple_fill_plan(text,context)
    if simple is not None:return simple
    intent=QUOTED.sub('引用内容',text)
    if not (re.search(r'网页|网站|CSS',intent,re.I) and re.search(r'表格|Excel|\.xlsx',text,re.I) and re.search(r'复制|填入|粘贴|提取|写入|写回|获取|粘到|拷到|放到|存入',intent)):
        return None
    def ask(message):return {'type':'message','content':message}
    negative_intent=re.sub(r'(?:先)?(?:不要|别|不用)(?:按|敲)?(?:回车|提交)','',intent)
    if re.search(r'不要|别|不必|不用',negative_intent):return ask('请明确要执行的表格与网页操作；当前包含否定要求，尚未生成步骤。')
    from models.dual_model import clauses
    parts,_=clauses(text)
    prepared=[];last_path=None;last_url=None;bindings=[]
    def add(kind,**params):prepared.append({'type_id':kind,'parameters':params})
    for part in parts:
        t=QUOTED.sub('引用内容',part)
        if no_enter(part) and not re.search(r'复制|填入|粘贴|提取|写入|写回|获取|粘到|拷到|放到|存入',t):continue
        urls=URL.findall(part)
        if len(urls)>1:return ask('每次表格传递请指定一个目标网页。')
        if urls and urls[0]!=last_url:
            add('打开网页',url=urls[0]);last_url=urls[0]
        if not re.search(r'复制|填入|粘贴|提取|写入|写回|获取|粘到|拷到|放到|存入',t):
            if re.fullmatch(r'(?:先|然后|接着|再)?打开(?:网页)?\s*https?://\S+',part.strip()):continue
            return ask('请把表格传递写清楚：文件路径、工作表、单元格区域和网页元素位置。')
        paths=[v for v in quoted_values(part) if re.match(r'^[A-Za-z]:[/\\]',v) and v.lower().endswith('.xlsx')]
        if len(paths)>1:return ask('请将不同表格的读写分成两句，每句指定一个文件。')
        path=paths[0] if paths else last_path if re.search(r'同一个表格|同一表格|原表格',t) else None
        if not path:return ask('请提供表格的完整 .xlsx 文件路径，并用引号括起来。')
        sheet=re.search(r'(?:工作表|sheet)\s*(?:“([^”]+)”|"([^"]+)"|([A-Za-z0-9_\u4e00-\u9fff]+?)(?=\s|的|[，,；;]|$))',part,re.I)
        if not sheet:return ask('请明确工作表名称，例如：工作表“数据”。')
        sheet=next(v for v in sheet.groups() if v is not None)
        masked=QUOTED.sub(lambda m:' '*(m.end()-m.start()),part)
        masked=URL.sub('',masked)
        masked=re.sub(r'CSS\s*[#.][A-Za-z_][A-Za-z0-9_-]*','',masked,flags=re.I)
        cells=re.findall(r'(?<![A-Za-z0-9_#])\$?[A-Za-z]{1,3}\$?[1-9][0-9]*(?::\$?[A-Za-z]{1,3}\$?[1-9][0-9]*)?(?![A-Za-z0-9_])',masked)
        if len(cells)!=1:return ask('请明确一个单元格或区域，例如 A1、A1:B3。')
        cell=cells[0].replace('$','').upper()
        for address in cell.split(':'):
            match=re.fullmatch(r'([A-Z]+)([0-9]+)',address);col=0
            for letter in match[1]:col=col*26+ord(letter)-64
            if col>16384 or int(match[2])>1048576:return ask('单元格超出 Excel 范围，请检查地址。')
        locator=re.search(r'CSS\s*(?:“([^”]+)”|"([^"]+)"|([#.][A-Za-z_][A-Za-z0-9_-]*))',part,re.I)
        if not locator:return ask('请提供网页位置：可使用元素拾取器取得 CSS 定位，再写成 CSS #元素名。')
        selector=next(v for v in locator.groups() if v is not None)
        if not last_url and not re.search(r'当前网页|当前页面',text):return ask('请提供网页地址，或明确使用当前网页。')
        last_path=path
        to_web=bool(re.search(r'(?:复制到|粘贴到|填入|写入|放到|拷到|粘到)(?:当前)?网页',t))
        to_sheet=bool(re.search(r'(?:写入|写回|存入|填入|保存到)(?:同一个|同一|原)?表格',t))
        if to_web and to_sheet:return ask('请将表格到网页、网页到表格分成两句，并分别指定位置。')
        if not to_web and not to_sheet:return ask('请明确方向：把表格区域填入网页，或把网页文字写入表格。')
        if to_sheet:
            if ':' in cell:return ask('网页提取写回请指定起始单元格，例如 C3；多项结果会从这里向下写。')
            add('提取文本到表格',selector=selector,by='CSS选择器',all='全部匹配' if re.search(r'全部|所有',t) else '单个',filter='文本与数字',toPath=path,toSheet=sheet,toCell=cell,save='保存')
        else:
            variable='表格传递_'+str(len(prepared)+1)
            add('打开Excel',path=path,sheetName=sheet)
            add('读取区域',range=cell,varName=variable,format='制表符文本')
            add('输入文本',selector=selector,by='CSS选择器',textVariable=variable,text='',pressEnter='否',clear='是')
        bindings.append({'request':part,'file':path,'sheet':sheet,'cell':cell,'selector':selector})
    if not prepared:return ask('请补充表格和网页传递的位置。')
    from anclicker.domain.agent_protocol import make_draft
    for item in prepared:make_draft(**item)
    context.metadata['spreadsheet_web_bindings']=bindings
    return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':prepared}}

def simple_fill_plan(text,context):
    """Bind a short request to the active workbook/page at execution time."""
    intent=QUOTED.sub('引用',text)
    if not (re.search(r'表格|Excel',intent,re.I) and re.search(r'网页|页面|网站',intent) and re.search(r'填|粘贴|复制',intent)):return None
    if re.search(r'CSS|提取|写回|存入',intent,re.I):return None
    paths=[v for v in quoted_values(text) if re.match(r'^[A-Za-z]:[/\\]',v) and v.lower().endswith('.xlsx')]
    urls=URL.findall(text)
    if len(paths)>1 or len(urls)>1:return {'type':'message','content':'请指定一个表格和一个目标网页。'}
    sheet=re.search(r'工作表\s*[“"]([^”"]+)[”"]',text)
    remaining=text
    if sheet:remaining=remaining.replace(sheet[0],'')
    for value in paths:remaining=remaining.replace('“'+value+'”','').replace('"'+value+'"','')
    remaining=URL.sub('',remaining)
    area=re.search(r'(?<![A-Za-z0-9])([A-Z]{1,3}[1-9][0-9]*(?::[A-Z]{1,3}[1-9][0-9]*)?)(?![A-Za-z0-9])',remaining,re.I)
    if area:
        addresses=[]
        for address in area[1].upper().split(':'):
            cell=re.fullmatch(r'([A-Z]+)([0-9]+)',address);column=0
            for letter in cell[1]:column=column*26+ord(letter)-64
            row=int(cell[2]);addresses.append((row,column))
            if row>1048576 or column>16384:return {'type':'message','content':'单元格超出 Excel 范围，请检查区域。'}
        if len(addresses)==2 and (addresses[1][0]<addresses[0][0] or addresses[1][1]<addresses[0][1]):return {'type':'message','content':'表格区域的结束位置不能在开始位置之前。'}
        remaining=remaining[:area.start()]+remaining[area.end():]
    remaining=re.sub(r'(?:先)?(?:不要|别|不用)(?:按|敲)?(?:回车|提交)','',remaining)
    allowed=r'(?:请|麻烦|帮我|先|把|将|当前|这个|已打开的|打开的|表格|Excel|内容|数据|的|填入|填到|填上|填写|填|复制|粘贴|到|网页|页面|网站|里|中|上|对应|后面|位置|输入框|按|顺序|依次|逐个|表头|字段|首行|无表头|不含表头|不带表头|含表头|全部|所有|然后|再|一下|吧|[\s，,；;。])+ '
    if not re.fullmatch(allowed.strip(),remaining,re.I):return None
    mode='按表头对应' if re.search(r'对应|按表头|按字段',remaining) else '按顺序'
    header='无表头' if re.search(r'无表头|不含表头|不带表头',remaining) else '首行表头'
    items=[]
    if paths:items.append({'type_id':'打开Excel','parameters':{'path':paths[0],'sheetName':sheet[1] if sheet else ''}})
    elif sheet:return {'type':'message','content':'指定工作表时请同时选定表格文件；否则使用当前已打开的工作表。'}
    if urls:items.append({'type_id':'打开网页','parameters':{'url':urls[0]}})
    items.append({'type_id':'表格填入网页','parameters':{'range':area[1].upper() if area else '', 'mode':mode,'header':header}})
    context.metadata['simple_fill_binding']={'source':'explicit_file' if paths else 'active_workbook','target':'explicit_url' if urls else 'active_browser','mode':mode}
    return {'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':items}}
