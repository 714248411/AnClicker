import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner
from models.capability_retrieval import _embedding,records
OUT=ROOT/'artifacts/debug/correction-memory'
rows=[]
for query,expected in [('页面往底下挪一小段','滚轮滑动'),('按一下Esc退出来','按下键盘'),('把这一页留个图片备份','网页截图'),('把剪贴板文字给我','获取剪切板')]:
 row={'query':query,'expected':expected}
 for enabled in (False,True):
  ranking=_embedding(query,json.dumps(records(enabled),ensure_ascii=False),str(ROOT/'.local/runtimes/training-gpu/venv/Scripts/python.exe'),str(ROOT/'models/embeddings/bge-small-zh-v1.5'),str(ROOT/'tools/capability_embedding_worker.py'),())
  row['with_memory' if enabled else 'without_memory']={'rank':ranking.index(expected)+1 if expected in ranking else None,'ranking':ranking}
 rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
(OUT/'vector-ablation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
