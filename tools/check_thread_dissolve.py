"""Dissolve one starter without deleting body steps or adopting sibling threads."""
import os
import sys
import tempfile
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.thread_groups import thread_parents

with tempfile.TemporaryDirectory() as folder:
    db = DatabaseOperation(str(Path(folder)/'dissolve.db'))
    repo = GraphRepository(db.db_path)
    drafts = []
    for name in ('A','B','C','D','E'):
        drafts += [InstructionDraft('多线程启动', {'线程名称':name, '入口编号':0}), InstructionDraft('时间等待', {'时长':0})]
    ids = repo.append_recording(drafts)
    # A > B > C, D and E remain independent siblings.
    repo.set_thread_nested(ids[2], True)
    repo.set_thread_nested(ids[4], True)
    before = repo.snapshot()
    removed = next(n.node_id for n in before.nodes if n.command_id==ids[2])
    assert repo.dissolve_thread(ids[2])
    after = repo.snapshot()
    assert {c.id for c in after.commands} == {c.id for c in before.commands}-{ids[2]}
    assert {(e.source,e.target,e.kind) for e in after.edges} == {(e.source,e.target,e.kind) for e in before.edges if removed not in (e.source,e.target)}
    assert {n.node_id:(n.x,n.y) for n in after.nodes} == {n.node_id:(n.x,n.y) for n in before.nodes if n.node_id!=removed}
    parents = thread_parents(after.commands)
    assert parents[ids[4]]==ids[0] and parents[ids[6]] is None and parents[ids[8]] is None
    assert repo.get_command(ids[3]) is not None
    # Dissolving the outer parent promotes its child to root, without reparenting siblings.
    repo.dissolve_thread(ids[0])
    parents = thread_parents(repo.list_commands())
    assert all(parent is None for parent in parents.values())
    assert all(repo.get_command(cid) is not None for cid in ids[1::2])
    stable = repo.snapshot()
    try:
        repo.dissolve_thread(ids[1])
    except ValueError:
        pass
    else:
        raise AssertionError('ordinary command accepted as a thread')
    assert repo.snapshot()==stable
print('PASS dissolve starter only, retain all body nodes/edges/positions, promote children, preserve siblings and atomic rejection')
