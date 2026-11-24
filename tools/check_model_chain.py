import sys,json,tempfile,threading,time
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner,dual_model
from models.capability_retrieval import retrieve
from models.instruction_compiler import compiler_candidates
from anclicker.domain.instructions import ExecutionContext
cases=[('往下翻一点','滚轮滑动'),('把现在的屏幕截下来','屏幕截图'),('把刚才改的表存一下','保存Excel'),('敲一下回车','按下键盘'),('按住鼠标拖过去','鼠标拖拽'),('把网页结果写回表里','提取文本到表格'),('把这段话敲进去','文本输入'),('提取图片上的字','OCR文字提取')]
rows=[]
for text,expected in cases:
 c=ExecutionContext();names=retrieve(text,compiler_candidates(text),c,{'embedding_enabled':False});assert expected in names,(text,names)
 schema=dual_model.conversion_schema(text,names)
 actual=[v['properties'].get('type_id',{}).get('const') for v in schema['oneOf']]
 assert expected in actual,(text,actual)
 rows.append({'request':text,'expected':expected,'trace':c.metadata['capability_retrieval']})
assert '按下键盘' not in retrieve('输入文字，不要回车',compiler_candidates('输入文字，不要回车'))
assert retrieve('计算文本“你好”的SHA256',compiler_candidates('计算文本“你好”的SHA256'))==['运行Python']
assert '运行cmd' not in retrieve('帮我随便弄一下',[])
assert '滚轮滑动' not in retrieve('输入“往下翻一点”',compiler_candidates('输入“往下翻一点”'))
ctx=ExecutionContext()
with patch('models.capability_retrieval._embedding',side_effect=ValueError('bad worker')):
 names=retrieve('往下翻一点',compiler_candidates('往下翻一点'),ctx,{'embedding_enabled':True})
 assert '滚轮滑动' in names
assert ctx.metadata['capability_retrieval'][0]['fallback']
s=dual_model.conversion_schema('打开网页',['时间等待'])
assert [v['properties'].get('type_id',{}).get('const') for v in s['oneOf']]==['时间等待',None]
try:
 dual_model.validate_conversion('把现在的屏幕截下来',{'type_id':'屏幕截图','parameters':{'保存路径':'目前未置信'}})
except ValueError:pass
else:raise AssertionError('invented screenshot path accepted')
# Serialize simultaneous roles and never stop an active request.
active=set();events=[]
class Fake:
 def __init__(self,name):self.name=name
 def stop(self):
  assert self.name not in active
  events.append(('stop',self.name))
 @contextmanager
 def lease(self,*args):
  assert not active;active.add(self.name);events.append(('start',self.name))
  try:yield 'fake'
  finally:active.remove(self.name);events.append(('end',self.name))
services={r:Fake(r) for r in ('splitter','converter')};errors=[]
def task(role):
 try:
  with dual_model.role_lease(role,ExecutionContext(),config={'serial_models':True}):time.sleep(.15)
 except BaseException as e:errors.append(repr(e))
with tempfile.TemporaryDirectory() as tmp,patch.object(dual_model,'runtime_root',return_value=Path(tmp)),patch.object(dual_model,'manager',side_effect=lambda r,c=None:services[r]):
 threads=[threading.Thread(target=task,args=(r,)) for r in ('splitter','converter')]
 for t in threads:t.start()
 for t in threads:t.join(5)
 assert not errors and all(not t.is_alive() for t in threads),(errors,events)
 cancelled=ExecutionContext();cancelled.stop_requested=True
 try:
  with dual_model.role_lease('splitter',cancelled,config={'serial_models':True}):raise AssertionError('cancel ignored')
 except InterruptedError:pass
(ROOT/'artifacts/debug/model-chain/contracts.json').write_text(json.dumps({'retrieval_cases':rows,'scheduler_events':events,'passed':True},ensure_ascii=False,indent=2),encoding='utf8')
print('CHAIN_CONTRACTS_PASS',flush=True)
