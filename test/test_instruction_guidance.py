import pytest
from qt_compat.QtWidgets import QApplication
from qt_compat.QtCore import Qt, QCoreApplication, QEvent
from qt_compat.QtGui import QTextCursor, QInputMethodEvent
from qt_compat.QtTest import QTest
from instruction_guidance import matching, next_steps, command_template, suggestions
from instructions.registry import INSTRUCTION_SPECS
from node_editor.palette import InstructionPalette, TYPE_ID_ROLE
from guided_code_editor import GuidedCodeEditor

@pytest.fixture
def app():
    app=QApplication.instance() or QApplication([])
    yield app
    QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
    app.processEvents()

def test_copy_followups_cover_paste_commands_and_click_then_paste():
    choices=next_steps('OCR复制')
    ids={s.kind for s in choices}
    assert {s.type_id for s in INSTRUCTION_SPECS if '粘贴' in s.type_id} <= ids
    assert choices[0].kind=='坐标点击'
    assert next_steps('坐标点击',True)[0].parameters=={'内容来源':'剪贴板'}
    assert not next_steps('坐标点击',False)

@pytest.mark.parametrize('phrase,kind',[('把文字粘贴到表格','粘贴到单元格'),('然后粘贴到网页','粘贴到网页元素'),('复制识别文字','OCR复制'),('先点击一个位置','坐标点击')])
def test_chinese_phrase_candidates(phrase,kind):
    assert kind in {s.kind for s in matching(phrase)}

def test_all_templates_have_registered_parameters():
    for s in suggestions():
        template=command_template(s)
        assert template.startswith(s.kind+'(')
        assert '重复次数=1' in template
    assert '剪贴板' in command_template(next_steps('坐标点击',True)[0])

def test_palette_next_step_payload_and_replacement(app):
    p=InstructionPalette(INSTRUCTION_SPECS)
    p.show_recent_ocr((1,2,30,40))
    p.command_added('OCR复制')
    assert p._quick_ocr_item.childCount()==0
    assert p._guide_item.childCount()>=6
    item=p._guide_item.child(0);p.tree.setCurrentItem(item)
    assert p.quick_parameters('坐标点击')=={}
    p.command_added('坐标点击')
    p.tree.setCurrentItem(p._guide_item.child(0))
    assert p.quick_parameters('OCR粘贴')=={'内容来源':'剪贴板'}
    p.show_recent_capture('another.png')
    assert p._guide_item.childCount()==0
    p.close();p.deleteLater()

def test_code_completion_preserves_other_lines_and_undo(app):
    e=GuidedCodeEditor();e.show();e.setFocus()
    original='# 已有说明\n把文字粘贴到表格'
    e.setPlainText(original);e.moveCursor(QTextCursor.End)
    e.show_suggestions();assert e._choices[0].kind=='粘贴到单元格'
    e._accept(e._choices[0].label)
    assert e.toPlainText().startswith('# 已有说明\n粘贴到单元格(')
    assert 'toCell' in e.toPlainText()
    e.undo();assert e.toPlainText()==original
    e.close();e.deleteLater()

def test_code_tab_selection_and_ime_composition(app):
    e=GuidedCodeEditor();e.show();e.setFocus()
    e.setPlainText('复制识别文字');e.moveCursor(QTextCursor.End);e.show_suggestions()
    QTest.keyClick(e,Qt.Key_Tab)
    assert e.toPlainText().startswith('OCR复制(')
    e.setPlainText('粘贴');e.moveCursor(QTextCursor.End);e.show_suggestions()
    QApplication.sendEvent(e,QInputMethodEvent('wang',[]))
    assert e._composing and not e.completer.popup().isVisible()
    assert e.toPlainText()=='粘贴'
    e.close();e.deleteLater()


def test_editor_cancel_does_not_advance_but_confirm_does(app,tmp_path,monkeypatch):
    from qt_compat.QtWidgets import QWidget,QDialog
    from instruction_workspace import InstructionWorkspace
    from 数据库操作 import DatabaseOperation
    from instructions.models import InstructionDraft
    from instructions.registry import InstructionSpec
    owner=QWidget();owner.db=DatabaseOperation(str(tmp_path/'guide.db'))
    ws=InstructionWorkspace(owner.db.db_path,owner)
    ws.palette.show_recent_ocr((1,2,30,40))
    class Editor:
        accepted=False
        testRequested=None
        def exec(self):return QDialog.Accepted if self.accepted else QDialog.Rejected
        def get_draft(self):return InstructionDraft('OCR复制',{'区域':'(1, 2, 30, 40)'})
    editor=Editor()
    monkeypatch.setattr(InstructionSpec,'create_editor',lambda *a,**k:editor)
    monkeypatch.setattr(ws,'_connect_editor_test',lambda *a:None)
    assert ws.add_command('OCR复制') is None
    app.processEvents()
    assert ws.palette._quick_ocr_item.childCount()==3
    assert not ws.repository.list_commands()
    editor.accepted=True
    assert ws.add_command('OCR复制') is not None
    app.processEvents()
    assert ws.palette._guide_item.childCount()>=6
    assert len(ws.repository.list_commands())==1
    owner.close();owner.deleteLater()
