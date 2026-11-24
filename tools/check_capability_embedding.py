"""Real offline embeddings, hybrid recall and cache verification (no inference mocks)."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner
from models.capability_retrieval import retrieve,_embedding
from models.instruction_compiler import compiler_candidates
from anclicker.domain.instructions import ExecutionContext
cases=[('页面往底下挪一小段','滚轮滑动'),('把图上的汉字读出来','OCR文字提取'),('把这一页留个图片备份','网页截图'),('把刚复制的那段话拿出来','获取剪切板'),('让鼠标按住拉到另一处','鼠标拖拽'),('表里的几行对应填到页面空格里','表格填入网页'),('页面显示的那段结果写进工作簿','提取文本到表格'),('在这个框里打几个字','文本输入')]
rows=[]
for text,expected in cases:
 c=ExecutionContext();start=time.monotonic();names=retrieve(text,compiler_candidates(text),c,{'embedding_enabled':True});trace=c.metadata['capability_retrieval'][-1]
 row={'text':text,'expected':expected,'seconds':round(time.monotonic()-start,3),'candidate_hit':expected in names,'trace':trace};rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
 assert trace['method']=='hybrid' and not trace['fallback'],row
# Repeated requests must use the in-process query cache.
text=cases[-1][0];before=_embedding.cache_info().hits;c=ExecutionContext();start=time.monotonic();retrieve(text,compiler_candidates(text),c,{'embedding_enabled':True});elapsed=time.monotonic()-start
assert _embedding.cache_info().hits>before
result={'total':len(rows),'hybrid_success':len(rows),'candidate_hits':sum(r['candidate_hit'] for r in rows),'cached_query_seconds':round(elapsed,4),'cases':rows}
(ROOT/'artifacts/debug/model-chain/embedding-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('EMBEDDING_VALIDATED',json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True)
