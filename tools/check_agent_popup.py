from types import SimpleNamespace
from unittest.mock import patch
from anclicker.platform.qt_compat.QtCore import QObject,QPoint
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QMainWindow,QTabWidget,QMenu
from anclicker.ui.agent_view import AgentView
from anclicker.ui.dock_workspace import DockWorkspace
from anclicker.domain.instructions import InstructionDraft
class Database:
    def __init__(self):self.values={}
    def get_setting_value(self,key):return self.values.get(key)
    def set_setting_value(self,key,value):self.values[key]=value
class Session:
    def __init__(self):self.drafts=[];self.history=[];self.pending_plan_text=''
    def close(self):pass
app=QApplication([])
window=QMainWindow();window.db=Database()
with patch('anclicker.ui.agent_view.create_agent_session',Session),patch.object(AgentView,'_activate_local_model'),patch.object(AgentView,'refresh_resources'):
    page=AgentView(window)
    page.add_message('user','保留对话');page.input.setPlainText('未发送内容')
    page.session.drafts=[InstructionDraft('运行cmd',{'命令':'echo test'})]
    page.render_drafts();page.key.setText('test-only-key')
    session=page.session
    tabs=QTabWidget();tabs.addTab(QWidget(),'主界面');tabs.addTab(page,'对话Ai编程')
    host=QMainWindow();host.setCentralWidget(tabs);window.setCentralWidget(host)
    manager=DockWorkspace.__new__(DockWorkspace);QObject.__init__(manager,window)
    manager.window=window;manager.host=host;manager.view=SimpleNamespace(tabs=tabs)
    manager.pages={'main':tabs.widget(0),'agent':page};manager.titles={'main':'主界面','agent':'对话Ai编程'}
    manager.docks={};manager.placeholders={};manager.parameters={};manager.editable=False;manager.schedule_save=lambda:None
    window.view_workspace=SimpleNamespace(docking=manager)
    assert manager.tab_key(1)=='agent' and manager.tab_key(-1) is None
    menus=[]
    with patch.object(QMenu,'exec',lambda menu,pos:menus.extend(action.text() for action in menu.actions())):
        manager.panel_menu('agent',QPoint())
    assert '弹出对话Ai编程（含设置与流程草稿）' in menus
    window.resize(1200,800);window.show();manager.float_panel('agent',True);app.processEvents()
    dock=manager.docks['agent']
    assert dock.isFloating() and dock.widget().widget() is page
    assert page.details.isVisible() and page.session is session
    assert page.input.toPlainText()=='未发送内容' and page.key.text()=='test-only-key'
    assert page.session.drafts[0].parameters['命令']=='echo test'
    assert manager.tab_key(1)=='agent'
    dock.grab().save('.local/cache/agent-popup.png')
    dock.close();app.processEvents()
    assert tabs.widget(1) is page and 'agent' not in manager.docks
    assert page.session is session and len(page.session.drafts)==1
    page.resource_timer.stop();page.history_timer.stop();window.close()
print('PASS: right-click entry, locked-layout popup, entire Agent with settings/drafts, state preservation, close to restore')
