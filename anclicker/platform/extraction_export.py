"""Export extracted data without executing formulas or fetching remote media."""
import json
import os
import re
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

from anclicker.platform.table_layout_export import TableRows, word_table, excel_layout

EXTENSIONS = {'Word': '.docx', 'Excel': '.xlsx', 'TXT': '.txt'}

def clean(value):
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value if value is not None else '')
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff]', '', text)

def blocks(value):
    if isinstance(value, dict) and any(key in value for key in ('text','markdown','tables','titles','links','images','videos')):
        result = []
        title = value.get('title')
        if title: result.append(('标题', [[title]]))
        if value.get('url'): result.append(('来源', [[value['url']]]))
        if value.get('text') or value.get('markdown'): result.append(('正文', [[line] for line in clean(value.get('text') or value['markdown']).splitlines()]))
        for key, label in [('tables','表格'),('links','链接'),('images','图片'),('videos','视频'),('titles','标题信息')]:
            if value.get(key): result.extend([(label+' '+name, rows) for name, rows in blocks(value[key])])
        return result or [('内容', [['']])]
    if isinstance(value, dict) and 'rows' in value:
        return [(clean(value.get('caption') or '表格'), TableRows(([value['headers']] if value.get('headers') else []) + value['rows'], value.get('layout')))]
    if isinstance(value, list):
        if value and all(isinstance(item, dict) and 'rows' in item for item in value):
            return [block for item in value for block in blocks(item)]
        if value and all(isinstance(item, dict) for item in value):
            keys = list(dict.fromkeys(key for item in value for key in item))
            return [('列表', [keys] + [[item.get(key, '') for key in keys] for item in value])]
        return [('列表', [item if isinstance(item, (list,tuple)) else [item] for item in value])]
    if isinstance(value, dict): return [('内容', [['字段','内容']] + [[k,v] for k,v in value.items()])]
    return [('正文', [[line] for line in clean(value).splitlines()] or [['']])]

