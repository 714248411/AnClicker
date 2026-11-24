import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest.mock import patch
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMessageBox
from anclicker.platform.qt_compat.QtCore import QTimer, Qt
from PySide2.QtTest import QTest
app=QApplication.instance() or QApplication([])
dialogs=[]
for mode in ('header','single','whole','cancel','enter','last'):
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'test.db'
        with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
        db.close()
        repo=GraphRepository(str(path))
        ids=repo.append_recording([InstructionDraft('折叠步骤',{'下方条数':2,'整体锁定':True})]+[InstructionDraft('时间等待',{'时长':0}) for _ in range(3)])
        errors=[]
        host=SimpleNamespace(repository=repo,parent_window=None,reload_graph=lambda:None,
             graphFinalized=SimpleNamespace(emit=lambda *a:None),statusMessage=SimpleNamespace(emit=lambda *a:None),
             _show_error=lambda *a:errors.append(a))
        before=repo.snapshot()
        def execute(box):
            dialogs.append(box)
            if mode=='header': return QMessageBox.Ok
            buttons={b.text():b for b in box.buttons()}
            assert set(buttons)=={'单行删除','整体删除','取消'}
            assert box.defaultButton() is buttons['单行删除']
            assert box.escapeButton() is buttons['取消']
            if mode=='enter':
                box.defaultButton().click()
            else:
                text={'whole':'整体删除','cancel':'取消'}.get(mode,'单行删除')
                buttons[text].click()
            return box.result()
        with patch.object(QMessageBox,'exec',execute):
            selected=[ids[0]] if mode=='header' else ids[1:3] if mode=='last' else [ids[1]]
            count=InstructionWorkspace.remove_commands(host,selected)
        assert not errors,errors
        remaining={c.id for c in repo.list_commands()}
        if mode in ('header','whole'):
            assert count==3 and remaining=={ids[3]}
        elif mode=='cancel':
            assert count==0 and repo.snapshot()==before
        else:
            members=folding_groups(repo.list_commands())[ids[0]]['members']
            assert members==(set() if mode=='last' else {ids[2]})
            assert ids[3] in remaining
print('PASS: locked header deletes group, three choices, default single, cancel, surviving and empty membership')
