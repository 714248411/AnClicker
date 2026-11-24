"""Independent thread locks translate without moving or reordering other commands."""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups, locked_move_ids
from anclicker.storage.graph_repository import GraphRepository
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.node_editor.widget import NodeEditorWidget
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QEvent
from anclicker.platform.qt_compat.QtGui import QMouseEvent, QFontDatabase, QFont
from PySide2.QtTest import QTest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
families = QFontDatabase.applicationFontFamilies(font_id)
if families: app.setFont(QFont(families[0], 10))

with tempfile.TemporaryDirectory() as folder:
    dbpath = Path(folder) / 'move.db'
    with sqlite3.connect(dbpath) as db: GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(dbpath))
    drafts = [InstructionDraft('多线程启动', {'线程名称':'采集线程','入口编号':0}),
              InstructionDraft('时间等待', {'时长':0}, note='采集步骤'),
              InstructionDraft('多线程启动', {'线程名称':'识别线程','入口编号':0}),
              InstructionDraft('时间等待', {'时长':0}, note='识别步骤'),
              InstructionDraft('时间等待', {'时长':0}, note='普通主流程'),
              InstructionDraft('时间等待', {'时长':0}, note='共享后续步骤'),
              InstructionDraft('时间等待', {'时长':0}, note='未连接普通指令')]
    a, aw, b, bw, main, common, loose = ids = repo.append_recording(drafts, connect=False)
    node_ids = {n.command_id:n.node_id for n in repo.snapshot().nodes if n.command_id is not None}
    def connect(source, target):
        repo.connect_nodes(node_ids.get(source,source),node_ids.get(target,target))
    for source,target in [('start',a),('start',b),('start',main),(a,aw),(b,bw),
                          (aw,common),(bw,common),(main,common),(common,'end')]:
        connect(source,target)
    groups = folding_groups(repo.list_commands())
    assert groups[a]['members'] == {aw} and groups[b]['members'] == {bw}, groups
    assert locked_move_ids(repo.list_commands(), [aw]) == {a,aw}
    assert locked_move_ids(repo.list_commands(), [common]) == {common}
    # Without the main branch the common tail is still shared, not owned by A or B.
    repo.delete_connection(node_ids[main],node_ids[common])
    assert folding_groups(repo.list_commands())[a]['members'] == {aw}
    connect(main,common)
    coordinates = {a:(-600,200), aw:(-320,310), b:(220,200), bw:(520,340),
                   main:(-600,500),common:(220,500),loose:(600,500)}
    repo.save_node_positions({node_ids[cid]:xy for cid,xy in coordinates.items()})
    repo.save_node_positions({'start':(-900,200),'end':(900,500)})
    graph = NodeEditorWidget(); graph.resize(1100,700)
    host = SimpleNamespace(editor=graph)
    def reload():
        snapshot = repo.snapshot()
        graph.load_graph(snapshot.nodes,snapshot.edges,INSTRUCTION_SPECS,allow_incomplete=True)
        InstructionWorkspace._apply_step_folds(host,snapshot)
        app.processEvents()
    reload(); graph.show(); app.processEvents()
    scene,view = graph.scene,graph.view
    committed = []
    scene.positionsCommitted.connect(lambda positions: (committed.append(dict(positions)),repo.save_node_positions(positions)))
    assert scene.locked_groups[node_ids[a]] == frozenset((node_ids[a],node_ids[aw]))
    assert scene.locked_groups[node_ids[b]] == frozenset((node_ids[b],node_ids[bw]))
    assert node_ids[common] not in scene.locked_groups
    assert scene.nodes_by_command_id[a].header_color.name() == '#3789dc'
    assert scene.nodes_by_command_id[main].header_color.name() != '#3789dc'
    before = repo.snapshot()
    original_display = {key:QPointF(n.pos()) for key,n in scene.nodes_by_id.items()}
    total = QPointF()
    for cid in (a,aw):
        node = scene.nodes_by_command_id[cid]
        view._set_zoom(1)
        hit = node.pos()+QPointF(node.width/2,node.height-6)
        view.centerOn(hit); app.processEvents()
        point = view.mapFromScene(hit)
        # Selecting an unrelated node beforehand must not include it in this drag.
        scene.nodes_by_command_id[main].setSelected(True)
        QTest.mousePress(view.viewport(),Qt.LeftButton,Qt.NoModifier,point)
        assert view._group_drag is not None
        assert set(view._group_drag[1]) == {node_ids[a],node_ids[aw]}
        delta = QPointF(45,-25)
        target = QPointF(point)+delta
        move = QMouseEvent(QEvent.MouseMove,target,Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
        app.sendEvent(view.viewport(),move)
        QTest.mouseRelease(view.viewport(),Qt.LeftButton,Qt.NoModifier,target.toPoint())
        total += delta
        assert set(committed[-1]) == {node_ids[a],node_ids[aw]}
        for key,node in scene.nodes_by_id.items():
            expected = original_display[key] + (total if key in {node_ids[a],node_ids[aw]} else QPointF())
            assert node.pos() == expected, (key,node.pos(),expected)
        after = repo.snapshot()
        assert after.commands == before.commands and after.edges == before.edges
        old = {n.node_id:n for n in before.nodes}
        for node in after.nodes:
            shift = total if node.command_id in (a,aw) else QPointF()
            assert QPointF(node.x,node.y) == QPointF(old[node.node_id].x,old[node.node_id].y)+shift
    translated = {key:QPointF(n.pos()) for key,n in scene.nodes_by_id.items()}
    reload()
    assert all(n.pos() == translated[key] for key,n in scene.nodes_by_id.items())
    node = scene.nodes_by_command_id[aw]
    view.centerOn(node);app.processEvents()
    point=view.mapFromScene(node.pos()+QPointF(node.width/2,node.height-6))
    QTest.mousePress(view.viewport(),Qt.LeftButton,Qt.NoModifier,point)
    view._move_copy_drag(QPointF(point)+QPointF(-70,50))
    view._finish_copy_drag(cancel=True)
    QTest.mouseRelease(view.viewport(),Qt.LeftButton,Qt.NoModifier,point)
    assert all(n.pos() == translated[key] for key,n in scene.nodes_by_id.items())
    repo.set_step_locks([a],False); reload()
    for cid in (a,aw):
        assert scene.nodes_by_command_id[cid].pos() == QPointF(*coordinates[cid])+total
    assert scene.nodes_by_command_id[b].pos() == translated[node_ids[b]]
    print('PASS separate shared/main nodes, any-member relative drag, unchanged outside positions/order/edges, reload, cancel and unlock')
    # Even an intentionally interleaved table order must survive a coordinate-only save.
    with sqlite3.connect(dbpath) as db:
        repo._set_command_orders(db,[a,b,main,aw,bw,common,loose])
    db.close()
    stable = repo.snapshot()
    with patch.object(repo,'_sync_thread_groups',side_effect=AssertionError('layout must not regroup')):
        repo.save_node_position(node_ids[loose],700,600)
        repo.save_node_positions({node_ids[a]:(10,20),node_ids[aw]:(40,70)})
        repo.save_node_size(node_ids[a],300,100)
    after=repo.snapshot()
    assert after.commands == stable.commands and after.edges == stable.edges
    print('PASS single/group position and size writes never regroup or reorder commands')
    # Screenshot retains the real grouped layout, before changing it for the write isolation test.
    repo.save_node_positions({node_ids[cid]:xy for cid,xy in coordinates.items()})
    repo.set_step_locks([a],True); reload(); view.fit_graph();app.processEvents()
    output=Path('artifacts/validation/thread-relative-move');output.mkdir(parents=True,exist_ok=True)
    graph.grab().save(str(output/'independent-thread-groups.png'))
    graph.close()
print('PASS thread relative movement suite')
