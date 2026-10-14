import json,time
from unittest.mock import patch
from qt_compat.QtWidgets import QApplication,QMessageBox,QLabel
from qt_compat.QtTest import QTest
from qt_compat.QtCore import Qt
from test.test_hidden_stop import host
from agent_protocol import make_draft
from agent_provider import ModelClient

def wait(page):
    deadline=time.monotonic()+5
    while page.busy and time.monotonic()<deadline:QTest.qWait(10)
    assert not page.busy

def test_agent_navigation_mock_model_write_once_and_secret_not_saved(host,tmp_path):
    page=host.view_workspace.agent_page
    host.view_workspace.show_agent();assert host.view_workspace.tabs.currentWidget() is page
    assert host.view_workspace.docking.titles['agent']=='对话 Agent'
    page.key.setText('test-secret-never-persist')
    call={'name':'draft_append','arguments':{'type_id':'时间等待','parameters':{'时长':2}},'id':''}
    response=[{'message':{'role':'assistant','content':'{}'},'text':'','call':call},
              {'message':{'role':'assistant','content':'已生成等待草稿'},'text':'已生成等待草稿','call':None}]
    page.input.setPlainText('编写等待2秒')
    with patch.object(ModelClient,'chat',side_effect=response):page.send();wait(page)
    assert page.session.drafts, '; '.join(label.text() for label in page.findChildren(QLabel) if label.text().startswith('未完成'))
    assert page.session.drafts[0].parameters['时长']==2
    assert not host.workspace._instruction_test_active
    assert 'test-secret' not in host.db.get_setting_value('对话Agent设置')
    count=len(host.workspace.repository.list_commands());page.write();page.write()
    assert len(host.workspace.repository.list_commands())==count+1
    assert page.written and not page.unsaved
    page.shutdown()

def test_agent_stop_waiting_model_releases_workspace(host):
    page=host.view_workspace.agent_page
    def slow(self,history,context):
        while not context.stop_requested:time.sleep(.01)
        raise InterruptedError('停止')
    page.input.setPlainText('查看网页')
    with patch.object(ModelClient,'chat',slow):
        page.send();assert host.workspace._instruction_test_active;page.stop();wait(page)
    assert not host.workspace._instruction_test_active
    page.shutdown()

def test_agent_draft_validation_blocks_invalid_coordinates(host):
    page=host.view_workspace.agent_page
    page.session.drafts=[make_draft('移动鼠标',{'类型':'指定坐标','坐标':'wrong'})]
    count=len(host.workspace.repository.list_commands())
    with patch.object(QMessageBox,'warning') as warning:page.write()
    assert warning.called and len(host.workspace.repository.list_commands())==count
    page.session.drafts=[];page.shutdown()


def test_worker_progress_does_not_override_qobject_event():
    from agent_view import AgentWorker
    from qt_compat.QtCore import QEvent
    from agent_provider import AgentSettings
    from agent_runtime import AgentSession
    worker=AgentWorker(AgentSession(object()),'',AgentSettings(),None)
    assert worker.event(QEvent(QEvent.User)) is True


def test_new_chat_uses_configured_session_factory_and_preserves_cancelled_drafts(host):
    from types import SimpleNamespace
    from unittest.mock import Mock
    page=host.view_workspace.agent_page
    old=page.session
    old.drafts=[make_draft('时间等待',{'时长':2})]
    fresh=SimpleNamespace(drafts=[],close=Mock(),api_url='http://127.0.0.1:8767')
    with patch('agent_view.create_agent_session',return_value=fresh) as factory,patch.object(old,'close',wraps=old.close) as close:
        with patch.object(QMessageBox,'question',return_value=QMessageBox.No):page.new_chat()
        assert page.session is old and len(old.drafts)==1
        factory.assert_not_called();close.assert_not_called()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):page.new_chat()
        factory.assert_called_once_with();close.assert_called_once_with()
        assert page.session is fresh and page.session.api_url and not page.session.drafts
        assert not page.written and page.preview.rowCount()==0
    page.shutdown()
