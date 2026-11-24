"""Palette category defaults, saved expansion and temporary search expansion."""
from pathlib import Path
import sys,tempfile,json
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.node_editor.palette import InstructionPalette
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.storage.database import DatabaseOperation

def groups(p):return {p.tree.topLevelItem(i).text(0):p.tree.topLevelItem(i) for i in range(p.tree.topLevelItemCount())}
def expanded(p):return {name for name,item in groups(p).items() if item.isExpanded()}
def main():
    configure_application();app=QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        db=DatabaseOperation(str(Path(folder)/'state.db'))
        def create():
            p=InstructionPalette(INSTRUCTION_SPECS)
            p.restore_expanded_groups(json.loads(db.get_setting_value('指令栏展开分类') or '[]'))
            p.expandedGroupsChanged.connect(lambda names:db.set_setting_value('指令栏展开分类',json.dumps(names,ensure_ascii=False)))
            return p
        p=create();assert not expanded(p)
        names=list(groups(p));a,b=names[1:3]
        groups(p)[a].setExpanded(True);groups(p)[b].setExpanded(True)
        assert expanded(p)=={a,b}
        saved=db.get_setting_value('指令栏展开分类')
        p.search_edit.setText('网页');app.processEvents()
        assert db.get_setting_value('指令栏展开分类')==saved
        p.search_edit.clear();assert expanded(p)=={a,b}
        p.command_added('打开网页',{});assert db.get_setting_value('指令栏展开分类')==saved
        p.set_specs(INSTRUCTION_SPECS);assert expanded(p)=={a,b}
        q=create();assert expanded(q)=={a,b}
        groups(q)[a].setExpanded(False)
        r=create();assert expanded(r)=={b}
        r.tree.expandAll();assert len(expanded(r))==len(groups(r))
        t=create();assert expanded(t)==set(groups(t))
        t.tree.collapseAll();assert not expanded(create())
        t.restore_expanded_groups({'invalid':True});assert not expanded(t)
        for panel in (p,q,r,t):panel.close()
    print('PASS initially collapsed; manual expand/collapse persists; search and guidance do not overwrite; rebuild/restart restores; expand-all/collapse-all persisted')
    return 0
if __name__=='__main__':raise SystemExit(main())
