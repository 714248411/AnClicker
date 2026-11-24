"""Connected thread grouping, nesting and real worker execution regressions."""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft, ExecutionContext, CommandRecord
from anclicker.domain.graph_models import GraphSnapshot, NodeView, EdgeRecord
from anclicker.domain.step_folding import folding_groups, locked_move_ids, hidden_steps, copy_group_drafts
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices
from openpyxl import Workbook, load_workbook


def make_repo(folder, name):
    db = DatabaseOperation(str(Path(folder) / (name + '.db')))
    return db, GraphRepository(db.db_path)


def chain(repo, labels=('a', 'b', 'c')):
    drafts = []
    for name in labels:
        drafts.extend([InstructionDraft('多线程启动', {'线程名称': name, '入口编号': 0}),
                       InstructionDraft('时间等待', {'时长': 0}, note=name)])
    return repo.append_recording(drafts)


with tempfile.TemporaryDirectory() as folder:
    db, repo = make_repo(folder, 'groups')
    ids = chain(repo)
    a, aw, b, bw, c, cw = ids
    groups = folding_groups(repo.list_commands())
    assert groups[a]['members'] == {aw} and groups[b]['members'] == {bw}
    assert groups[a]['locked'] and groups[a]['collapsed']
    assert locked_move_ids(repo.list_commands(), [bw]) == {b, bw}
    repo.set_thread_nested(b, True)
    repo.set_thread_nested(c, True)
    groups = folding_groups(repo.list_commands())
    assert groups[a]['members'] == {aw, b, bw, c, cw}
    assert groups[b]['members'] == {bw, c, cw}
    assert locked_move_ids(repo.list_commands(), [cw]) == set(ids)
    repo.set_step_collapsed(a, False)
    groups = folding_groups(repo.list_commands())
    assert b not in hidden_steps(groups) and c in hidden_steps(groups)
    repo.set_step_collapsed(b, False)
    groups = folding_groups(repo.list_commands())
    assert c not in hidden_steps(groups) and cw in hidden_steps(groups)
    repo.set_thread_nested(c, False)
    assert repo.get_command(c).parameters['嵌套层级'] == 1
    groups = folding_groups(repo.list_commands())
    assert groups[b]['members'] == {bw} and groups[a]['members'] == {aw,b,bw,c,cw}
    repo.set_thread_nested(c, True)
    assert repo.get_command(c).parameters['嵌套层级'] == 2
    repo.set_thread_nested(c, False)
    repo.set_thread_nested(b, False)
    assert repo.get_command(b).parameters['嵌套层级'] == 0
    assert folding_groups(repo.list_commands())[a]['members'] == {aw, c, cw}
    repo.set_thread_nested(c, False)
    ids = [record.id for record in repo.list_commands()]
    copied = copy_group_drafts(repo.list_commands(), [b], repo.snapshot())
    pasted = repo.insert_table_commands(copied)
    assert folding_groups(repo.list_commands())[pasted[0]]['members'] == {pasted[1]}
    assert locked_move_ids(repo.list_commands(), [pasted[1]]) == set(pasted)
    repo.reorder_table_commands(pasted + ids)
    assert [c.id for c in repo.list_commands()][:2] == pasted
    book = Workbook(); repo.export_to_workbook(book, db)
    filename = Path(folder) / 'groups.xlsx'; book.save(filename); book.close()
    _, restored = make_repo(folder, 'restored')
    book = load_workbook(filename); restored.import_from_workbook(book); book.close()
    assert folding_groups(restored.list_commands()) == folding_groups(repo.list_commands())
    graph_copies = repo.append_recording(copy_group_drafts(repo.list_commands(), [a], repo.snapshot()), connect=False)
    assert folding_groups(repo.list_commands())[graph_copies[0]]['members'] == set(graph_copies[1:])
    assert '_线程复制' not in repo.get_command(graph_copies[0]).parameters
    print('PASS automatic locks, recursive folds, nesting promotion, graph/table copy, reorder and workbook roundtrip')

    for nesting in (False, True):
        for variant in ('ordinary', 'loop', 'jump'):
            db, repo = make_repo(folder, str(nesting) + variant)
            ids = chain(repo, ('a', 'b'))
            if nesting:
                repo.set_thread_nested(ids[2], True)
            if variant == 'loop':
                repo.add_command(InstructionDraft('循环', {'次数': 0}), unconnected=True)
            elif variant == 'jump':
                repo.add_command(InstructionDraft('变量比较'), unconnected=True)
            seen, logs, failures = [], [], []
            barrier = threading.Barrier(2)
            def probe(context, command):
                seen.append((command.note, context.runtime.wait.__self__.control.parent))
                if not nesting:
                    try: barrier.wait(2)
                    except threading.BrokenBarrierError: failures.append('siblings did not run concurrently')
                context.runtime.wait(.03, context)
            engine = ExecutionEngine(ExecutionServices(db, output=logs.append))
            engine.run_unconnected = False
            context = ExecutionContext(services={'时间等待': probe}, output=logs.append)
            engine.execute(repo.execution_snapshot(), context)
            assert not failures, (failures, seen, logs)
            assert sorted(n for n, _ in seen) == ['a','b'], (seen, logs)
            tasks = context.metadata['parallel_manager'].tasks
            assert all(not t.thread.is_alive() for t in tasks.values())
            assert tasks['b'].owner_control is (tasks['a'].control if nesting else engine.control)
            print('PASS', nesting, variant, 'scope isolation, concurrency, parent ownership and completion')

    db, repo = make_repo(folder, 'root-nesting')
    ids = chain(repo, ('a','b','c'))
    repo.set_thread_nested(ids[2], True)
    repo.set_thread_nested(ids[4], True)
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes if n.command_id is not None}
    repo.delete_node_connections(nodes[ids[1]], 'outgoing')
    repo.connect_nodes(nodes[ids[1]], 'end')
    repo.delete_node_connections(nodes[ids[3]], 'outgoing')
    repo.connect_nodes(nodes[ids[3]], 'end')
    repo.connect_nodes('start', nodes[ids[2]])
    repo.connect_nodes('start', nodes[ids[4]])
    seen = []
    engine = ExecutionEngine(ExecutionServices(db, output=lambda text: None))
    engine.run_unconnected = False
    context = ExecutionContext(services={'时间等待': lambda context, command: seen.append(command.note)})
    engine.execute(repo.execution_snapshot(), context)
    tasks = context.metadata['parallel_manager'].tasks
    assert sorted(seen) == ['a','b','c'], seen
    assert tasks['b'].owner_control is tasks['a'].control
    assert tasks['c'].owner_control is tasks['b'].control
    print('PASS separately wired nested roots run once under the correct parent')
    for nested in (False, True):
        db, repo = make_repo(folder, 'loop-body-' + str(nested))
        commands = [CommandRecord(1, '多线程启动', {'线程名称':'a','入口编号':0}, order=0),
                    CommandRecord(2, '循环', {'次数':3}, order=1),
                    CommandRecord(3, '时间等待', {'时长':0}, note='loop', order=2),
                    CommandRecord(4, '多线程启动', {'线程名称':'b','入口编号':0,'嵌套层级':int(nested)}, order=3),
                    CommandRecord(5, '时间等待', {'时长':0}, note='after', order=4)]
        nodes = [NodeView('start', None, 'start', None, '开始', 0, 0),
                 NodeView('end', None, 'end', None, '结束', 0, 0)]
        nodes += [NodeView(str(c.id), c.id, 'instruction', c.type_id, c.type_id, 0, 0) for c in commands]
        edges = [('start','1',0), ('1','2',0), ('2','3',3), ('3','2',0), ('2','4',4), ('4','5',0), ('5','end',0)]
        graph = GraphSnapshot(tuple(commands), tuple(nodes), tuple(EdgeRecord(*e) for e in edges))
        seen, logs = [], []
        engine = ExecutionEngine(ExecutionServices(db, output=logs.append))
        context = ExecutionContext(services={'时间等待':lambda context,command:seen.append(command.note)}, output=logs.append)
        engine.execute(graph, context)
        assert seen.count('loop') == 3 and seen.count('after') == 1, (seen, logs)
    print('PASS actual loop body retains back-edges and exits into sibling/nested threads')

    db, repo = make_repo(folder, 'legacy-nested')
    ids = repo.append_recording([
        InstructionDraft('多线程启动', {'线程名称':'old-a','入口编号':3}),
        InstructionDraft('多线程启动', {'线程名称':'old-b','入口编号':4}),
        InstructionDraft('时间等待', {'时长':0}, note='old-a'),
        InstructionDraft('时间等待', {'时长':0}, note='old-b')], connect=False)
    node_ids = {n.command_id:n.node_id for n in repo.snapshot().nodes if n.command_id is not None}
    for source, target in [('start',node_ids[ids[0]]), (node_ids[ids[0]],node_ids[ids[1]]),
                           (node_ids[ids[1]],'end'), (node_ids[ids[2]],'end'), (node_ids[ids[3]],'end')]:
        repo.connect_nodes(source,target)
    repo.set_thread_nested(ids[1], True)
    seen, logs = [], []
    engine = ExecutionEngine(ExecutionServices(db, output=logs.append))
    context = ExecutionContext(services={'时间等待':lambda context,command:seen.append(command.note)},output=logs.append)
    engine.execute(repo.execution_snapshot(), context)
    assert sorted(seen) == ['old-a','old-b'], (seen,logs)
    tasks = context.metadata['parallel_manager'].tasks
    assert tasks['old-b'].owner_control is tasks['old-a'].control
    print('PASS nesting legacy explicit-entry threads without changing their entry numbers')

    db, repo = make_repo(folder, 'control')
    ids = chain(repo, ('a','b','c'))
    repo.set_thread_nested(ids[2], True); repo.set_thread_nested(ids[4], True)
    # Last descendant stays alive so pause / stop must propagate through two parents.
    counts, failures = [], []
    ready = threading.Event()
    def ticking(context, command):
        if command.note != 'c':
            return
        ready.set()
        while context.runtime.wait(.01, context):
            counts.append(time.monotonic())
    engine = ExecutionEngine(ExecutionServices(db, output=lambda text: None))
    context = ExecutionContext(services={'时间等待': ticking})
    def running():
        try: engine.execute(repo.execution_snapshot(), context)
        except Exception as error: failures.append(error)
    worker = threading.Thread(target=running)
    worker.start()
    try:
        assert ready.wait(3)
        engine.pause(); time.sleep(.08)
        frozen = len(counts); time.sleep(.1)
        assert len(counts) == frozen
        engine.resume(); time.sleep(.1)
        assert len(counts) > frozen
        engine.pause_for_schedule(True); time.sleep(.08)
        frozen = len(counts); time.sleep(.1)
        assert len(counts) == frozen
        engine.pause_for_schedule(False); time.sleep(.1)
        assert len(counts) > frozen
        engine.pause()
    finally:
        engine.request_stop(); worker.join(3)
    assert not worker.is_alive() and not failures, failures
    assert all(not t.thread.is_alive() for t in context.metadata['parallel_manager'].tasks.values())
    print('PASS three-level manual/scheduled pause, resume and stop while paused')
print('PASS thread groups suite')
