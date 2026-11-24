"""Native Qt regression: popup tooltip crash, persistent moves and table run-from."""
import sys,tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QEvent,QPoint,QTimer,Qt
from anclicker.platform.qt_compat.QtGui import QHelpEvent,QContextMenuEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QMenu,QTableWidgetItem
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.ui.tooltip_policy import TooltipPolicy
from anclicker.ui.two_column_menu import MenuColumn,TwoColumnMenu
from anclicker.ui.context_menu_style import style_context_menu
from anclicker.ui.dialogs.窗口状态 import install_window_state
from anclicker.storage.database import DatabaseOperation
import anclicker.ui.instruction_table as table_module
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
 db=DatabaseOperation(str(Path(folder)/'state.db'))
 window=QMainWindow(None,Qt.FramelessWindowHint);window.db=db;window.menu_2=QMenu(window)
 table=table_module.InstructionTableWidget(window);window.setCentralWidget(table)
 window.resize(800,600);window.show();app.processEvents()
 policy=TooltipPolicy(window)
 left,right=MenuColumn(table),MenuColumn(table)
 left.addAction('操作');right.addAction('插入');style_context_menu(left,window);style_context_menu(right,window)
 popup=TwoColumnMenu(left,right,table)
 errors=[]
 def hover():
  try:
   # The popup is a direct child of the item view but is not viewport content.
   for obj in (popup,left,right,table,table.viewport()):
    pos=QPoint(12,12)
    QApplication.sendEvent(obj,QHelpEvent(QEvent.ToolTip,pos,obj.mapToGlobal(pos)))
  except BaseException as e:errors.append(e)
  popup.close()
 QTimer.singleShot(1500,hover);popup.exec(QPoint(120,120));assert not errors,errors
 print('PASS delayed tooltip over popup/columns/table without native crash',flush=True)
 table.setColumnCount(3);table.setRowCount(2)
 for row,cid in enumerate((93,108)):
  item=QTableWidgetItem(str(cid));item.setData(Qt.UserRole,cid);table.setItem(row,0,item)
 received=[];table.runFromRequested.connect(received.append)
 def choose(left,right,position,owner):
  action=next(a for a in left.actions() if a.text()=='在此指令运行')
  assert action.isEnabled();return action
 original=table_module.exec_two_column_menu;table_module.exec_two_column_menu=choose
 point=table.visualItemRect(table.item(1,0)).center()
 table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,point,table.viewport().mapToGlobal(point)))
 assert received==[108],received
 def blank(left,right,position,owner):
  action=next(a for a in left.actions() if a.text()=='在此指令运行');assert not action.isEnabled();return None
 table_module.exec_two_column_menu=blank
 point=QPoint(10,table.viewport().height()-10)
 table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,point,table.viewport().mapToGlobal(point)))
 assert received==[108]
 table_module.exec_two_column_menu=original
 print('PASS table run-from uses clicked command ID; blank area disabled',flush=True)
 controller=install_window_state(window,db,'position-probe',remember_position=True,enable_maximize_button=False)
 window.move(130,140);QTest.qWait(650)
 saved=db.get_window_state('position-probe');assert saved['position']==(130,140),saved
 window.move(160,170);QTest.qWait(650)
 saved=db.get_window_state('position-probe');assert saved['position']==(160,170),saved
 window.close()
 second=QMainWindow(None,Qt.FramelessWindowHint);install_window_state(second,db,'position-probe',remember_position=True,enable_maximize_button=False);second.show();QTest.qWait(100)
 assert second.pos()==QPoint(160,170),second.pos();second.close()
 print('PASS repeated moves persist before closing and reopen at saved position',flush=True)
