import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext
cases=[('往下翻一点','滚轮滑动'),('敲一下回车','按下键盘'),('把现在的屏幕截下来','question')]
cases.append(('把现在的屏幕截下来\n用户补充：保存到“'+(ROOT/'artifacts/debug/model-chain/capture.png').as_posix()+'”','屏幕截图'))
rows=[]
try:
 for text,expected in cases:
  ctx=ExecutionContext();start=time.monotonic()
  try:
   result=plan_drafts(text,AgentSettings(local_profile='cpu'),ctx)
   items=result.get('arguments',{}).get('instructions',[])
   passed=(result.get('type')=='message' and '保存到哪里' in result.get('content','')) if expected=='question' else len(items)==1 and items[0]['type_id']==expected
   if expected=='屏幕截图':passed=passed and items[0]['parameters'].get('保存路径')==(ROOT/'artifacts/debug/model-chain/capture.png').as_posix()
   if expected=='滚轮滑动':passed=passed and not {'最小距离','最大距离'}.intersection(items[0]['parameters'])
   rows.append({'text':text,'passed':passed,'response':result,'trace':ctx.metadata,'seconds':round(time.monotonic()-start,2)})
  except Exception as e:rows.append({'text':text,'passed':False,'error':str(e),'trace':ctx.metadata})
  print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
finally:
 stop_dual();(ROOT/'artifacts/debug/model-chain/new-language.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
assert all(r['passed'] for r in rows)
print('NEW_LANGUAGE_PASS',len(rows),flush=True)
