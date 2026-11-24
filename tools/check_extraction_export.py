import os,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='offscreen'
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from openpyxl import load_workbook
from anclicker.platform.extraction_export import export_extracted
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext,CommandRecord,InstructionDraft
from anclicker.platform.qt_compat.QtWidgets import QApplication
app=QApplication.instance() or QApplication([])
value=[{'caption':'测试表格','headers':['名称','内容'],'rows':[['中文','=1+1'],['第二行','测试 & < >']]}]
with tempfile.TemporaryDirectory() as td:
    for kind in ['Word','Excel','TXT']:
        name='提取转'+kind
        spec=get_instruction_spec(name)
        assert all(f.key!='变量' for f in spec.parameter_fields())
        command=CommandRecord(None,name,{'保存路径':str(Path(td)/kind),'文件已存在':'自动更名'})
        context=ExecutionContext()
        try:spec.create_executor().execute_once(context,command)
        except ValueError:pass
        else:raise AssertionError('Missing extraction should fail')
        context.metadata['last_web_extraction']=value
        path=Path(spec.create_executor().execute_once(context,command));assert path.is_file()
        second=Path(spec.create_executor().execute_once(context,command));assert second!=path
        if kind=='Excel':
            book=load_workbook(path);sheet=book.active
            assert sheet['B2'].value=='=1+1' and sheet['B2'].data_type=='s'
            assert sheet['A2'].value=='中文';book.close()
        elif kind=='Word':
            with ZipFile(path) as archive:
                for item in archive.namelist():ET.fromstring(archive.read(item))
                xml=archive.read('word/document.xml').decode();assert '中文' in xml and 'w:tbl' in xml
        else:assert '中文' in path.read_text(encoding='utf-8-sig')
        editor=spec.create_editor(draft=InstructionDraft(name,command.parameters),context=context)
        assert editor.get_draft().parameters['保存路径']==command.parameters['保存路径']
        assert len(editor._controls)==2
        editor.deleteLater()
    full={'title':'标题','text':'正文','url':'https://example.com','tables':value,'links':[{'url':'https://example.com','text':'示例'}]}
    for kind in ['Word','Excel','TXT']:export_extracted(full,Path(td)/('full'+kind),kind)
    try:export_extracted('x',Path(td)/'Word.docx','Word','报错')
    except FileExistsError:pass
    else:raise AssertionError('existing file should not be overwritten')
with tempfile.TemporaryDirectory() as td:
    positioned={'text':'左侧\n右侧\n下一行','layout':{'width':600,'height':240,'items':[
        {'text':'左侧','x':20,'y':30,'w':70,'h':20,'fontSize':16},
        {'text':'右侧','x':350,'y':30,'w':70,'h':20,'fontSize':16},
        {'text':'下一行','x':20,'y':150,'w':90,'h':20,'fontSize':16}]}}
    path=export_extracted(positioned,Path(td)/'位置.xlsx','Excel')
    book=load_workbook(path);sheet=book['网页原位置']
    found={cell.value:cell for row in sheet for cell in row if cell.value}
    assert found['左侧'].row==found['右侧'].row
    assert found['左侧'].column<found['右侧'].column
    assert found['下一行'].row>found['左侧'].row
    assert found['下一行'].column==found['左侧'].column
    assert found['左侧'].row>1 and found['左侧'].column>1
    assert len(sheet.merged_cells.ranges)>=1
    assert '提取内容' in book.sheetnames
    book.close()
print('PASS positions, automatic previous result, three registered editors, Word XML, Excel cells, TXT, collision handling')
