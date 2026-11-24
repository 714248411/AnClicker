import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import Qt,QPoint,QEvent
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTableWidgetItem
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.instruction_table import InstructionTableWidget
configure_application();app=QApplication([])
with tempfile.TemporaryDirectory() as directory:
 db=DatabaseOperation(str(Path(directory)/'task.db'))
 with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
  w=Main_window()
 w.register_global_shortcut_keys=lambda:None;w.unregister_global_shortcut_keys=lambda:None
 from anclicker.platform.qt_compat.QtWidgets import QTabBar
 import time
 def settle():
  end=time.monotonic()+.5
  while time.monotonic()<end:app.processEvents();time.sleep(.01)
 w.resize(1180,744);w.show();v=w.view_workspace;settle()
 assert v.tabs.currentWidget() is v.table_page
 assert [v.command_table.horizontalHeader().logicalIndex(i) for i in range(7)] == [0,2,3,1,4,5,6]
 assert not w.toolBar.isVisible() and not w.actiong.isChecked()
 print('ordinary',v.docking.docks['palette'].width(),v.docking.docks['controls'].width(),v.table_splitter.sizes())
 w.grab().save('artifacts/validation/default-layout-light.png')
 v.layout_presets.apply('dynamic2');settle()
 for width in (1180,1450,900):
  w.resize(width,744);settle()
  d=v.docking
  assert d.docks['controls'] in d.host.tabifiedDockWidgets(d.docks['palette'])
  bars=[b for b in d.host.findChildren(QTabBar) if b is not v.tabs.tabBar() and b.isVisible() and b.count()==2]
  assert bars
  bar=bars[0]
  assert all(bar.rect().contains(bar.tabRect(i)) for i in range(2)),(width,bar.size(),[bar.tabRect(i) for i in range(2)])
  print('dynamic',width,d.docks['palette'].width(),[bar.tabText(i) for i in range(2)])
  d.docks['controls'].raise_();settle()
  assert not d.docks['controls'].visibleRegion().isEmpty()
  w.resize(width+10,744);settle()
  assert not d.docks['controls'].visibleRegion().isEmpty()
  d.docks['palette'].raise_();settle()
 w.resize(1180,744);settle()
 for mode in ('light','dark'):
  v.theme_mode=mode;v._apply_theme();settle()
  w.grab().save('artifacts/validation/dynamic-default-'+mode+'.png')
 # A manual toolbar choice remains usable and survives DB initialization.
 w.actiong.trigger();settle();assert w.toolBar.isVisible()
 db.set_setting_value('显示工具栏','True')
 reopened=DatabaseOperation(db.db_path);assert reopened.get_bool_setting('显示工具栏')
 v.layout_presets.reset();settle()
 assert not w.toolBar.isVisible()
 assert not v.docking.host.tabifiedDockWidgets(v.docking.docks['palette'])
 w.close();w.ocr_pool.close();app.processEvents()
print('PASS default table layout, hidden toolbar, dynamic tabs across widths/themes, active tab preservation and reset')
