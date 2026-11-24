"""Translate bounded browser CSS-pixel table geometry into editable Office tables."""
import math
from xml.etree import ElementTree as ET

class TableRows(list):
    def __init__(self, rows, layout=None):
        super().__init__(rows)
        self.layout=validated(layout, self)

def validated(layout, rows):
    if not isinstance(layout,dict):return None
    try:
        def number(v, maximum=20000):
            v=float(v)
            if not math.isfinite(v) or not 0<=v<=maximum:raise ValueError()
            return v
        columns=[number(v) for v in layout['columns']]
        heights=[number(v) for v in layout['heights']]
        if not 0<len(columns)<=50 or not 0<len(heights)<=100 or len(heights)!=len(rows):return None
        if len(columns)!=max(map(len,rows),default=0) or min(columns)<=0:return None
        cells=[];occupied=set()
        for source in layout['cells']:
            r,c,rs,cs=[int(source[k]) for k in ('row','col','rowspan','colspan')]
            if r<0 or c<0 or rs<1 or cs<1 or r+rs>len(rows) or c+cs>len(columns):return None
            keys={(i,j) for i in range(r,r+rs) for j in range(c,c+cs)}
            if occupied & keys:return None
            occupied.update(keys)
            padding=[number(v,2000) for v in source.get('padding',[0]*4)]
            if len(padding)!=4:return None
            cells.append(dict(row=r,col=c,rowspan=rs,colspan=cs,padding=padding,
                fontSize=max(1,number(source.get('fontSize',14),512)),
                lineHeight=max(1,number(source.get('lineHeight',18),2000)),
                fontFamily=str(source.get('fontFamily','微软雅黑'))[:100],bold=bool(source.get('bold',False)),
                align=source.get('align','left'),vertical=source.get('vertical','top')))
        if len(occupied)!=len(rows)*len(columns):return None
        return dict(columns=columns,heights=heights,cells=cells)
    except (KeyError,ValueError,TypeError,OverflowError):return None

def excel_layout(sheet, layout):
    from openpyxl.styles import Alignment,Font
    from openpyxl.utils import get_column_letter
    for i,pixels in enumerate(layout['columns'],1):
        sheet.column_dimensions[get_column_letter(i)].width=pixels/12 if pixels<=12 else (pixels-5)/7
    for i,pixels in enumerate(layout['heights'],1):sheet.row_dimensions[i].height=min(409,max(1,pixels*.75))
    for spec in layout['cells']:
        r,c=spec['row']+1,spec['col']+1
        if spec['rowspan']>1 or spec['colspan']>1:
            sheet.merge_cells(start_row=r,start_column=c,end_row=r+spec['rowspan']-1,end_column=c+spec['colspan']-1)
        cell=sheet.cell(r,c)
        cell.font=Font(name=spec['fontFamily'],size=spec['fontSize']*.75,bold=spec['bold'])
        align={'start':'left','end':'right','-webkit-center':'center'}.get(spec['align'],spec['align'])
        vertical={'middle':'center'}.get(spec['vertical'],spec['vertical'])
        cell.alignment=Alignment(horizontal=align if align in ('left','right','center','justify') else 'left',
            vertical=vertical if vertical in ('top','bottom','center') else 'top',wrap_text=True,
            indent=min(250,round(spec['padding'][3]/max(1,spec['fontSize']*1.5))))

def word_table(body, rows, tag, clean):
    layout=rows.layout
    scale=min(1,9638/(sum(layout['columns'])*15))
    twips=lambda v:str(max(0,round(v*15*scale)))
    table=ET.SubElement(body,tag('tbl'));props=ET.SubElement(table,tag('tblPr'))
    ET.SubElement(props,tag('tblW'),{tag('w'):twips(sum(layout['columns'])),tag('type'):'dxa'})
    ET.SubElement(props,tag('tblLayout'),{tag('type'):'fixed'})
    borders=ET.SubElement(props,tag('tblBorders'))
    for side in ('top','left','bottom','right','insideH','insideV'):
        ET.SubElement(borders,tag(side),{tag('val'):'single',tag('sz'):'4',tag('color'):'D6DAE1'})
    grid=ET.SubElement(table,tag('tblGrid'))
    for width in layout['columns']:ET.SubElement(grid,tag('gridCol'),{tag('w'):twips(width)})
    owners={}
    for spec in layout['cells']:
        for row in range(spec['row'],spec['row']+spec['rowspan']):owners[row,spec['col']]=spec
    for ri,row in enumerate(rows):
        tr=ET.SubElement(table,tag('tr'));rp=ET.SubElement(tr,tag('trPr'))
        ET.SubElement(rp,tag('trHeight'),{tag('val'):twips(layout['heights'][ri]),tag('hRule'):'atLeast'})
        for ci in range(len(layout['columns'])):
            spec=owners.get((ri,ci))
            if spec is None:continue
            tc=ET.SubElement(tr,tag('tc'));pr=ET.SubElement(tc,tag('tcPr'))
            ET.SubElement(pr,tag('tcW'),{tag('w'):twips(sum(layout['columns'][ci:ci+spec['colspan']])),tag('type'):'dxa'})
            if spec['colspan']>1:ET.SubElement(pr,tag('gridSpan'),{tag('val'):str(spec['colspan'])})
            if spec['rowspan']>1:ET.SubElement(pr,tag('vMerge'),{tag('val'):'restart' if ri==spec['row'] else 'continue'})
            margins=ET.SubElement(pr,tag('tcMar'))
            for side,pixels in zip(('top','right','bottom','left'),spec['padding']):
                ET.SubElement(margins,tag(side),{tag('w'):twips(pixels),tag('type'):'dxa'})
            ET.SubElement(pr,tag('vAlign'),{tag('val'):{'middle':'center','bottom':'bottom'}.get(spec['vertical'],'top')})
            p=ET.SubElement(tc,tag('p'));pp=ET.SubElement(p,tag('pPr'))
            align={'start':'left','end':'right','justify':'both'}.get(spec['align'],spec['align'])
            ET.SubElement(pp,tag('jc'),{tag('val'):align if align in ('left','right','center','both') else 'left'})
            ET.SubElement(pp,tag('spacing'),{tag('before'):'0',tag('after'):'0',tag('line'):twips(spec['lineHeight']),tag('lineRule'):'atLeast'})
            run=ET.SubElement(p,tag('r'));runpr=ET.SubElement(run,tag('rPr'))
            ET.SubElement(runpr,tag('rFonts'),{tag('ascii'):spec['fontFamily'],tag('eastAsia'):spec['fontFamily'],tag('hAnsi'):spec['fontFamily']})
            ET.SubElement(runpr,tag('sz'),{tag('val'):str(max(2,round(spec['fontSize']*1.5*scale)))})
            if spec['bold']:ET.SubElement(runpr,tag('b'))
            value=clean(row[ci]) if ri==spec['row'] else ''
            for i,line in enumerate(value.split('\n')):
                if i:ET.SubElement(run,tag('br'))
                ET.SubElement(run,tag('t'),{'{http://www.w3.org/XML/1998/namespace}space':'preserve'}).text=line
