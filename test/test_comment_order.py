from flow_comments import BELOW, ABOVE
from graph_repository import GraphRepository
from instructions.models import InstructionDraft
from 数据库操作 import DatabaseOperation


def test_align_markers_in_incomplete_graph_preserves_layout_and_edges(tmp_path):
    db = DatabaseOperation(str(tmp_path / 'order.db'))
    repo = GraphRepository(db.db_path)
    records = [repo.add_command(InstructionDraft(kind, {}), unconnected=True)
               for kind in ('时间等待', '时间等待', '时间等待', BELOW, ABOVE, '时间等待')]
    head, middle, tail, low, high, other = records
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    chain = ['start'] + [nodes[c.id] for c in (head,low,middle,high,tail)] + ['end']
    for source,target in zip(chain,chain[1:]):
        repo.connect_nodes(source,target)
    before = repo.snapshot()
    assert repo.align_comment_marker_orders()
    after = repo.snapshot()
    assert [c.id for c in after.commands] == [head.id,low.id,middle.id,high.id,tail.id,other.id]
    assert [c.order for c in after.commands] == list(range(6))
    assert after.edges == before.edges
    assert {n.node_id:(n.x,n.y) for n in after.nodes} == {n.node_id:(n.x,n.y) for n in before.nodes}
    assert not repo.align_comment_marker_orders()
    reopened = GraphRepository(db.db_path)
    assert [c.id for c in reopened.list_commands()] == [c.id for c in after.commands]


def test_unconnected_markers_keep_manual_order(tmp_path):
    db = DatabaseOperation(str(tmp_path / 'unconnected.db'))
    repo = GraphRepository(db.db_path)
    for kind in (BELOW, '时间等待', ABOVE):
        repo.add_command(InstructionDraft(kind, {}), unconnected=True)
    assert not repo.align_comment_marker_orders()
