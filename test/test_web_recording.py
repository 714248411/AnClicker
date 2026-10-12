import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch
import pytest
from instructions.common.rpa_bridge import RpaBridge
from web_recording import events_to_web_drafts

def test_recording_preserves_waits_coalesces_input_and_keeps_tail():
    drafts=events_to_web_drafts('https://example.com',[
        {'type':'click','selector':'#q','at':250},
        {'type':'input','selector':'#q','text':'a','at':400},
        {'type':'input','selector':'#q','text':'abc','at':900},
        {'type':'key','selector':'#q','key':'Enter','at':1200},
        {'type':'navigation','url':'https://example.com/result','at':1300}],2000)
    assert [d.parameters['seconds'] for d in drafts if d.type_id=='等待（秒）']==[.25,.65,.3,.1,.7]
    assert [d.parameters['text'] for d in drafts if d.type_id=='输入文本']==['abc']
    assert sum(d.type_id=='打开网页' for d in drafts)==1
    assert any(d.type_id=='等待页面加载完成' for d in drafts)

def test_real_browser_records_trusted_input_navigation_and_wait(tmp_path,monkeypatch):
    monkeypatch.setenv('ANCLICKER_DATA_DIR',str(tmp_path))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=(b'<input id="second" autofocus>' if self.path.startswith('/next') else
                  b'<input id="first" autofocus><button onclick="location.href=\'/next\'">Next</button>')
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    bridge=RpaBridge('recorder-test')
    def call(kind,params=None):return bridge.execute({'id':kind,'params':params or {}}).get('result')
    try:
        url=f'http://127.0.0.1:{server.server_port}'
        call('openUrl',{'url':url,'engine':'Chrome','target':'新窗口','waitType':'加载完成'})
        call('input',{'selector':'#first','by':'CSS选择器','text':'','clear':'是','pressEnter':'否'})
        call('acRecordStart')
        time.sleep(.15)
        call('pressKey',{'key':'自定义','customKey':'a'})
        call('pressKey',{'key':'Tab'})
        call('pressKey',{'key':'回车(Enter)'})
        call('waitElement',{'selector':'#second','by':'CSS选择器','timeout':5})
        call('input',{'selector':'#second','by':'CSS选择器','text':'','clear':'是','pressEnter':'否'})
        call('pressKey',{'key':'自定义','customKey':'a'})
        time.sleep(.15)
        recording=call('acRecordStop')
        events=recording['events']
        assert any(e['type']=='input' and e['selector']=='#first' for e in events),events
        assert any(e['type']=='navigation' for e in events),events
        assert any(e['type']=='input' and e['selector']=='#second' for e in events),events
        assert not any(e['type']=='click' for e in events), 'Enter should not duplicate its generated click'
        drafts=events_to_web_drafts(url,events,recording['elapsed'])
        assert sum(d.parameters['seconds'] for d in drafts if d.type_id=='等待（秒）')>=.3
        before=len(events)
        call('pressKey',{'key':'自定义','customKey':'a'})
        assert len(call('acRecordStatus')['events'])==before
    finally:
        bridge.close();server.shutdown();server.server_close()

def test_ocr_anchor_uses_same_point_picker_and_options_share_row():
    from qt_compat.QtWidgets import QApplication, QDialog
    from instructions.registry import get_instruction_spec
    app=QApplication.instance() or QApplication([])
    editor=get_instruction_spec('OCR点击识别区域').create_editor()
    editor._controls['点击来源'].setCurrentText('重新识别')
    editor.ocr_advanced_button.setChecked(True)
    with patch('instructions.common.editor._PointSelectionDialog') as picker:
        picker.return_value.exec.return_value=QDialog.DialogCode.Accepted
        picker.return_value.point=(-120,330);picker.return_value.capture_error=None
        index=next(i for i,f in enumerate(editor.FIELDS) if f.key=='中心锚点')
        getattr(editor.ui,f'auxiliary_{index}').click()
    assert editor.get_draft().parameters['中心锚点']=='-120,330'
    editor.show();app.processEvents()
    first=editor._controls['忽略大小写'];second=editor._controls['忽略空白']
    assert first.parentWidget().parentWidget() is editor.ocr_match_options
    assert second.parentWidget().parentWidget() is editor.ocr_match_options
    assert first.mapTo(editor,first.rect().center()).y()==second.mapTo(editor,second.rect().center()).y()
    assert first.mapTo(editor,first.rect().center()).x()<second.mapTo(editor,second.rect().center()).x()
    editor.close()


def test_web_recording_view_stops_previews_and_writes_once(tmp_path):
    from types import SimpleNamespace
    from qt_compat.QtCore import QObject, Signal
    from qt_compat.QtTest import QTest
    from qt_compat.QtWidgets import QApplication, QMainWindow
    from graph_repository import GraphRepository
    from 数据库操作 import DatabaseOperation
    from web_recording_view import WebRecordingView
    app=QApplication.instance() or QApplication([])
    class Workspace(QObject):
        graphFinalized=Signal(bool)
    window=QMainWindow();workspace=Workspace()
    db=DatabaseOperation(str(tmp_path/'recording.db'))
    workspace.repository=GraphRepository(db.db_path);workspace.reload_graph=Mock()
    window.workspace=workspace;window.command_thread=SimpleNamespace(isRunning=lambda:False)
    window.view_workspace=SimpleNamespace(recording_page=SimpleNamespace(busy=False))
    page=WebRecordingView(window)
    def execute(command):
        if command['id']=='acRecordStart':return {'result':{'active':True,'url':'https://img.hao123.com/manual_res_2023/redict/to_www.html'}}
        if command['id']=='acRecordStop':return {'result':{'active':False,'elapsed':1500,'events':[{'type':'click','selector':'#go','at':500}]}}
        return {'result':{'active':True,'count':0,'elapsed':0,'events':[]}}
    page.bridge=Mock();page.bridge.execute.side_effect=execute
    page.url.setText('https://example.com');page.begin()
    deadline=time.monotonic()+3
    while page.worker is not None and time.monotonic()<deadline:QTest.qWait(10)
    assert page.active and not page.start_button.isEnabled()
    assert page.recorded_url == 'https://example.com'
    page.finish()
    while page.worker is not None and time.monotonic()<deadline:QTest.qWait(10)
    assert not page.busy
    assert [d.type_id for d in page.drafts]==['打开网页','等待（秒）','点击元素','等待（秒）']
    page.write();page.write()
    assert len(workspace.repository.list_commands())==4
    workspace.repository.validate_graph()
    assert page.written and not page.write_button.isEnabled()
    page.shutdown();page.deleteLater();window.close();window.deleteLater()
    from qt_compat.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    app.processEvents()


def test_manual_address_navigation_becomes_an_open_command():
    drafts=events_to_web_drafts('https://example.com',[{'type':'directNavigation','url':'https://example.org','at':500}],600)
    opens=[d for d in drafts if d.type_id=='打开网页']
    assert len(opens)==2
    assert opens[1].parameters['url']=='https://example.org'
    assert opens[1].parameters['target']=='当前标签页'


def test_entered_site_names_and_paths_keep_their_destination():
    from web_urls import normalize_web_url
    assert normalize_web_url('hao123') == 'https://www.hao123.com'
    assert normalize_web_url('https://hao123/path?q=1#section') == 'https://www.hao123.com/path?q=1#section'
    assert normalize_web_url('localhost:8000/path') == 'https://localhost:8000/path'
    with pytest.raises(ValueError):
        normalize_web_url('https://')
