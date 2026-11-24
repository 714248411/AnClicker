import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner
from models.correction_memory import family,binding,cases,guidance
from models.capability_retrieval import records,retrieve
from models.dual_model import conversion_messages,conversion_schema,validate_conversion
from models.instruction_compiler import compiler_candidates
from anclicker.domain.instructions import ExecutionContext
negative=['输入“给我朝下滚两格”','输入“按一下Esc退出来”','不要按Esc','别往下滚','把文字复制到剪贴板','清空剪贴板','把工作簿另存为新文件','把表格填到网页里','把鼠标拖到下面','把单元格往下挪','把这张表挨个填进网页的框','把表格内容填进网页搜索框']
for text in negative:assert family(text) is None,(text,family(text))
assert binding('朝上滚三格')[1]['距离']==3
assert binding('按一下Esc退出来')[1]['按键']=='esc'
assert len(cases())==9
before=json.dumps(records(False),ensure_ascii=False);after=json.dumps(records(True),ensure_ascii=False)
assert before!=after and '页面往底下挪一小段' in after and 'selector' not in json.dumps([x['query'] for x in cases()])
for text in ['页面往底下挪一小段','按一下Esc退出来','读一下剪贴板里的东西']:
 c=ExecutionContext();names=retrieve(text,compiler_candidates(text),c,{'embedding_enabled':False,'correction_memory_enabled':True});g=guidance(text,names)
 assert g and c.metadata['capability_retrieval'][-1]['correction_ids']
 messages=conversion_messages(text,names,conversion_schema(text,names),g)
 assert '已审核纠错参考' in messages[0]['content']
assert guidance('输入“页面往底下挪一小段”',['文本输入'])==[]
try:validate_conversion('页面往底下挪一小段',{'type_id':'获取文本','parameters':{'selector':'A1'}})
except ValueError:pass
else:raise AssertionError('invented selector accepted')
validate_conversion('搜索天气',{'type_id':'输入文本','parameters':{'selector':'#search','text':'天气'}},{'selector':'#search'})
c=ExecutionContext();c.stop_requested=True
try:retrieve('往下挪一小段',[],c,{'embedding_enabled':True})
except InterruptedError:pass
else:raise AssertionError('cancel swallowed')
print('CORRECTION_CONTRACTS_PASS',len(negative),'negative cases',flush=True)
