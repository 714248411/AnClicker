"""Persist multiple start edges and launch all workers before blocking continuations."""
import os, sys, tempfile, threading, time
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft, ExecutionContext
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices
from openpyxl import Workbook, load_workbook

with tempfile.TemporaryDirectory() as folder:
    for variant in ('ordinary', 'loop', 'jump'):
        db = DatabaseOperation(str(Path(folder) / (variant+'.db')))
        repo = GraphRepository(db.db_path)
        drafts = [InstructionDraft('时间等待', {'时长': 0}, note='main'),
                  InstructionDraft('多线程启动', {'线程名称': 'a', '入口编号': 4}),
                  InstructionDraft('多线程启动', {'线程名称': 'b', '入口编号': 5}),
                  InstructionDraft('时间等待', {'时长': 0}, note='a'),
                  InstructionDraft('时间等待', {'时长': 0}, note='b')]
        if variant == 'loop': drafts.append(InstructionDraft('循环', {'次数': 0}))
        if variant == 'jump': drafts.append(InstructionDraft('变量比较'))
        ids = repo.append_recording(drafts, connect=False)
        def node(cid): return next(n.node_id for n in repo.snapshot().nodes if n.command_id == cid)
        repo.delete_node_connections('start', 'outgoing')
        # A normal branch is inserted first; both starters must still win priority.
        for cid in ids[:3]: repo.connect_nodes('start', node(cid))
        repo.connect_nodes(node(ids[1]), node(ids[0]))
        repo.connect_nodes(node(ids[2]), 'end')
        repo.connect_nodes(node(ids[0]), 'end')
        for cid in ids[3:5]: repo.connect_nodes(node(cid), 'end')
        graph = repo.execution_snapshot()
        assert len([e for e in graph.edges if e.source == 'start']) == 3
        book = Workbook(); repo.export_to_workbook(book, db)
        filename = Path(folder)/(variant+'.xlsx'); book.save(filename); book.close()
        restored_db = DatabaseOperation(str(Path(folder)/(variant+'-restored.db')))
        restored = GraphRepository(restored_db.db_path)
        book = load_workbook(filename)
        restored.import_from_workbook(book); book.close()
        assert len([e for e in restored.execution_snapshot().edges if e.source == 'start']) == 3
        ready = {name: threading.Event() for name in ('a', 'b')}
        seen = []; failures = []
        def probe(context, command):
            seen.append(command.note)
            if command.note in ready:
                ready[command.note].set()
                context.runtime.wait(.04, context)
            else:
                deadline = time.monotonic()+2
                while not all(event.is_set() for event in ready.values()) and time.monotonic()<deadline:
                    context.runtime.wait(.01, context)
                if not all(event.is_set() for event in ready.values()):
                    failures.append('main continuation blocked before all starters ran')
        engine = ExecutionEngine(ExecutionServices(db, output=lambda *a: None))
        engine.run_unconnected = False
        context = ExecutionContext(services={'时间等待': probe})
        engine.execute(graph, context)
        assert not failures, failures
        assert sorted(seen) == ['a','b','main'], seen
        manager = context.metadata['parallel_manager']
        assert len(manager.tasks) == 2 and all(not task.thread.is_alive() for task in manager.tasks.values())
        print('PASS', variant, 'multiple start links, workbook roundtrip, launch priority, branch isolation and cleanup')
print('PASS parallel start fanout across all three flow interpreters')
