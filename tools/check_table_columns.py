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
 w.resize(1180,720);w.show();v=w.view_workspace;v.show_table();app.processEvents()
 table=v.command_table;header=table.horizontalHeader();table.setRowCount(1)
 values=['1','#1','时间等待','秒：2','1','自动跳过','测试备注']
 for column,value in enumerate(values):table.setItem(0,column,QTableWidgetItem(value))
 table.setCurrentCell(0,3)
 widths=[header.sectionSize(i) for i in range(7)]
 selected=[(i.row(),i.column()) for i in table.selectedIndexes()]
 def order(h=header):return [h.logicalIndex(i) for i in range(h.count())]
 for mode in ('dark','light'):
  v.theme_mode=mode;v._apply_theme();app.processEvents()
  def choose_left(menu,point):
   assert [a.text() for a in menu.actions()]==['左移','右移','','恢复默认排序']
   assert menu.actions()[0].isEnabled() and menu.actions()[1].isEnabled()
   menu.popup(point);app.processEvents();menu.grab().save('artifacts/validation/table-columns-menu-'+mode+'.png');menu.close();menu.actions()[0].trigger()
  point=QPoint(header.sectionViewportPosition(3)+20,header.height()//2)
  with patch('anclicker.ui.instruction_table.QMenu.exec',choose_left):
   QApplication.sendEvent(header.viewport(),QContextMenuEvent(QContextMenuEvent.Mouse,point,header.viewport().mapToGlobal(point)))
  assert order()==[0,3,2,1,4,5,6]
  assert [table.item(0,i).text() for i in range(7)]==values
  assert [(i.row(),i.column()) for i in table.selectedIndexes()]==selected
  assert [header.sectionSize(i) for i in range(7)]==widths
  reopened=InstructionTableWidget(0,7);reopened.configure_column_order(db,w);assert order(reopened.horizontalHeader())==order();reopened.deleteLater()
  def edge_menu(menu,point):
   assert not menu.actions()[0].isEnabled();menu.actions()[-1].trigger()
  with patch('anclicker.ui.instruction_table.QMenu.exec',edge_menu):
   table._show_column_order_menu(QPoint(header.sectionViewportPosition(0)+5,header.height()//2))
  assert order()==[0,2,3,1,4,5,6]
  table.move_column(6,1);table.move_column(0,-1);assert order()==[0,2,3,1,4,5,6]
  table.move_column(2,1);assert order()==[0,3,2,1,4,5,6];table.restore_default_column_order()
  assert json.loads(db.get_setting_value('表格列顺序'))==[0,2,3,1,4,5,6]
 db.set_setting_value('表格列顺序','[0,0,2,3,4,5,6]')
 reopened=InstructionTableWidget(0,7);reopened.configure_column_order(db,w);assert order(reopened.horizontalHeader())==list(range(7));reopened.deleteLater()
 w.close();w.ocr_pool.close();app.processEvents()
print('PASS actual header context event, left/right boundaries, reset, persisted reopen, selection/data/widths preserved, invalid order fallback, light/dark menus')
