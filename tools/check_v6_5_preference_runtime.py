import sys,json,argparse,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.dual_model import infer,configuration,conversion_schema,conversion_messages,validate_conversion
from models.instruction_compiler import compiler_candidates
from models.desktop_contracts import grounded_instruction,grounded_schema
from models.agent_local import LocalModelManager
from models.agent_provider import AgentSettings,request_json
from anclicker.domain.instructions import ExecutionContext
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--report',required=True);args=ap.parse_args()
config={**configuration(),'converter':args.model,'serial_models':False}
service=LocalModelManager(ROOT/'artifacts/debug/v6_5_runtime_check'/Path(args.model).stem,model_file=ROOT/'models'/args.model,runtime_dir=ROOT/'models')
rows=json.loads((ROOT/'models/training/data_v6_4_dpo/generation-probes.json').read_text(encoding='utf8'));results=[];trace=[]
def bounded(url,payload,settings,context):
 payload={**payload,'max_tokens':300};return request_json(url,payload,settings,context)
try:
 with patch('models.dual_model.manager',return_value=service),patch('models.dual_model.request_json',side_effect=bounded):
  for r in rows[:12]:
   ctx=ExecutionContext();start=time.monotonic();row={'user':r['user'],'expected':r['expected']}
   try:
    names=compiler_candidates(r['user']);ground=grounded_instruction(r['user']);schema=grounded_schema(*ground) if ground else conversion_schema(r['user'],names)
    messages=conversion_messages(r['user'],names,schema);value=infer('converter',messages,schema,AgentSettings(local_profile='cpu'),ctx,config)
    row['actual']=value;row['pass']=value==r['expected'];row['candidates']=names
    if value.get('type_id'):
     try:validate_conversion(r['user'],value);row['source_guard']='accepted'
     except Exception as e:row['source_guard']='rejected: '+str(e);row['pass']=False
   except Exception as e:row.update({'pass':False,'error':str(e)})
   row['seconds']=round(time.monotonic()-start,2);results.append(row);trace.extend(ctx.metadata.get('dual_model_trace',[]))
   report={'model':args.model,'passed':sum(r['pass'] for r in results),'total':len(results),'max_tokens':300,'scope':'Actual AnClicker GGUF inference with current patched routing, schema and source validation; no actions executed.','results':results,'trace':trace}
   Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(row,ensure_ascii=False),flush=True)
finally:service.stop()
print('RUNTIME_CHECK_COMPLETE',flush=True)
