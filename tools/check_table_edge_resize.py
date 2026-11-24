import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import Qt,QEvent,QPointF,QEventLoop,QTimer
from anclicker.platform.qt_compat.QtGui import QMouseEvent,QPalette,QColor
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTableWidgetItem,QHeaderView
from anclicker.ui.instruction_table import InstructionTableWidget
app=QApplication([])
def wait():
 loop=QEventLoop();QTimer.singleShot(60,loop.quit);loop.exec_()
table=InstructionTableWidget(4,3);table.setHorizontalHeaderLabels(['指令','参数','备注']);table.resize(620,300)
table.horizontalHeader().setMinimumSectionSize(48)
for col,width in enumerate((180,240,300)):table.setColumnWidth(col,width)
for row in range(4):
 for col in range(3):table.setItem(row,col,QTableWidgetItem('备注内容' if col==2 else '测试'))
table.show();wait();grip=table.edge_resize_grip;h=table.horizontalHeader()
assert grip.isVisible() and grip.logical==2
assert grip.geometry().right()==h.viewport().width()-1
selected=table.selected_command_ids()
def drag(dx):
 local=QPointF(grip.rect().center());global_=QPointF(grip.mapToGlobal(grip.rect().center()))
 for kind,point,buttons in ((QEvent.MouseButtonPress,global_,Qt.LeftButton),(QEvent.MouseMove,global_+QPointF(dx,0),Qt.LeftButton),(QEvent.MouseButtonRelease,global_+QPointF(dx,0),Qt.NoButton)):
  e=QMouseEvent(kind,local,point,Qt.LeftButton if kind!=QEvent.MouseMove else Qt.NoButton,buttons,Qt.NoModifier)
  app.sendEvent(grip,e)
 wait()
visible=h.viewport().width()-h.sectionViewportPosition(2);drag(-40)
assert h.sectionSize(2)==visible-40 and table.selected_command_ids()==selected
assert grip.geometry().right()==h.sectionViewportPosition(2)+h.sectionSize(2)-1
before=h.sectionSize(2);drag(50);assert h.sectionSize(2)==before+50
table.resize(500,300);wait();assert grip.geometry().right()==h.viewport().width()-1
table.horizontalScrollBar().setValue(table.horizontalScrollBar().maximum());wait();assert grip.isVisible()
# Follow visual ordering rather than hard-coding the remarks column.
h.moveSection(h.visualIndex(0),2);wait();assert grip.logical==0
h.hideSection(0);wait();assert grip.logical==2
h.showSection(0);h.moveSection(h.visualIndex(0),0);table.resize(620,300);wait()
# At a clipped sliver, the overlapping handle resizes the visible left column.
table.horizontalScrollBar().setValue(0)
for col,width in enumerate((180,240,300)):table.setColumnWidth(col,width)
wait()
table.resize(table.width() + (180+240+6-h.viewport().width()),300);wait()
assert grip.isVisible() and grip.logical==1
left_width=h.sectionSize(1);last_width=h.sectionSize(2)
drag(-30)
assert h.sectionSize(1)==left_width-30 and h.sectionSize(2)==last_width
assert grip.logical==2  # Once separated, the last column is independently draggable.
# The same priority follows visual ordering after column moves.
h.moveSection(h.visualIndex(0),2);wait()
table.horizontalScrollBar().setValue(0)
left_edge=h.sectionViewportPosition(0)
table.resize(table.width()+(left_edge+6-h.viewport().width()),300);wait()
assert grip.logical==2
left_width=h.sectionSize(2);last_width=h.sectionSize(0)
drag(-25)
assert h.sectionSize(2)==left_width-25 and h.sectionSize(0)==last_width
table.resize(620,300);wait()
for mode in ('light','dark'):
 if mode=='dark':
  palette=table.palette();palette.setColor(QPalette.Text,QColor('#eeeeee'));palette.setColor(QPalette.Base,QColor('#242630'));palette.setColor(QPalette.Button,QColor('#343640'));palette.setColor(QPalette.ButtonText,QColor('#eeeeee'));table.setPalette(palette)
 wait();table.grab().save('artifacts/validation/table-edge-'+mode+'.png')
table.close()
print('PASS clipped right-edge visibility, shrinking/growing, minimum width, selection preservation, resize/scroll, column reorder/hide, light/dark rendering')
