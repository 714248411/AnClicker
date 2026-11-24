import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest.mock import patch
from anclicker.domain.instructions import InstructionDraft
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_table import InstructionTableController
from anclicker.domain.flow_loop_table import loop_groups
from anclicker.platform.qt_compat.QtWidgets import QApplication
app=QApplication.instance() or QApplication([])
class Host(SimpleNamespace): pass
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'test.db'
 with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
 db.close()
 repo=GraphRepository(str(path))
 ids=repo.append_recording([InstructionDraft('时间等待',{'时长':0}) for _ in range(5)])
 nodes=[SimpleNamespace(node_id=str(i),command_id=i,type_id='循环' if i==ids[1] else '时间等待') for i in ids]
 edges=[SimpleNamespace(source=str(a),target=str(b),kind=k) for a,b,k in [(ids[0],ids[1],0),(ids[1],ids[2],3),(ids[2],ids[3],0),(ids[3],ids[1],0),(ids[1],ids[4],4)]]
 snapshot=SimpleNamespace(nodes=nodes,edges=edges)
 assert loop_groups(snapshot)=={ids[1]:{ids[2],ids[3]}}
 selected=[]
 workspace=Host(_table_mutation_allowed=lambda:True,_select_table_ids=lambda x:selected.extend(x),
    window=Host(workspace=Host(repository=repo,reload_graph=lambda *a:None,graphFinalized=Host(emit=lambda *a:None)),statusBar=Host(showMessage=lambda *a:None)))
 controller=InstructionTableController(workspace)
 with patch.object(repo,'snapshot',return_value=snapshot):
    controller.move_table_commands([ids[1]],5)
 assert [c.id for c in repo.list_commands()]==[ids[0],ids[4],ids[1],ids[2],ids[3]]
 assert selected==ids[1:4]
print('PASS: graph-derived loop header drag moves full body and preserves member order')
