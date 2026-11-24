"""Exercise real rendered HTML -> bounded extraction -> both Office formats."""
import sys,threading,tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from zipfile import ZipFile
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.crawl4ai_bridge import crawl_page
from anclicker.platform.extraction_export import export_extracted,blocks
from openpyxl import load_workbook
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
  self.wfile.write('''<html><style>table{border-collapse:collapse;table-layout:fixed;width:480px}td,th{padding:12px 18px;font:16px/24px Arial;border:1px solid #aaa}tr{height:60px}tr:last-child{height:90px}</style><table id="test"><colgroup><col style="width:120px"><col style="width:360px"></colgroup><tr><th>项目</th><th>内容</th></tr><tr><td rowspan="2">合并</td><td>=1+1</td></tr><tr><td>最后一行</td></tr></table></html>'''.encode())
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 result=crawl_page('http://127.0.0.1:'+str(server.server_port),selector='#test')
 table=result['tables'][0];rows=blocks(table)[0][1];layout=rows.layout
 assert layout,table
 assert abs(layout['columns'][0]-120)<2 and abs(layout['columns'][1]-360)<2,layout
 assert layout['heights']==[60,60,90],layout
 assert layout['cells'][0]['padding']==[12,18,12,18]
 with tempfile.TemporaryDirectory() as tmp:
  xlsx=export_extracted([table],Path(tmp)/'table.xlsx','Excel')
  book=load_workbook(xlsx);sheet=book.active
  assert list(map(str,sheet.merged_cells.ranges))==['A2:A3']
  assert sheet['B2'].value=='=1+1' and sheet['B2'].data_type=='s'
  assert sheet.row_dimensions[3].height==67.5
  assert sheet.column_dimensions['B'].width>sheet.column_dimensions['A'].width*2
  book.close()
  docx=export_extracted([table],Path(tmp)/'table.docx','Word')
  with ZipFile(docx) as z:doc=ET.fromstring(z.read('word/document.xml'))
  ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};w='{'+ns['w']+'}'
  assert len(doc.findall('.//w:vMerge',ns))==2
  assert [e.get(w+'val') for e in doc.findall('.//w:trHeight',ns)]==['900','900','1350']
  assert doc.find('.//w:tcMar/w:top',ns).get(w+'w')=='180'
  assert doc.find('.//w:tcMar/w:left',ns).get(w+'w')=='270'
  print('PASS real browser dimensions, nonuniform columns/rows, padding, merged cells, Word spacing, Excel formula safety')
finally:server.shutdown()
