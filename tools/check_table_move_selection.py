"""Lock hit testing, persistence and atomic grouped reorder regressions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace, MethodType
from anclicker.domain.instructions import InstructionDraft, CommandRecord
from anclicker.domain.step_folding import folding_groups, locked_move_ids
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController, FOLD_LOCK_ROLE, fold_lock_rect
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QEvent
from anclicker.platform.qt_compat.QtGui import QMouseEvent
from anclicker.instructions.registry import get_instruction_spec

app = QApplication.instance() or QApplication([])
class Workspace(SimpleNamespace): pass

def ordinary(): return InstructionDraft('时间等待', {'时长': 0})
def repo_at(path):
    with sqlite3.connect(path) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    return GraphRepository(str(path))

from unittest.mock import patch
from anclicker.domain.table_movement import move_selected_one_step
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
assert move_selected_one_step([1,2,3,4,5],{2,4},{},-1)==[2,1,4,3,5]
assert move_selected_one_step([1,2,3,4,5],{2,4},{},1)==[1,3,2,5,4]
assert move_selected_one_step([1,2,3,4,5],{2,3},{},-1)==[2,3,1,4,5]
assert move_selected_one_step([1,2,3,4,5],{2,3},{},1)==[1,4,2,3,5]
assert move_selected_one_step([1,2,3],{1,2,3},{},-1)==[1,2,3]
assert move_selected_one_step([1,2,3],{1,3},{},-1)==[1,3,2]
assert move_selected_one_step([1,2,3],{1,3},{},1)==[2,1,3]
with tempfile.TemporaryDirectory() as folder:
 repo=repo_at(Path(folder)/'moves.db')
 ids=repo.append_recording([ordinary(),InstructionDraft('折叠步骤',{'下方条数':2,'整体锁定':True}),ordinary(),ordinary(),ordinary(),ordinary()])
 table=InstructionTableWidget(0,7);table.resize(950,400)
 def refresh(*args):
  commands=repo.list_commands();table.setRowCount(len(commands))
  for row,command in enumerate(commands):
   for col in range(7):
    item=QTableWidgetItem(command.type_id if col==2 else str(row+1));item.setData(Qt.UserRole,command.id);table.setItem(row,col,item)
  table.update_comment_ranges(repo.snapshot())
 host=Workspace(repository=repo,reload_graph=refresh,graphFinalized=SimpleNamespace(emit=refresh))
 allowed=[True]
 workspace=Workspace(window=SimpleNamespace(workspace=host,statusBar=SimpleNamespace(showMessage=lambda *a:None)),command_table=table,_table_mutation_allowed=lambda:allowed[0])
 controller=InstructionTableController(workspace);workspace._select_table_ids=controller._select_table_ids
 refresh();table.show();app.processEvents()
 table.moveSelectionRequested.connect(lambda direction:controller.move_table_commands(table.selected_command_ids(),None,direction=direction))
 def order():return [c.id for c in repo.list_commands()]
 # Moving a normal row upwards crosses the entire locked group.
 controller.move_table_commands([ids[4]],None,direction=-1)
 assert order()==[ids[0],ids[4],ids[1],ids[2],ids[3],ids[5]]
 controller.move_table_commands([ids[4]],None,direction=1)
 assert order()==ids
 # A child moves with the whole locked group, selection follows all members.
 controller.move_table_commands([ids[2]],None,direction=-1)
 assert order()==ids[1:4]+[ids[0]]+ids[4:]
 assert ids[1] in table.selected_command_ids()
 assert all(table.selectionModel().isSelected(table.model().index(row,2)) for row in range(3))
 assert folding_groups(repo.list_commands())[ids[1]]['members']==set(ids[2:4])
 controller.move_table_commands([ids[2]],None,direction=1)
 assert order()==ids
 before=order();allowed[0]=False;controller.move_table_commands([ids[5]],None,direction=-1);assert order()==before;allowed[0]=True
 # Actual context menu ordering and signal wiring.
 table.clearSelection();table.setCurrentCell(5,2)
 def choose(menu,*args):
  actions=menu.actions();names=[a.text() for a in actions];i=names.index('粘贴指令到表格末尾')
  assert names[i+1:i+3]==['上移选中指令','下移选中指令']
  assert actions[i+1].isEnabled() and not actions[i+2].isEnabled()
  actions[i+1].trigger()
 point=table.visualRect(table.model().index(5,2)).center()
 with patch('anclicker.ui.instruction_table.exec_two_column_menu',choose):
  table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,point,table.viewport().mapToGlobal(point)))
 assert order()==ids[:4]+[ids[5],ids[4]]
 assert set(table.selected_command_ids())=={ids[5]}
 assert [c.id for c in repo.validate_graph().commands]==order()
 table.close()
print('PASS menu order/trigger/boundary, contiguous and disjoint selection, locked-group crossing/moving, selection retention, execution guard, persisted graph consistency')
