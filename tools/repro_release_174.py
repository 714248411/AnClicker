import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
from models.dual_model import stop_dual
c=ExecutionContext()
try:
 r=plan_drafts('1. 打开文件“C:/Work/report.txt”\n2. 复制刚才打开的文件到“C:/Backup/report.txt”',AgentSettings(),c)
 print(json.dumps({'result':r,'trace':c.metadata},ensure_ascii=False,indent=2))
finally:stop_dual()
