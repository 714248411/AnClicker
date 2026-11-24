import sys,json,os,subprocess,tempfile,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.9';APP=ROOT/'artifacts/dist/v1.8.9/AnClicker'
cases=[{'text':'帮我输入“测试通过”，先别按回车','expected':'文本输入'},{'text':'等待三秒','expected':'时间等待'}]
source=OUT/'v8-cases.json';target=OUT/'frozen-v8.json';source.write_text(json.dumps(cases,ensure_ascii=False),encoding='utf8')
with tempfile.TemporaryDirectory(prefix='ac-v8-frozen-') as folder:
 env=dict(os.environ,ANCLICKER_DATA_DIR=folder,ANCLICKER_SINGLETON_KEY=uuid.uuid4().hex)
 subprocess.run([str(APP/'AnClicker.exe'),'--language-validation',str(source),str(target)],cwd=folder,env=env,check=True,timeout=600)
report=json.loads(target.read_text(encoding='utf8'));assert report['version']=='v1.8.9'
assert report['configuration']['splitter_mode']=='pairwise'
roles=set()
for case in report['cases']:
 items=case['response']['arguments']['instructions'];assert len(items)==1 and items[0]['type_id']==case['expected'],case
 for row in case['trace']['dual_model_trace']:
  assert 'v8' in row['model'];roles.add(row['role'])
assert roles=={'splitter','converter'}
assert (APP/'integrations/yingdao/node_modules/ws/index.js').is_file()
print('PASS frozen v8 pairwise splitter, converter, planning and CDP WebSocket runtime',flush=True)
