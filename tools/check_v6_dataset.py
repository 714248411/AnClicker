"""Validate every SFT target against the real instruction registry and patch merger."""
import json
from pathlib import Path
from models.workflow_ast import edges,apply_patch
from anclicker.domain.agent_protocol import make_draft
ROOT=Path(__file__).resolve().parents[1]
count=0
for path in (ROOT/'models/training/data_v6').glob('*/*.jsonl'):
 for line in path.read_text(encoding='utf8').splitlines():
  row=json.loads(line);messages=row['messages'];result=json.loads(messages[-1]['content'])
  if path.parent.name=='splitter':
   parts=json.loads(messages[-2]['content']);assert len(result['boundaries'])==len(parts)-1
   assert all(type(c) is bool for c in result['boundaries'])
  elif 'operations' in result:
   ast=json.loads(messages[-2]['content'])['ast'];ast['edges']=edges(ast['nodes']);apply_patch(ast,result)
  elif 'type_id' in result:make_draft(result['type_id'],result['parameters'])
  else:assert result['type']=='message' and result['content']
  count+=1
print('PASS all',count,'SFT targets match boundary counts, real schemas and transactional patches')
