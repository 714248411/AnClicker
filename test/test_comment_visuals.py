from qt_compat.QtWidgets import QApplication
from instructions.models import InstructionDraft
from flow_comments import BELOW, ABOVE
from test.test_hidden_stop import host


def setup_range(host):
    repo = host.workspace.repository
    records = [repo.add_command(InstructionDraft(kind, {}), unconnected=True)
               for kind in (BELOW, '时间等待', '时间等待', ABOVE, '时间等待')]
    host.workspace.reload_graph()
    host.view_workspace.show_table()
    host.view_workspace.refresh_table()
    return records


def test_fold_keeps_boundaries_and_refresh(host):
    records = setup_range(host)
    views = host.view_workspace
    table = views.command_table
    rows = views._table_command_rows
    table.set_comment_collapsed(records[0].id, True)
    assert not table.isRowHidden(rows[records[0].id])
    assert all(table.isRowHidden(rows[c.id]) for c in records[1:3])
    assert not table.isRowHidden(rows[records[3].id])
    assert not table.isRowHidden(rows[records[4].id])
    host.workspace.repository.add_command(InstructionDraft('时间等待', {}), unconnected=True)
    views.refresh_table()
    assert all(table.isRowHidden(views._table_command_rows[c.id]) for c in records[1:3])
    table.set_comment_collapsed(records[0].id, False)
    assert not any(table.isRowHidden(row) for row in range(table.rowCount()))
    assert len(host.workspace.repository.list_commands()) == 7


def test_graph_comment_nodes_and_edges_restore(host):
    records = setup_range(host)
    repo = host.workspace.repository
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    for source,target in zip(records, records[1:]):
        repo.connect_nodes(nodes[source.id], nodes[target.id])
    host.workspace.reload_graph()
    scene = host.workspace.editor.scene
    for command in records[:4]:
        node = scene.nodes_by_command_id[command.id]
        assert node.comment_disabled
        assert node.graphicsEffect() is not None
    assert not scene.nodes_by_command_id[records[-1].id].comment_disabled
    assert sum(edge.comment_disabled for edge in scene.edges) == 3
    host.view_workspace.show_flow()
    QApplication.processEvents()
    assert not host.workspace.editor.view.viewport().grab().isNull()
    repo.delete_commands([records[0].id, records[3].id], preserve_flow=False)
    host.workspace.reload_graph()
    host.view_workspace.refresh_table()
    assert not any(n.comment_disabled for n in host.workspace.editor.scene.nodes_by_id.values())
    assert not any(n.graphicsEffect() for n in host.workspace.editor.scene.nodes_by_id.values())


def test_nested_fold_ranges_keep_inner_state(host):
    repo = host.workspace.repository
    records = [repo.add_command(InstructionDraft(kind, {}), unconnected=True)
               for kind in (BELOW, BELOW, '时间等待', ABOVE, ABOVE)]
    host.view_workspace.refresh_table()
    table = host.view_workspace.command_table
    rows = host.view_workspace._table_command_rows
    table.set_comment_collapsed(records[1].id, True)
    table.set_comment_collapsed(records[0].id, True)
    table.set_comment_collapsed(records[0].id, False)
    assert not table.isRowHidden(rows[records[1].id])
    assert table.isRowHidden(rows[records[2].id])
    assert not table.isRowHidden(rows[records[3].id])


def test_table_comment_background_tracks_theme_and_removal(host):
    from qt_compat.QtCore import Qt
    records = setup_range(host)
    views = host.view_workspace
    table = views.command_table
    for theme in ('light', 'dark'):
        views.theme_mode = theme
        views._apply_theme()
        views.refresh_table()
        for command in records[:4]:
            row = views._table_command_rows[command.id]
            for col in range(table.columnCount()):
                assert table.item(row, col).background().color().name() == ('#3c3c40' if theme == 'dark' else '#dedee3')
        row = views._table_command_rows[records[-1].id]
        assert table.item(row, 0).background().style() == Qt.NoBrush
    host.workspace.repository.delete_commands([records[0].id, records[3].id], preserve_flow=False)
    views.refresh_table()
    for row in range(table.rowCount()):
        assert table.item(row, 0).background().style() == Qt.NoBrush


def test_comment_background_is_actually_painted(host):
    records = setup_range(host)
    views = host.view_workspace
    table = views.command_table
    table.clearSelection()
    for theme, expected in [('light', '#dedee3'), ('dark', '#3c3c40')]:
        views.theme_mode = theme
        views._apply_theme()
        views.refresh_table()
        QApplication.processEvents()
        for command in records[1:3]:
            row = views._table_command_rows[command.id]
            table.scrollToItem(table.item(row, 0))
            QApplication.processEvents()
            rect = table.visualItemRect(table.item(row, 0))
            image = table.viewport().grab().toImage()
            scale = image.devicePixelRatio()
            point = rect.bottomLeft()
            assert image.pixelColor(int((point.x()+10)*scale), int((point.y()-3)*scale)).name() == expected


def test_connected_fold_excludes_unrelated_rows_and_tracks_edges(host):
    records = setup_range(host)
    low, first, unrelated, high, tail = records
    repo = host.workspace.repository
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    repo.connect_nodes(nodes[low.id], nodes[first.id])
    repo.connect_nodes(nodes[first.id], nodes[high.id])
    views = host.view_workspace
    views.refresh_table()
    table = views.command_table
    table.set_comment_collapsed(low.id, True)
    assert table.isRowHidden(views._table_command_rows[first.id])
    for command in (low, unrelated, high, tail):
        assert not table.isRowHidden(views._table_command_rows[command.id])
    # Changing only edges must invalidate folding even if the table text is unchanged.
    repo.delete_connection(nodes[first.id], nodes[high.id])
    repo.connect_nodes(nodes[first.id], nodes[unrelated.id])
    repo.connect_nodes(nodes[unrelated.id], nodes[high.id])
    views.refresh_table()
    assert table.isRowHidden(views._table_command_rows[unrelated.id])
    table.set_comment_collapsed(low.id, False)
    assert not any(table.isRowHidden(row) for row in range(table.rowCount()))
