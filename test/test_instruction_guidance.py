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
    assert p._quick_ocr_item.childCount()>0 and not p._quick_ocr_item.isExpanded()
    assert p._guide_item.childCount()>=6
    item=p._guide_item.child(0);p.tree.setCurrentItem(item)
    assert p.quick_parameters('坐标点击')=={}
    p.command_added('坐标点击')
    p.tree.setCurrentItem(p._guide_item.child(0))
    assert p.quick_parameters('OCR粘贴')=={'内容来源':'剪贴板'}
    p.show_recent_capture('another.png')
    assert p._guide_item.childCount()>0 and not p._guide_item.isExpanded()
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


def test_open_web_followups_offer_waits_then_web_actions():
    choices = next_steps('打开网页')
    assert [item.kind for item in choices[:3]] == ['等待（秒）', '等待元素出现', '等待页面加载完成']
    assert {'拾取元素', '点击元素', '输入文本', '粘贴到网页元素', '获取文本'} <= {item.kind for item in choices}
    for wait in choices[:3]:
        assert '点击元素' in {item.kind for item in next_steps(wait.kind)}
        assert wait.kind not in {item.kind for item in next_steps(wait.kind)}
        assert command_template(wait).startswith(wait.kind + '(')
    assert '等待页面加载完成' in {item.kind for item in matching('等待网页加载完毕')}


def test_web_wait_shortcuts_replace_previous_guide(app):
    palette = InstructionPalette(INSTRUCTION_SPECS)
    palette.command_added('打开网页')
    assert palette._web_open_item.text(0) == '打开网页'
    assert palette._web_open_item.isExpanded()
    assert palette._guide_item.childCount() == 0
    expected = ['等待（秒）', '等待元素出现', '等待页面加载完成']
    for index, kind in enumerate(expected):
        item = palette._web_open_item.child(index)
        assert item.data(0, TYPE_ID_ROLE) == kind
        palette.tree.setCurrentItem(item)
        assert palette.quick_parameters(kind) == {}
    palette.command_added('等待元素出现')
    assert palette._guide_item.text(0) == '等待元素出现后，可以…'
    assert palette._guide_item.child(0).data(0, TYPE_ID_ROLE) == '拾取元素'
    palette.close(); palette.deleteLater()


def test_double_click_web_adds_once_and_followups_can_collapse(app,tmp_path,monkeypatch):
    from qt_compat.QtWidgets import QWidget
    from instruction_workspace import InstructionWorkspace
    from 数据库操作 import DatabaseOperation
    from instructions.registry import InstructionSpec
    owner=QWidget();owner.db=DatabaseOperation(str(tmp_path/'web-guide.db'))
    ws=InstructionWorkspace(owner.db.db_path,owner)
    def no_editor(*args,**kwargs):raise AssertionError('Web double-click should insert directly')
    monkeypatch.setattr(InstructionSpec,'create_editor',no_editor)
    web=ws.palette._web_open_item
    ws.palette.tree.setCurrentItem(web)
    ws.palette.tree.itemDoubleClicked.emit(web,0)
    app.processEvents()
    rows=ws.repository.list_commands()
    assert len(rows)==1 and rows[0].type_id=='打开网页'
    assert rows[0].parameters['engine']=='跟随当前'
    count=web.childCount()
    assert count>=8 and web.isExpanded()
    ws.palette.tree.collapseItem(web)
    assert not web.isExpanded() and web.childCount()==count
    ws.palette.tree.expandItem(web)
    assert web.isExpanded() and len(ws.repository.list_commands())==1
    ws.palette.tree.setCurrentItem(web.child(0))
    assert ws.palette.quick_parameters('等待（秒）')=={}
    ws.palette.show_recent_capture('new.png')
    assert web.childCount()>0 and not web.isExpanded()
    owner.close();owner.deleteLater()
