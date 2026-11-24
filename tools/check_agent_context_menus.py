"""User-facing right-click edit/delete operations and restart persistence."""
import runpy,json
from unittest.mock import patch
from anclicker.ui.agent_view import AgentView
from anclicker.ui.local_model_dialog import LocalModelDialog
from anclicker.platform.qt_compat.QtWidgets import QMenu,QMessageBox
from anclicker.domain.instructions import InstructionDraft
ns=runpy.run_path('tools/check_agent_history.py');app=ns['app'];window=ns['window'];window.db=ns['Database']()
with patch.object(AgentView,'_activate_local_model'),patch.object(AgentView,'refresh_resources'):
 view=AgentView(window);view.resize(1100,760);view.show()
 view.add_message('user','删除测试甲');view.session.drafts=[InstructionDraft('时间等待',{'时长':n,'单位':'秒'}) for n in (1,2,3)]
 view.render_drafts();app.processEvents()
 def move_menu(menu,position):
  assert [a.text() for a in menu.actions()]==['删除','上移','下移']
  assert menu.actions()[1].isEnabled();menu.actions()[1].trigger()
 with patch.object(QMenu,'exec',move_menu):view.draft_context_menu(view.preview.visualRect(view.preview.model().index(1,0)).center())
 assert [d.parameters['时长'] for d in view.session.drafts]==[2,1,3]
 first=view._chat_id;view.new_chat();view.add_message('user','删除测试乙');view._save_history();second=view._chat_id
 view._refresh_history_menu();view.history_menu.popup(view.mapToGlobal(view.rect().center()));app.processEvents();target=next(a for a in view.history_menu.actions() if a.data()==first)
 def delete_menu(menu,position):
  assert [a.text() for a in menu.actions()]==['删除'];menu.actions()[0].trigger()
 with patch.object(QMenu,'exec',delete_menu),patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
  view.history_context_menu(view.history_menu.actionGeometry(target).center())
 assert first not in [e['id'] for e in view._history] and view._chat_id==second
 with patch.object(QMessageBox,'question',return_value=QMessageBox.No):view.delete_history(second)
 assert view._chat_id==second
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):view.delete_history(second)
 assert view._chat_id!=second and not view.session.drafts and not view.input.toPlainText()
 view._save_history();assert json.loads(window.db.values['对话Agent历史'])==[]
 restored=AgentView(window);assert not restored._history
 with patch.object(LocalModelDialog,'exec',return_value=0) as opened:view.badge.click();assert opened.called
 for w in (view,restored):w.resource_timer.stop();w.history_timer.stop();w.close()
print('PASS right-click draft order, historical delete/cancel, current reset, no resurrection on restart, model badge entry')
