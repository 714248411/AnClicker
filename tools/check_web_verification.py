import sys,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.web_evidence import matches
from models.agent_provider import AgentSettings
from anclicker.execution.agent_runtime import AgentSession
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.rpa_bridge import RpaBridge
s={'readyState':'complete','url':'https://www.baidu.com/s?wd=热点'}
assert matches({'kind':'web_search','query':'热点'},s)
for url in ['https://www.baidu.com/?wd=热点','https://www.baidu.com/s?wd=天气','https://evil.com/s?wd=热点']:
 assert not matches({'kind':'web_search','query':'热点'},{**s,'url':url})
assert not matches({'kind':'web_search','query':'热点'},{**s,'readyState':'loading'})
bridge=RpaBridge('web-verification-acceptance');session=AgentSession(bridge);events=[]
try:
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge),patch('models.web_evidence.get_bridge',return_value=bridge):
  session.run('打开百度，搜索热点',AgentSettings(),ExecutionContext(),lambda *a:events.append(a))
 assert not session.pending_verification,session.pending_verification
 assert len(session.drafts)==2,events
 evidence=[v for k,v in events if k=='verification_evidence']
 assert len(evidence)==2 and all(e['verified'] for e in evidence),events
 assert evidence[-1]['page']['search_query']=='热点' and evidence[-1]['page']['results_present'],evidence
 out=ROOT/'artifacts/debug/ui-trial/web-verification.json';out.write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf8')
 print('PASS real AgentSession: 2 executed steps, Baidu result URL verified; 4 negative state checks')
finally:bridge.close()
