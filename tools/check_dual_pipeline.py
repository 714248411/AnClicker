"""Dual role boundaries, source fidelity, edit transactions and role isolation."""
from unittest.mock import patch
from copy import deepcopy
from models.dual_model import clauses,split_task,plan,validate_conversion,manager,DEFAULT
from models.agent_provider import AgentSettings
from models.workflow_ast import from_drafts
from anclicker.domain.instructions import ExecutionContext
from anclicker.domain.agent_protocol import make_draft

@patch('models.dual_model.configuration', return_value=dict(DEFAULT, splitter_mode='whole'))
def main(_configuration):
 settings=AgentSettings();context=ExecutionContext()
 parts,_=clauses('输入“然后，再等两秒”，不要回车，然后等待三秒')
 assert parts==['输入“然后，再等两秒”','不要回车','等待三秒']
 with patch('models.dual_model.infer',return_value={'boundaries':[False,True]}):
  assert split_task('输入“然后，再等两秒”，不要回车，然后等待三秒',settings,context)==['输入“然后，再等两秒”，不要回车','等待三秒']
 with patch('models.dual_model.infer',return_value={'boundaries':[]}):
  assert split_task('第二步的等待改成5秒',settings,context,editing=True)==['第二步的等待改成5秒']
 ast=from_drafts([make_draft('时间等待',{'时长':1}),make_draft('时间等待',{'时长':2})],3)
 original=deepcopy(ast)
 replies=[{'boundaries':[]},{'base_revision':3,'operations':[{'op':'update','target':'n2','parameters':{'时长':7}}]}]
 with patch('models.dual_model.infer',side_effect=replies) as infer:
  result=plan('把第2步等待改成7秒',settings,ExecutionContext(),ast=ast)
  assert [c.args[0] for c in infer.call_args_list]==['splitter','converter']
 assert result['name']=='workflow_patch' and ast==original
 replies=[{'boundaries':[]},{'base_revision':3,'operations':[{'op':'delete','target':'n1'}]}]
 with patch('models.dual_model.infer',side_effect=replies):
  try:plan('删除第2步',settings,ExecutionContext(),ast=ast)
  except ValueError:pass
  else:raise AssertionError('Wrong target accepted')
 for item in [{'type_id':'快速文件操作','parameters':{'操作':'打开','源路径':'C:/wrong'}},{'type_id':'时间等待','parameters':{'时长':3000,'单位':'秒'}}]:
  try:validate_conversion('等待三秒',item)
  except ValueError:pass
  else:raise AssertionError('Invented parameter accepted')
 from pathlib import Path
 import json
 current={**DEFAULT,**json.loads((Path(__file__).resolve().parents[1]/'models/recommended_dual_model.json').read_text())}
 a=manager('splitter',current);b=manager('converter',current)
 assert a.root!=b.root and a.runtime_dir==b.runtime_dir and a.model_file!=b.model_file
 with patch('models.dual_model.infer',side_effect=[{'new_action':False},{'new_action':True}]):
  assert split_task('输入“然后，再等两秒”，不要回车，然后等待三秒',settings,ExecutionContext(),config=dict(DEFAULT,splitter_mode='pairwise'))==['输入“然后，再等两秒”，不要回车','等待三秒']
 print('PASS quote/negation grouping, edit numbering, whole-request edit transactions, wrong-target veto, literal checks and separate runtime locks')
if __name__=='__main__':main()
