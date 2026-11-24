import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups, hidden_steps
from anclicker.storage.graph_repository import GraphRepository
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'test.db'
 with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
 db.close()
 repo=GraphRepository(str(path))
 fold=lambda n:InstructionDraft('折叠步骤',{'下方条数':n,'已折叠':False})
 ids=repo.append_recording([fold(1),fold(1),fold(2),InstructionDraft('时间等待'),InstructionDraft('时间等待'),fold(1),InstructionDraft('时间等待')])
 for child_state in (False,True):
  repo.set_step_collapsed(ids[2],child_state)
  before={c.id:c.parameters for c in repo.list_commands() if c.id!=ids[0]}
  repo.set_step_collapsed(ids[0],True)
  groups=folding_groups(repo.list_commands())
  assert hidden_steps(groups)==set(ids[1:5])
  assert {c.id:c.parameters for c in repo.list_commands() if c.id!=ids[0]}==before
  repo=GraphRepository(str(path))
  repo.set_step_collapsed(ids[0],False)
  groups=folding_groups(repo.list_commands())
  assert not groups[ids[0]]['collapsed'] and not groups[ids[1]]['collapsed']
  assert groups[ids[2]]['collapsed']==child_state
  assert hidden_steps(groups)==(set(ids[3:5]) if child_state else set())
  assert not groups[ids[5]]['collapsed']
print('PASS: outer collapse hides descendants, preserves mixed child states and restores after reopen')
