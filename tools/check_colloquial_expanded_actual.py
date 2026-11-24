"""Real dialogue -> RPA -> browser and saved workbook readback."""
import sys,json,threading,shutil,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.agent_provider import AgentSettings
from anclicker.execution.agent_runtime import AgentSession
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.rpa_bridge import RpaBridge
OUT=ROOT/'artifacts/debug/colloquial-expanded/actual';OUT.mkdir(parents=True,exist_ok=True)
source=OUT/'input.xlsx';target=OUT/'output.xlsx'
shutil.copy2(ROOT/'artifacts/debug/simple-language/source.xlsx',source)
HTML='''<!doctype html><meta charset="utf-8"><title>表格双向实测</title>'''+''.join('<label>'+name+'<input value="原值"></label>' for name in ['编号','姓名','备注']*2)+'''<pre id="result"></pre><div class="values">00123</div><div class="values">=2+2</div><div class="values">中文</div><script>function sync(){document.querySelector('#result').textContent=JSON.stringify(Array.from(document.querySelectorAll('input')).map(e=>e.value));}document.addEventListener('input',sync);sync();</script>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(body)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
def cells(path,sheet_index=1):
 ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 with zipfile.ZipFile(path) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',ns)]
  data={}
  for c in ET.fromstring(z.read(f'xl/worksheets/sheet{sheet_index}.xml')).findall('.//x:c',ns):
   v=c.find('x:v',ns);value=v.text if v is not None else ''
   if c.get('t')=='s':value=strings[int(value)]
   if c.get('t')=='inlineStr':value=''.join(c.find('x:is',ns).itertext())
   data[c.get('r')]={'value':value,'type':c.get('t'),'formula':c.find('x:f',ns) is not None}
  return data

bridge=RpaBridge('colloquial-sheet');session=AgentSession(bridge);reports=[]
def task(text,session=session):
 events=[];session.run(text,AgentSettings(),ExecutionContext(),lambda *a:events.append(a))
 reports.append({'request':text,'events':events});assert not session.pending_verification,session.pending_verification
 return events
try:
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge),patch('models.colloquial_sheet.get_bridge',return_value=bridge),patch('models.web_evidence.get_bridge',return_value=bridge):
  bridge.execute({'id':'excelOpen','params':{'path':source.as_posix(),'sheetName':'数据'}})
  e=task('姓名改成王五，号码不要改');assert '哪一行' in e[-1][1] and not session.drafts,e
  e=task('就张三那一行');assert '试运行已执行' in e[-1][1],e
  values=bridge.execute({'id':'excelReadRange','params':{'range':'A1:C3','varName':'readback'}})['variables']['readback']
  assert values[1]==['王五','00123','$'+'{secret}'] and values[2]==['李四','00007',"O'Brien😀"],values
  e=task('存起来');assert '试运行已执行' in e[-1][1] and cells(source)['A2']['value']=='王五',e
  bridge.execute({'id':'openUrl','params':{'url':url}})
  e=task('将当前表格的内容填入网页中，按名称填');assert '试运行已执行' in e[-1][1],e
  actual=bridge.execute({'id':'getText','params':{'selector':'#result','by':'CSS选择器','varName':'actual'}})['result']
  assert json.loads(actual)==['00123','王五','$'+'{secret}','00007','李四',"O'Brien😀"],actual
  for text,word in [('其他的也照刚才那样填','剩余行'),('把网页的结果写回那张表','哪块结果')]:
   fresh=AgentSession(bridge);e=task(text,fresh);assert word in e[-1][1] and not fresh.drafts,e
  fresh=AgentSession(bridge);e=task('名字改成赵六，编号别动',fresh);assert '哪一行' in e[-1][1]
  other=OUT/'other.xlsx';shutil.copy2(source,other);bridge.execute({'id':'excelOpen','params':{'path':other.as_posix(),'sheetName':'数据'}})
  e=task('王五那行',fresh);assert '切换' in e[-1][1] and not fresh.drafts,e
  from models.dual_model import validate_conversion
  try:validate_conversion('把表格填到网页',{'type_id':'打开网页','parameters':{'url':'表格'}})
  except ValueError:pass
  else:raise AssertionError('invalid URL accepted')
 print('PASS: real follow-up row edit, untouched IDs, save, field-matched webpage fill, two targeted clarifications, switched-workbook rejection, invalid URL rejection',flush=True)
finally:
 bridge.close();server.shutdown();(OUT/'after.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
