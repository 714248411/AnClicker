import sys,json
from pathlib import Path
sys.path.insert(0,'models/training')
from campaign_v65_worker import generate,judge,compact,write
from models.conversational_contracts import validate_model_output
sets={s:generate(651103+i*100,260,s) for i,s in enumerate(['train','selection','sealed'])}
for s,rows in sets.items():
 assert len(rows)==len({r['user'] for r in rows})
 for r in rows:
  e=r['expected'] if r['expected']!={'type':'message'} else {'type':'message','content':'请提供目标。'}
  validate_model_output(e,r['schema']);assert judge(r,compact(e))==(True,False)
assert not {r['user'] for r in sets['train']}.intersection(r['user'] for r in sets['selection']+sets['sealed'])
x=next(r for r in sets['train'] if r['family']=='copy');a=json.loads(compact(x['expected']));a['parameters']['操作']='移动';assert judge(x,compact(a))==(False,True)
x=next(r for r in sets['train'] if r['family']=='clarify');assert judge(x,'{"type_id":"打开网页","parameters":{"url":"https://invented.invalid"}}')==(False,True)
write('artifacts/training-campaign-v65-20261103/worker-smoke-cases.json',sets['train'][:8]);print('PASS dataset schemas, exact-user isolation, deduplication and critical-error scoring', {s:len(r) for s,r in sets.items()})
