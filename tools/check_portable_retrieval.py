import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import draft_planner
from models.capability_retrieval import retrieve
from models.instruction_compiler import compiler_candidates
from models.dual_model import configuration
from anclicker.domain.instructions import ExecutionContext
OUT=ROOT/'artifacts/debug/v173-optimize/retrieval';extra=len(sys.argv)>1;cases=json.loads((OUT/('extra-cases.json' if extra else 'cases.json')).read_text(encoding='utf8'));rows=[]
for i,case in enumerate(cases,1):
 c=ExecutionContext();start=time.monotonic()
 try:
  baseline=compiler_candidates(case['text']);names=retrieve(case['text'],baseline,c,configuration());trace=c.metadata['capability_retrieval'][-1]
  row={**case,'hit':bool(set(case['expected'])&set(names)),'baseline_hit':bool(set(case['expected'])&set(baseline)),'trace':trace,'seconds':round(time.monotonic()-start,3)}
 except Exception as e:row={**case,'hit':False,'error':str(e)}
 rows.append(row);(OUT/('extra-results.json' if extra else 'retrieval-results.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(i,len(cases),row['hit'],case['text'],flush=True)
print('COMPLETED',sum(r['hit'] for r in rows),len(rows),flush=True)
