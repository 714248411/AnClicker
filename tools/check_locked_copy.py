import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys, sqlite3, tempfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import copy_group_drafts, folding_groups
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.instruction_table import InstructionTableController
from anclicker.platform.qt_compat.QtWidgets import QApplication
app=QApplication.instance() or QApplication([])
class Host(SimpleNamespace): pass
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'copy.db'
 with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
 db.close()
 repo=GraphRepository(str(path))
 fold=lambda end:InstructionDraft('折叠步骤',{'整体锁定':True,'已折叠':True,'动态范围':True,'按条数':False,'按范围':True,'终止步骤':end})
 ids=repo.append_recording([fold(4),fold(4),InstructionDraft('时间等待',{'时长':2},note='a'),InstructionDraft('时间等待',{'时长':3},note='b'),InstructionDraft('时间等待',note='outside')])
 before=repo.snapshot()
 for selected in ([ids[0]],[ids[2]],[ids[0],ids[1],ids[3]]):
    drafts=copy_group_drafts(repo.list_commands(),selected)
    assert len(drafts)==4
    assert [d.note for d in drafts]==['','','a','b']
 assert repo.snapshot()==before
 workspace=Host(command_table=Host(selected_command_ids=lambda:[ids[2]]),window=Host(workspace=Host(repository=repo),statusBar=Host(showMessage=lambda *a:None)))
 InstructionTableController(workspace).copy_table_commands()
 payload=json.loads(bytes(app.clipboard().mimeData().data('application/x-anclicker-commands')))
 assert len(payload)==4
 drafts=[InstructionDraft.from_mapping(item) for item in payload]
 pasted=repo.insert_table_commands(drafts,before_command_id=ids[4])
 groups=folding_groups(repo.list_commands())
 assert groups[pasted[0]]['members']==set(pasted[1:])
 assert groups[pasted[1]]['members']==set(pasted[2:])
 errors=[]
 host=Host(repository=repo,reload_graph=lambda *a:None,editor=Host(view=Host(register_copied_group=lambda *a:None)),graphFinalized=Host(emit=lambda *a:None),statusMessage=Host(emit=lambda *a:None),_show_error=lambda *a:errors.append(a))
 copied=InstructionWorkspace.copy_commands(host,[ids[0]])
 assert not errors,errors
 assert len(copied)==4
 groups=folding_groups(repo.list_commands())
 assert groups[copied[0]]['members']==set(copied[1:])
 assert groups[copied[1]]['members']==set(copied[2:])
 assert groups[ids[0]]['members']==set(ids[1:4])
 assert len(copy_group_drafts(repo.list_commands(),[ids[4]]))==1
app.clipboard().clear()
app.processEvents()
print('PASS: table clipboard and graph group copy, hidden/nested members, deduplication, paste ranges and original unchanged')
