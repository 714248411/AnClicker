import sys,os,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/debug/v173-optimize'
from tools.colloquial_expanded_judge import judge
exe=ROOT/'artifacts/dist/v1.7.3-ai-candidate/AnClicker/AnClicker.exe'
env=dict(os.environ);env.pop('ANCLICKER_AGENT_HOME',None);env['ANCLICKER_DATA_DIR']=str(OUT/'candidate-data')
result=subprocess.run([str(exe),'--language-validation',str(OUT/'language-cases.json'),str(OUT/'candidate-language.json')],cwd=exe.parent,env=env,timeout=600)
data=json.loads((OUT/'candidate-language.json').read_text(encoding='utf8'))
for row in data['cases']:
 errors=[row['error']] if 'error' in row else judge(row,row['response'])
 if 'distance' in row and not any(x['parameters'].get('距离')==row['distance'] for x in row.get('response',{}).get('arguments',{}).get('instructions',[])):errors.append('滚动格数不符')
 row.update(errors=errors,passed=not errors)
data['process_exit_code']=result.returncode
data['passed']=sum(r['passed'] for r in data['cases']);data['total']=len(data['cases'])
traces=[t for r in data['cases'] for t in r['trace'].get('capability_retrieval',[])]
data['hybrid_calls']=sum(t['method']=='hybrid' for t in traces);data['fallbacks']=[t for t in traces if t.get('fallback')]
(OUT/'candidate-language.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in data.items() if k!='cases'},ensure_ascii=False),flush=True)
sys.exit(0 if data['passed']==data['total'] and data['hybrid_calls']>0 and not data['fallbacks'] else 1)
