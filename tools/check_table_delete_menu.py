"""Deletion is dispatched after the context popup releases its event filter."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QPoint, Qt
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem
from anclicker.ui import instruction_table

app = QApplication.instance() or QApplication([])
table = instruction_table.InstructionTableWidget()
table.setColumnCount(3)
table.setRowCount(1)
item = QTableWidgetItem('test')
item.setData(Qt.UserRole, 42)
table.setItem(0, 0, item)
table.selectRow(0)
table.show()
app.processEvents()
calls = []
table.deleteRequested.connect(lambda: calls.append(table.selected_command_ids()))

def choose(left, right, position, owner):
    action = next(a for a in left.actions() if a.text().startswith('删除选中指令'))
    assert action.isEnabled()
    action.trigger()
    assert not calls, 'Deletion opened while the popup event filter was active'
    return action

with patch.object(instruction_table, 'exec_two_column_menu', choose):
    point = table.visualItemRect(item).center()
    table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, point, table.mapToGlobal(point)))
assert calls == [[42]], calls
print('PASS selected row deletion dispatched once after context menu closes')
