import sys,tempfile,sqlite3,time,json,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'bench.db'
 with sqlite3.connect(path) as db:GraphRepository.initialize_schema(db)
 db.close();repo=GraphRepository(str(path))
 ids=repo.append_recording([InstructionDraft('时间等待',{'时长':0}) for _ in range(1000)])
 node=repo.snapshot().nodes[1].node_id
 times=[]
 for i in range(12):
  start=time.perf_counter();repo.save_node_positions({node:(i*10,i*10)});times.append((time.perf_counter()-start)*1000)
 print(json.dumps({'rows':1000,'position_save_median_ms':statistics.median(times),'samples':times}))
