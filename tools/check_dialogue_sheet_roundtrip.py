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
OUT=ROOT/'artifacts/debug/dialogue-sheet';OUT.mkdir(parents=True,exist_ok=True)
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
bridge=RpaBridge('dialogue-sheet-acceptance');session=AgentSession(bridge);ctx=ExecutionContext();reports=[]
def task(text):
 events=[];session.run(text,AgentSettings(),ctx,lambda *a:events.append(a))
 row={'request':text,'events':events,'passed':False};reports.append(row)
 assert not session.pending_verification,session.pending_verification
 assert events[-1][0]=='assistant' and '试运行已执行' in events[-1][1],events
 row['passed']=True;print('PASS',text,flush=True)
try:
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge),patch('models.web_evidence.get_bridge',return_value=bridge):
  task(f'在表格“{source.as_posix()}”工作表“数据”的A2填入“王五”，B2填入“00123”，然后保存')
  disk=cells(source);assert disk['A2']['value']=='王五' and disk['B2']['value']=='00123',disk
  task(f'把当前表格按表头对应填入网页 {url}')
  actual=bridge.execute({'id':'getText','params':{'selector':'#result','by':'CSS选择器','varName':'actual'}})['result']
  expected=['00123','王五','$'+'{secret}','00007','李四',"O'Brien😀"]
  assert json.loads(actual)==expected,actual
  task(f'提取当前网页 CSS #result 的文字写入表格“{target.as_posix()}”工作表“结果”的C3')
  assert json.loads(cells(target)['C3']['value'])==expected
  task(f'提取当前网页 CSS .values 的全部文字写回表格“{target.as_posix()}”工作表“结果”的E1')
  disk=cells(target);assert [disk[a]['value'] for a in ['E1','E2','E3']]==['00123','=2+2','中文'];assert not disk['E2']['formula']
finally:
 bridge.close();server.shutdown();(OUT/'results.json').write_text(json.dumps({'cases':reports,'passed':sum(x['passed'] for x in reports)},ensure_ascii=False,indent=2),encoding='utf8')
print('DIALOGUE_SHEET_PASS',len(reports),flush=True)
