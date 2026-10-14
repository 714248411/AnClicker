"""Dry evaluation of real model tool routing. Never executes returned tools."""
import argparse,json,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from agent_provider import AgentSettings,ModelClient
from instructions.models import ExecutionContext

def evaluate(client,cases):
    results=[]
    for case in cases:
        start=time.monotonic()
        try:
            response=client.chat(case['messages'],ExecutionContext())
            call=response['call']
            expected=case['expected']
            passed=(call is None if expected.get('type')=='message' else
                    bool(call and call['name']==expected['name'] and all(call['arguments'].get(k)==v for k,v in expected['arguments'].items())))
            result={'id':case['id'],'passed':passed,'response':call or response['text']}
        except Exception as error:result={'id':case['id'],'passed':False,'error':str(error)}
        result['seconds']=round(time.monotonic()-start,2);results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    return {'passed':sum(r['passed'] for r in results),'total':len(results),'results':results,
            'scope':'工具选择与参数离线评测，不代表浏览器多步任务成功率'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8766/v1');parser.add_argument('--model',default='anclicker-small')
    parser.add_argument('--backend',choices=['ollama','compatible'],default='compatible');parser.add_argument('--mode',choices=['json','native'],default='json')
    parser.add_argument('--cases',default=str(root/'docs/agent-eval-v1.jsonl'));parser.add_argument('--output',default=str(root/'validation/agent-model-eval.json'))
    args=parser.parse_args();cases=[json.loads(line) for line in Path(args.cases).read_text(encoding='utf-8').splitlines() if line.strip()]
    report=evaluate(ModelClient(AgentSettings(backend=args.backend,endpoint=args.url,model=args.model,mode=args.mode)),cases)
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if report['passed']==report['total'] else 1)
