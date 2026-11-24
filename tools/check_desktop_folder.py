"""User's natural folder request must bypass model path guessing."""
import sys,tempfile
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.system_actions import parse_file_task
from models.draft_planner import plan_drafts
from models.draft_verification import verify_plan
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
with tempfile.TemporaryDirectory() as folder:
 base=Path(folder)
 for name in ['111','我的项目','新建','新建文件夹','文件夹资料','资料文件夹','文件夹','年度报告文件夹 (2)']:(base/name).mkdir()
 with patch('models.local_paths.known_folder',return_value=base):
  for text in ['打开桌面文件夹111','打开桌面上的111文件夹','请打开桌面的“111”文件夹','帮我打开桌面111','打开桌面文件夹我的项目']:
   result=parse_file_task(text);assert result and Path(result['source']).is_dir(),text
  assert parse_file_task('打开桌面')['source']==str(base.resolve())
  for phrase,name in [('打开桌面的新建文件夹','新建文件夹'),('打开桌面上的新建文件夹','新建文件夹'),('打开桌面文件夹新建文件夹','新建文件夹'),('打开桌面的“新建文件夹”文件夹','新建文件夹'),('打开桌面的文件夹资料','文件夹资料'),('打开桌面资料文件夹','资料文件夹'),('打开桌面的“文件夹”','文件夹'),('打开桌面的年度报告文件夹 (2)','年度报告文件夹 (2)')]:
   assert parse_file_task(phrase)['source']==str((base/name).resolve()),phrase
   with patch('models.draft_planner._dual.load',side_effect=AssertionError('known folder must bind before model routing')):
    result=plan_drafts(phrase,AgentSettings(),ExecutionContext())
   assert result['arguments']['instructions'][0]['parameters']['源路径']==str((base/name).resolve()),phrase
  for text in ['不要打开桌面111','打开桌面文件夹../111','打开桌面111然后删除文件','如果存在就打开桌面111']:assert parse_file_task(text) is None,text
  try:parse_file_task('打开桌面文件夹不存在')
  except ValueError as error:assert '没有找到文件夹' in str(error)
  else:raise AssertionError('missing folder guessed')
  with patch('models.draft_planner.request_json',side_effect=AssertionError('must not invoke planner')):
   plan=plan_drafts('打开桌面文件夹111',AgentSettings(),ExecutionContext())
   assert plan['arguments']['instructions'][0]['parameters']['源路径']==str((base/'111').resolve())
  with patch('models.draft_verification.get_instruction_spec') as spec,patch('models.draft_verification.judge_ocr',return_value={'passed':True,'reason':'111'}):
   spec.return_value.create_executor.return_value.execute.return_value={'visual_verification':{'verified':True,'text':'111','expected_text':['111']}}
   result=verify_plan('打开桌面文件夹111',plan['arguments']['instructions'],AgentSettings(),ExecutionContext(),lambda *a:None)
   assert result['passed'] and result['executed']==1
print('PASS desktop Chinese phrases, Unicode names, missing/negated paths, no model path guessing, automatic OCR gate')
