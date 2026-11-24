import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups, group_title
from anclicker.storage.graph_repository import GraphRepository
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.qt_compat.QtWidgets import QApplication
app=QApplication.instance() or QApplication([])
spec=get_instruction_spec('折叠步骤')
assert spec.display_name=='折叠以下指令'
editor=spec.create_editor()
editor.by_count.setChecked(False); editor.by_range.setChecked(True); editor.ranges.setValue(3)
draft=editor.get_draft()
assert draft.parameters['动态范围'] and draft.parameters['终止步骤']==3
for locked in (False,):
 with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'test.db'
    with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
    db.close()
    repo=GraphRepository(str(path))
    draft.parameters['整体锁定']=locked
    ids=repo.append_recording([draft]+[InstructionDraft('时间等待',{'时长':0}) for _ in range(4)])
    def members(): return folding_groups(repo.list_commands())[ids[0]]['members']
    assert members()==set(ids[1:3])
    new=repo.insert_table_commands([InstructionDraft('时间等待',{'时长':0})],before_command_id=ids[2])[0]
    assert members()=={ids[1],ids[2],new}
    assert repo.get_command(ids[0]).parameters['终止步骤']==4
    # Inserting outside the interval shifts row numbers, not membership.
    before=repo.insert_table_commands([InstructionDraft('时间等待',{'时长':0})],before_command_id=ids[0])[0]
    assert members()=={ids[1],ids[2],new}
    repo.delete_commands([ids[2]])
    assert members()=={ids[1],new}
    order=[before, ids[3], ids[4], ids[0], ids[1], new]
    repo.reorder_table_commands(order)
    assert members()=={ids[1],new}
    assert repo.get_command(ids[0]).parameters['终止步骤']==6
    repo.delete_commands([ids[1],new])
    assert members()==set()
    assert '折叠1（0 条）' in group_title(folding_groups(repo.list_commands())[ids[0]])
editor.close()
print('PASS: renamed editor, contiguous endpoint, dynamic insert/delete/move, unlocked and empty groups (locked boundaries covered separately)')
