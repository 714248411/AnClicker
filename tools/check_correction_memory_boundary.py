import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner
from models.capability_retrieval import retrieve
from models.instruction_compiler import compiler_candidates
from models.dual_model import configuration
from anclicker.domain.instructions import ExecutionContext
OUT=ROOT/'artifacts/debug/correction-memory'
rows=json.loads((OUT/'retrieval-results.json').read_text(encoding='utf8'))+json.loads((OUT/'extra-results.json').read_text(encoding='utf8'));checked=[]
for row in rows:
 if 'correction-001' not in row['trace']['correction_ids']:continue
 c=ExecutionContext();names=retrieve(row['text'],compiler_candidates(row['text']),c,configuration())
 row['before_boundary_fix']=dict(row['trace']);row['trace']=c.metadata['capability_retrieval'][-1];row['hit']=bool(set(row['expected'])&set(names));checked.append(row['text'])
 print('RECHECK',row['hit'],row['text'],flush=True)
(OUT/'retrieval-final.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('FINAL',sum(r['hit'] for r in rows),len(rows),'rechecked',len(checked),flush=True)
