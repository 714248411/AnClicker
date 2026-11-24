import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication,QToolButton
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
configure_application();app=QApplication([])
with tempfile.TemporaryDirectory() as directory:
 db=DatabaseOperation(str(Path(directory)/'task.db'))
 with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
  w=Main_window()
 w.register_global_shortcut_keys=lambda:None;w.unregister_global_shortcut_keys=lambda:None
 w.resize(1180,720);w.show();app.processEvents();v=w.view_workspace
 controller=w.view_workspace.toolbar_customization
 controller.sync()
 with patch.object(controller,'collect',wraps=controller.collect) as collect:
  controller.sync();controller.sync();assert collect.call_count==0
  action=w.menu.addAction('动态工具');action.setObjectName('testDynamicTool');controller.sync()
  assert collect.call_count==1
  key=next(key for key,value in controller.sources.items() if value[0] is action)
  controller.select(key,True);assert key in controller.proxies
  action.setText('更新名称');action.setEnabled(False);controller.sync()
  assert controller.proxies[key].text()=='更新名称' and not controller.proxies[key].isEnabled()
  action.setCheckable(True);action.setChecked(True);controller.sync();assert controller.proxies[key].isChecked()
  w.menu.removeAction(action);controller.sync();assert key not in controller.proxies
 for mode in ('dark','light'):
  v.theme_mode=mode;v._apply_theme();app.processEvents()
  controller.populate()
  assert controller.menu._tool_submenus
  expected = '#222225' if mode == 'dark' else '#ffffff'
  assert all(sub._rounded_menu_background.background.name() == expected for sub in controller.menu._tool_submenus)
  for button in w.toolBar.findChildren(QToolButton):
   if button.defaultAction() and not button.icon().isNull() and button.text() in ('保存\tCtrl+S','设置','使用说明','关于'):
    assert not button.property('toolbarTextOnly')
  w.toolBar.grab().save('artifacts/validation/toolbar-1610-'+mode+'.png')
 w.close();w.ocr_pool.close();app.processEvents()
print('PASS cached toolbar collection; add/remove/rename/enabled/checked actions invalidate correctly; toolbar theme and alignment')
