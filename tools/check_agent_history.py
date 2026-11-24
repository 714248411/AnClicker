from anclicker.platform.qt_compat.QtWidgets import QPlainTextEdit,QLabel
import json
from types import SimpleNamespace
from unittest.mock import patch
from anclicker.ui.agent_view import AgentView
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.agent_protocol import export_drafts
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
class Database:
    def __init__(self):self.values={}
    def get_setting_value(self,key):return self.values.get(key)
    def set_setting_value(self,key,value):self.values[key]=value
class Session:
    def __init__(self):self.drafts=[];self.history=[];self.pending_plan_text=''
    def close(self):pass
app=QApplication([])
window=QWidget();window.db=Database()
with patch('anclicker.ui.agent_view.create_agent_session',Session), patch.object(AgentView,'_activate_local_model'),patch.object(AgentView,'refresh_resources'):
    view=AgentView(window)
    view._refresh_history_menu();assert view.history_menu.actions()[0].text()=='暂无历史对话'
    view.add_message('user','第一条需求')
    view.add_message('assistant','第一条回复')
    view.session.drafts=[InstructionDraft('运行cmd',{'命令':'echo first'})]
    view.session.history=[{'role':'user','content':'第一条需求'}]
    view.session.pending_plan_text='等待补充'
    view.input.setPlainText('未发送输入')
    first=view._chat_id
    view.new_chat()
    assert not view.session.drafts and len(view._history)==1
    view.add_message('user','第二条需求')
    view.session.drafts=[InstructionDraft('运行cmd',{'命令':'echo second'})]
    view.written=True
    second=view._chat_id
    view._restore_chat(first)
    assert view.session.drafts[0].parameters['命令']=='echo first'
    assert view.input.toPlainText()=='未发送输入' and not view.written
    assert view.session.pending_plan_text=='等待补充'
    assert view.session.history[0]['content']=='第一条需求'
    view._restore_chat(second)
    assert view.written and view.session.drafts[0].parameters['命令']=='echo second'
    view._refresh_history_menu();assert len(view.history_menu.actions())==2
    # Replay failures without screenshots must never prevent startup.
    failure={'verified':False,'error':'目标窗口未找到','missing':None,'text':None}
    view.on_event('verification_evidence',failure)
    view.on_event('verification_evidence',{'screenshot':'.local/cache/no-such-evidence.png','error':'旧截图已移除'})
    view._save_history()
    view2=AgentView(window)
    assert any('目标窗口未找到' in x.toPlainText() for x in view2.findChildren(QPlainTextEdit))
    assert any('截图不可用' in x.text() for x in view2.findChildren(QLabel))
    for evidence in (None,{}, {'screenshot':123}, {'screenshot':'bad\\0path'}, {'screenshot':__file__}):
        view2.add_evidence(evidence)

    assert view2._chat_id==second and view2.written
    view.written=False
    view.session.drafts=[InstructionDraft('时间等待',{'时长':n,'单位':'秒'}) for n in (1,2,3)]
    view.render_drafts();view.preview.selectRow(1);view.update_buttons()
    view.move_draft(-1);assert [d.parameters['时长'] for d in view.session.drafts]==[2,1,3]
    assert not view.move_up_button.isEnabled()
    view.move_draft(1);assert [d.parameters['时长'] for d in view.session.drafts]==[1,2,3]
    view.delete_draft();assert [d.parameters['时长'] for d in view.session.drafts]==[1,3]
    assert [d['parameters']['时长'] for d in export_drafts(view.session.drafts)['instructions']]==[1,3]
    saved=view._chat_id;view.new_chat();view._restore_chat(saved)
    assert [d.parameters['时长'] for d in view.session.drafts]==[1,3]
    view.written=True;view.delete_draft();view.move_draft(-1);assert len(view.session.drafts)==2
    view.written=False
    for i in range(23):
        view.new_chat();view.add_message('user','history '+str(i));view._save_history()
    assert len(view._history)==20
    assert len(json.loads(window.db.values['对话Agent历史']))==20
    assert first not in [item['id'] for item in view._history]
    view._refresh_history_menu();assert len(view.history_menu.actions())==20
    view.worker=object();previous=view._chat_id;view.new_chat();view._restore_chat(view._history[-1]['id']);assert view._chat_id==previous
    view.worker=None;view.resize(1000,720);view.show();app.processEvents()
    view.grab().save('.local/cache/agent-history.png')
    view.history_menu.popup(view.history_button.mapToGlobal(view.history_button.rect().bottomLeft()));app.processEvents()
    view.history_menu.grab().save('.local/cache/agent-history-menu.png')
    view.history_menu.hide()
    view.resource_timer.stop();view.history_timer.stop();view2.resource_timer.stop();view2.history_timer.stop()
    view.close();view2.close()
print('PASS: history menu, separate drafts, model context, composer, written state, restart, 20-record limit and busy guards')
