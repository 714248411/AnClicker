"""Load the exported GGUF through AnClicker's real converter interface; no actions run."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.dual_model import infer,configuration,conversion_schema,conversion_messages
from models.instruction_compiler import compiler_candidates
from models.desktop_contracts import grounded_instruction,grounded_schema
from models.agent_local import LocalModelManager
from unittest.mock import patch
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
out=ROOT/'models/anclicker-v6_4-dpo-r2-converter'
rows=json.loads((ROOT/'models/training/data_v6_4_dpo/generation-probes.json').read_text(encoding='utf8'))
config={**configuration(),'converter':'anclicker-v6_4-dpo-r2-converter-q4_0.gguf','serial_models':False}
service=LocalModelManager(ROOT/'artifacts/debug/v6_4_dpo_runtime',model_file=ROOT/'models'/config['converter'],runtime_dir=ROOT/'models')
settings=AgentSettings();settings.local_profile='cpu';context=ExecutionContext();results=[]
try:
 with patch('models.dual_model.manager',return_value=service):
  for r in [rows[i] for i in [0,1,2,4,6,7,10,11]]:
   names=compiler_candidates(r['user']);grounded=grounded_instruction(r['user'])
   schema=grounded_schema(*grounded) if grounded else conversion_schema(r['user'],names)
   messages=conversion_messages(r['user'],names,schema)
   value=infer('converter',messages,schema,settings,context,config)
   results.append({'user':r['user'],'expected':r['expected'],'actual':value,'pass':value==r['expected']})
   print(json.dumps(results[-1],ensure_ascii=False),flush=True)
finally:service.stop()
report={'passed':sum(r['pass'] for r in results),'total':len(results),'scope':'Real AnClicker inference plus JSON schema validation; no desktop actions executed.','results':results,'trace':context.metadata.get('dual_model_trace',[])}
(out/'anclicker-gguf-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if not all(r['pass'] for r in results):raise SystemExit(1)
