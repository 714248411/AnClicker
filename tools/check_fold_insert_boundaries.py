"""Locked insertion gaps and unlocked endpoint tracking, including persisted nested groups."""
import os,sys,sqlite3,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups,locked_insertion_boundary
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_table import InstructionTableWidget
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTableWidgetItem
from anclicker.platform.qt_compat.QtCore import Qt,QPoint
app=QApplication.instance() or QApplication([])
def ordinary():return InstructionDraft('时间等待',{'时长':0})
def fold(count,locked=True):return InstructionDraft('折叠步骤',{'动态范围':True,'按条数':True,'下方条数':count,'整体锁定':locked,'已折叠':False})
with tempfile.TemporaryDirectory() as folder:
 def fresh(name):
  path=Path(folder)/name
  with sqlite3.connect(path) as db:GraphRepository.initialize_schema(db)
  return GraphRepository(str(path))
 for placement in (None,'above','below'):
  repo=fresh(str(placement)+'.db');ids=repo.append_recording([ordinary(),fold(3),ordinary(),ordinary(),ordinary(),ordinary()]);owner=ids[1]
  def members():return folding_groups(repo.list_commands())[owner]['members']
  expected=set(ids[2:5])
  for anchor in ids[2:5]:
   new=repo.insert_table_commands([ordinary(),ordinary()],before_command_id=anchor,placement=placement)
   assert members()==expected
   order=[c.id for c in repo.list_commands()];a=order.index(owner);b=order.index(ids[4])
   assert order[a:b+1]==ids[1:5]
   assert all(order.index(n)<a if placement=='above' else order.index(n)>b if placement=='below' else not a<order.index(n)<=b for n in new)
  # Direct reorders cannot slip an outsider into a locked group or reverse its members.
  current=[c.id for c in repo.list_commands()];bad=list(current);bad.remove(ids[0]);bad.insert(bad.index(ids[3]),ids[0]);before=repo.snapshot()
  try:repo.reorder_table_commands(bad)
  except ValueError:pass
  else:raise AssertionError('Allowed insertion inside locked group')
  assert repo.snapshot()==before
  repo.set_step_locks([owner],False)
  inserted=repo.insert_table_commands([ordinary(),ordinary()],before_command_id=ids[4])
  expected.update(inserted);assert members()==expected
  order=[c.id for c in repo.list_commands()];tail=order.index(ids[4])+1
  outside=repo.insert_table_commands([ordinary()],before_command_id=order[tail] if tail<len(order) else 'end')
  assert members()==expected and not set(outside)&members()
  repo.set_step_locks([owner],True)
  repo.insert_table_commands([ordinary()],before_command_id=inserted[0]);assert members()==expected
  assert folding_groups(GraphRepository(repo.db_path).list_commands())[owner]['members']==expected
 # Nested locked groups snap through the outer boundary, even when inner is unlocked.
 repo=fresh('nested.db');ids=repo.append_recording([fold(4),fold(2,False),ordinary(),ordinary(),ordinary(),ordinary()])
 groups=folding_groups(repo.list_commands())
 assert locked_insertion_boundary(ids,groups,2,'above')==0
 assert locked_insertion_boundary(ids,groups,2,'below')==5
 new=repo.insert_table_commands([ordinary()],before_command_id=ids[2],placement='below')
 assert folding_groups(repo.list_commands())[ids[0]]['members']==set(ids[1:5])
 assert folding_groups(repo.list_commands())[ids[1]]['members']==set(ids[2:4])
 # Actual drag indicator uses the same legal boundary with expanded locked rows.
 table=InstructionTableWidget(len(ids),7);table.resize(900,500)
 for row,cid in enumerate(ids):
  for col in range(7):
   item=QTableWidgetItem(str(cid));item.setData(Qt.UserRole,cid);table.setItem(row,col,item)
 table.step_groups=groups;table.show();app.processEvents()
 for row in range(1,5):
  point=QPoint(10,table.rowViewportPosition(row)+1)
  boundary,y=table._drop_boundary(point)
  assert boundary in (0,5),(row,boundary)
  assert y==table.rowViewportPosition(boundary)
 table.close()
 # A last group does not absorb append, but does absorb insertion before its final member when unlocked.
 repo=fresh('tail.db');ids=repo.append_recording([fold(2,False),ordinary(),ordinary()])
 new=repo.append_recording([ordinary()]);assert folding_groups(repo.list_commands())[ids[0]]['members']==set(ids[1:])
 interior=repo.insert_table_commands([ordinary()],before_command_id=ids[2]);assert folding_groups(repo.list_commands())[ids[0]]['members']==set(ids[1:]+interior)
print('PASS locked above/below/batch insertion, reorder rollback, unlock endpoint, exclusive tail, relock, persistence, nested groups and drag indicator',flush=True)
os._exit(0)
