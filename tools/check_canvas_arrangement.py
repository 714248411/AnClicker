"""Regression checks for checked layout modes, append-only placement and reflow."""
import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMenu
from anclicker.platform.qt_compat.QtCore import QCoreApplication, QEvent
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.node_editor.arrangement import MODES, next_position
from anclicker.platform.qt_compat.QtCore import QRectF
app = QApplication([])
# Three 100px cards with two 30px gaps fit exactly; no trailing gap is required.
bounds = QRectF(0, 0, 360, 360)
assert next_position(MODES[2], (130, 0), 130, 130, bounds, 30) == (260, 0)
assert next_position(MODES[2], (260, 0), 130, 130, bounds, 30) == (0, 130)
assert next_position(MODES[3], (0, 130), 130, 130, bounds, 30) == (0, 260)
assert next_position(MODES[3], (0, 260), 130, 130, bounds, 30) == (130, 0)
assert next_position(MODES[4], (260, 0), 130, 130, bounds, 30) == (260, 130)
assert next_position(MODES[4], (260, 130), 130, 130, bounds, 30) == (130, 130)
assert next_position(MODES[5], (0, 260), 130, 130, bounds, 30) == (130, 260)
assert next_position(MODES[5], (130, 260), 130, 130, bounds, 30) == (130, 130)
print('PASS viewport boundary capacity and both snake turn directions')
with tempfile.TemporaryDirectory() as folder:
    path = str(Path(folder) / 'graph.db')
    db = sqlite3.connect(path)
    GraphRepository.initialize_schema(db)
    db.commit()
    db.close()
    ws = InstructionWorkspace(path)
    ws._check_parameter_save_allowed = lambda: None
    ws._show_error = lambda title, error: (_ for _ in ()).throw(AssertionError((title, error)))
    ws.editor.resize(1000, 700)
    ws.editor.show()
    app.processEvents()
    ws.editor.view._set_zoom(1)
    layout = ws.arrangement
    saved_mode = layout.mode
    font = ws.editor.view.font()
    base_gap = layout.spacing()
    larger = ws.editor.view.font()
    larger.setPointSizeF(max(12, font.pointSizeF()) * 1.5)
    ws.editor.view.setFont(larger)
    assert layout.spacing() > base_gap
    ws.editor.view.setFont(font)
    repo = ws.repository
    draft = lambda: InstructionDraft('时间等待', {'类型':'时间等待','时长':1,'单位':'秒'})
    for _ in range(23):
        repo.add_command(draft(), unconnected=True)
    ws.reload_graph()
    def coordinates():
        return {n.node_id: (n.x, n.y) for n in repo.snapshot().nodes}
    def ordered():
        return [ws.editor.scene.nodes_by_command_id[c.id] for c in repo.snapshot().commands]
    def assert_wrap_bounds():
        app.processEvents()
        bounds = layout.bounds.adjusted(-2, -2, 2, 2)
        for node in ws.editor.scene.nodes_by_id.values():
            if not node.isVisible():
                continue
            rect = layout.card_rect(node)
            if layout.mode in (MODES[2], MODES[4]):
                assert rect.left() >= bounds.left() and rect.right() <= bounds.right(), (node.node_id, bounds, rect)
            elif layout.mode in (MODES[3], MODES[5]):
                assert rect.top() >= bounds.top() and rect.bottom() <= bounds.bottom(), (node.node_id, bounds, rect)
    for mode in MODES:
        ws.editor.view._set_zoom(1.0)
        before = coordinates()
        menu = QMenu()
        layout.add_menu(menu)
        action = next(a for a in menu.actions() if a.text() == ('横向贪吃蛇排布' if mode == MODES[4] else mode))
        action.trigger()
        assert coordinates() == before, 'selecting a mode moved existing nodes'
        menu.deleteLater()
        menu = QMenu()
        layout.add_menu(menu)
        checked = [a.text() for a in menu.actions() if a.isChecked()]
        assert checked == [('横向贪吃蛇排布' if mode == MODES[4] else mode)], checked
        menu.deleteLater()
        edges = repo.snapshot().edges
        transform = ws.editor.view.transform()
        layout.rearrange()
        assert ws.editor.view.transform() == transform
        assert_wrap_bounds()
        assert edges == repo.snapshot().edges
        nodes = ordered()
        rects = [n.sceneBoundingRect() for n in nodes]
        assert all(not a.intersects(b) for i,a in enumerate(rects) for b in rects[i+1:]), mode
        if mode == MODES[0]:
            assert len({round(n.y()) for n in nodes}) == 1
        elif mode == MODES[1]:
            assert len({round(n.x()) for n in nodes}) == 1
        elif mode == MODES[5]:
            columns = {}
            for n in nodes:
                columns.setdefault(round(n.x()), []).append(n.y())
            assert len(columns) > 1
            for index, ys in enumerate(columns.values()):
                assert ys == sorted(ys, reverse=(index % 2 == 1)), (index, ys)
        elif mode == MODES[3]:
            assert nodes[1].x() == nodes[0].x() and nodes[1].y() > nodes[0].y()
            assert len({round(n.x()) for n in nodes}) > 1
        else:
            rows = {}
            for n in nodes:
                rows.setdefault(round(n.y()), []).append(n.x())
            assert len(rows) > 1
            for index, xs in enumerate(rows.values()):
                assert xs == sorted(xs, reverse=(mode == MODES[4] and index % 2 == 1)), (mode, index, xs)
        before = coordinates()
        new = repo.add_command(draft(), unconnected=True)
        ws.reload_graph()
        after = coordinates()
        assert all(after[k] == v for k,v in before.items() if k != 'end'), 'append moved old commands'
        rects = [n.sceneBoundingRect() for n in ordered()]
        assert all(not rects[-1].intersects(r) for r in rects[:-1]), mode
        assert coordinates() == {n.node_id:(n.x,n.y) for n in GraphRepository(path).snapshot().nodes}
        print('PASS', mode, 'selection/reflow/append/no-overlap/persistence')
    # A 58% canvas uses scene-space viewport dimensions, not cached 100% limits.
    import math
    view = ws.editor.view
    layout.select(MODES[2])
    view._set_zoom(1.0)
    layout.rearrange()
    assert_wrap_bounds()
    view._set_zoom(0.58)
    app.processEvents()
    units = layout.units(repo.snapshot())
    card_width = max(rect.width() for _, _, rect in units)
    gap = layout.spacing()
    desired_width = (4 * card_width + 5 * gap + 4) * 0.58
    ws.editor.resize(ws.editor.width() + round(desired_width - view.viewport().width()), 700)
    app.processEvents()
    layout.rearrange()
    rows = {}
    for n in ordered():
        rows.setdefault(round(n.y()), []).append(n)
    assert max(len(row) for row in rows.values()) == 4, [len(r) for r in rows.values()]
    assert abs(view.transform().m11() - 0.58) < 0.00001
    assert_wrap_bounds()
    view._set_zoom(0.40)
    app.processEvents()
    current_width = layout._bounds().width()
    before = coordinates()
    repo.add_command(draft(), unconnected=True)
    ws.reload_graph()
    assert abs(layout.bounds.width() - current_width) < 0.01
    after = coordinates()
    assert all(after[k] == v for k,v in before.items() if k != 'end')
    print('PASS 58% fits four cards; zoom change refreshes append limits without moving old commands')
    # Mixed-size cards must use visible edges, not a maximum-size grid or hit margins.
    from anclicker.platform.qt_compat.QtGui import QFontMetricsF
    nodes = ordered()
    for index, node in enumerate(nodes):
        repo.save_node_size(node.node_id, 180 + (index % 3)*70, 80 + (index % 3)*30)
    ws.reload_graph()
    assert abs(layout.spacing()-QFontMetricsF(ordered()[0].title_font).horizontalAdvance('字字字')) < 0.001
    for mode in MODES[:2]:
        layout.select(mode)
        layout.rearrange()
        rects = [layout.card_rect(n) for n in ordered()]
        for a,b in zip(rects, rects[1:]):
            distance = b.left()-a.right() if mode == MODES[0] else b.top()-a.bottom()
            assert abs(distance-layout.spacing()) < 0.001, (mode, distance, layout.spacing())
    print('PASS mixed width/height cards have exactly three title-character widths between visible edges')
    # Moving an existing card, connecting or changing settings must not reflow.
    before = coordinates()
    ws.reload_graph()
    assert coordinates() == before
    ids = [c.id for c in repo.snapshot().commands][2:5]
    ws.set_step_locks(ids, True)
    scene = ws.editor.scene
    groups = {members for members in scene.locked_groups.values()}
    assert groups
    group = next(iter(groups))
    before = coordinates()
    layout.rearrange()
    after = coordinates()
    deltas = {(round(after[k][0]-before[k][0], 4), round(after[k][1]-before[k][1], 4)) for k in group}
    assert len(deltas) == 1, deltas
    assert group in scene.locked_groups.values()
    assert_wrap_bounds()
    print('PASS locked stack moves as one unit and preserves member offsets')
    # A freshly imported project retains its saved coordinates.
    before = coordinates()
    ws.reload_graph(reset_view=True)
    assert coordinates() == before
    print('PASS imported project retains saved layout')
    layout.select(saved_mode)
    ws.editor.close()
    ws.editor.deleteLater()
    ws.palette.deleteLater()
    ws.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
print('PASS all canvas arrangement checks')