def write_docx(path, sections):
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    ET.register_namespace('w', ns)
    tag = lambda name: '{'+ns+'}'+name
    document = ET.Element(tag('document')); body = ET.SubElement(document,tag('body'))
    def paragraph(parent, text, bold=False):
        p=ET.SubElement(parent,tag('p'));r=ET.SubElement(p,tag('r'));pr=ET.SubElement(r,tag('rPr'))
        ET.SubElement(pr,tag('rFonts'),{tag('ascii'):'Calibri',tag('eastAsia'):'微软雅黑'})
        if bold:ET.SubElement(pr,tag('b'))
        ET.SubElement(r,tag('t'),{'{http://www.w3.org/XML/1998/namespace}space':'preserve'}).text=clean(text)
    for name, rows in sections:
        paragraph(body,name,True)
        if getattr(rows,'layout',None):
            word_table(body,rows,tag,clean)
        elif max((len(row) for row in rows),default=0)>1:
            table=ET.SubElement(body,tag('tbl'));props=ET.SubElement(table,tag('tblPr'))
            borders=ET.SubElement(props,tag('tblBorders'))
            for side in ('top','left','bottom','right','insideH','insideV'):
                ET.SubElement(borders,tag(side),{tag('val'):'single',tag('sz'):'4',tag('color'):'808080'})
            width=max(len(row) for row in rows)
            grid=ET.SubElement(table,tag('tblGrid'))
            for _ in range(width):ET.SubElement(grid,tag('gridCol'),{tag('w'):str(max(300,9000//width))})
            for row in rows:
                tr=ET.SubElement(table,tag('tr'))
                for item in list(row)+['']*(width-len(row)):
                    paragraph(ET.SubElement(tr,tag('tc')),item)
        else:
            for row in rows:paragraph(body,row[0] if row else '')
    sect=ET.SubElement(body,tag('sectPr'))
    ET.SubElement(sect,tag('pgSz'),{tag('w'):'11906',tag('h'):'16838'})
    ET.SubElement(sect,tag('pgMar'),{tag(k):'1134' for k in ('top','right','bottom','left')})
    with ZipFile(path,'w',ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr('word/document.xml',ET.tostring(document,encoding='utf-8',xml_declaration=True))

def write_xlsx(path, sections):
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell
    from openpyxl.styles import Alignment
    has_layout=any(getattr(rows,'layout',None) for _,rows in sections)
    book=Workbook(write_only=not has_layout)
    if has_layout:book.remove(book.active)
    for index,(name,rows) in enumerate(sections,1):
        name=re.sub(r'[\\/*?:\[\]]','_',name)
        sheet=book.create_sheet((str(index)+' '+name)[:31]);sheet.freeze_panes='A2'
        for row in rows:
            if len(row)==1:
                text=clean(row[0]); parts=[text[i:i+32000] for i in range(0,len(text),32000)] or ['']
                values=[[part] for part in parts]
            else:values=[row]
            for values_row in values:
                cells=[]
                for value in values_row:
                    text=clean(value)
                    if len(text)>32767:raise ValueError('表格单元格超过 Excel 的 32767 字符限制，请改存 Word 或 TXT。')
                    cell=WriteOnlyCell(sheet,value=text);cell.data_type='s';cell.alignment=Alignment(wrap_text=True,vertical='top');cells.append(cell)
                sheet.append(cells)
        if getattr(rows,'layout',None):excel_layout(sheet,rows.layout)
    book.save(path)

def write_positioned_xlsx(path, value):
    """Map viewport text rectangles to worksheet rows/columns in pixel order."""
    import math
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.utils import get_column_letter
    layout=value['layout']
    width=float(layout['width']);height=float(layout['height'])
    if not (math.isfinite(width) and math.isfinite(height) and 0<width<=20000 and 0<height<=20000):
        raise ValueError('网页区域尺寸无效，请重新提取')
    items=[]
    for item in layout.get('items',[]):
        coords=[float(item[key]) for key in ('x','y','w','h')]
        if not all(math.isfinite(n) for n in coords):raise ValueError('网页位置数据无效')
        x,y,w,h=coords
        if not clean(item.get('text','')).strip() or w<=0 or h<=0:continue
        if x<0 or y<0 or x>=width or y>=height:continue
        items.append(dict(item,x=x,y=y,w=min(w,width-x),h=min(h,height-y)))
    # Shared edges preserve whitespace, columns and line spacing without adding titles above the region.
    def edges(size, entries, start, extent, maximum):
        values={0.0,round(size,2)}
        for item in entries:values.update((round(item[start],2),round(item[start]+item[extent],2)))
        values=sorted(values)
        if len(values)>maximum:
            return [size*i/(maximum-1) for i in range(maximum)]
        return values
    xs=edges(width,items,'x','w',513);ys=edges(height,items,'y','h',2049)
    from bisect import bisect_left
    def index(values,point):
        i=bisect_left(values,point)
        if i and (i==len(values) or abs(values[i-1]-point)<=abs(values[i]-point)):i-=1
        return i+1
    book=Workbook();sheet=book.active;sheet.title='网页原位置';sheet.sheet_view.showGridLines=False
    for i,(left,right) in enumerate(zip(xs,xs[1:]),1):
        pixels=max(.5,right-left)
        sheet.column_dimensions[get_column_letter(i)].width=pixels/12 if pixels<=12 else (pixels-5)/7
    for i,(top,bottom) in enumerate(zip(ys,ys[1:]),1):sheet.row_dimensions[i].height=max(.5,(bottom-top)*.75)
    occupied={}
    for item in sorted(items,key=lambda item:(item['y'],item['x'])):
        col=index(xs,item['x']);row=index(ys,item['y'])
        last_col=max(col,index(xs,item['x']+item['w'])-1);last_row=max(row,index(ys,item['y']+item['h'])-1)
        keys=[(r,c) for r in range(row,last_row+1) for c in range(col,last_col+1)]
        anchors={occupied[key] for key in keys if key in occupied}
        text=clean(item['text'])
        if len(text)>32767:raise ValueError('单行文字超过 Excel 字数限制，请改存 TXT')
        if anchors:
            # Overlapping DOM fragments must not discard text or overwrite merged cells.
            anchor=min(anchors);cell=sheet.cell(*anchor);cell.value=clean(cell.value)+' '+text;cell.data_type='s'
            continue
        for key in keys:occupied[key]=(row,col)
        if last_row>row or last_col>col:sheet.merge_cells(start_row=row,start_column=col,end_row=last_row,end_column=last_col)
        cell=sheet.cell(row,col,text);cell.data_type='s'
        cell.font=Font(name='微软雅黑',size=max(6,min(72,float(item.get('fontSize',14))*.75)))
        cell.alignment=Alignment(horizontal='left',vertical='center',wrap_text=False)
    # A plain-text companion keeps all content readable even for overlapping page elements.
    text_sheet=book.create_sheet('提取内容');text_sheet.column_dimensions['A'].width=100
    for line in clean(value.get('text','')).splitlines():
        for offset in range(0,max(1,len(line)),32000):
            cell=text_sheet.cell(text_sheet.max_row+1 if text_sheet['A1'].value is not None else 1,1,line[offset:offset+32000]);cell.data_type='s'
    book.save(path)


def export_extracted(value, destination, kind, existing='自动更名'):
    if kind not in EXTENSIONS:raise ValueError('不支持的导出格式')
    if existing not in ('自动更名','覆盖','报错'):raise ValueError('不支持的重名处理方式')
    if not str(destination).strip():raise ValueError('请选择保存路径')
    target=Path(str(destination).strip()).expanduser()
    suffix=EXTENSIONS[kind]
    if not target.suffix:target=target.with_suffix(suffix)
    elif target.suffix.lower()!=suffix:raise ValueError('保存文件的扩展名必须为 '+suffix)
    if not target.parent.is_dir():raise ValueError('保存目录不存在，请选择已有文件夹')
    sections=blocks(value)
    fd,temporary=tempfile.mkstemp(prefix='.anclicker-export-',suffix=suffix,dir=target.parent);os.close(fd)
    temporary=Path(temporary)
    try:
        if kind=='Word':write_docx(temporary,sections)
        elif kind=='Excel':
            if isinstance(value,dict) and value.get('layout'):write_positioned_xlsx(temporary,value)
            else:write_xlsx(temporary,sections)
        else:temporary.write_text('\n\n'.join(name+'\n'+'\n'.join('\t'.join(clean(cell) for cell in row) for row in rows) for name,rows in sections),encoding='utf-8-sig')
        if existing=='覆盖':os.replace(temporary,target)
        else:
            original=target;number=1
            while True:
                try:os.link(temporary,target);break
                except FileExistsError:
                    if existing=='报错':raise FileExistsError('文件已存在：'+str(target))
                    target=original.with_name(original.stem+' ('+str(number)+')'+suffix);number+=1
        return str(target.resolve())
    finally:
        temporary.unlink(missing_ok=True)
