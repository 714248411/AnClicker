"""Expanded table borders and stateful loop menu regression."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from anclicker.ui.instruction_table import InstructionTableWidget
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QMenu
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtGui import QColor, QPalette, QContextMenuEvent
app = QApplication.instance() or QApplication([])
table = InstructionTableWidget(7, 7)
table.resize(1000, 500)
table.setColumnWidth(2, 260)
for row in range(7):
    for col in range(7):
        item = QTableWidgetItem('循环' if row == 0 else '时间等待')
        item.setToolTip(item.text())
        item.setData(Qt.UserRole, row + 1)
        table.setItem(row, col, item)
table.loop_ranges = {1: {2,3,4,5}}
table.step_groups = {2: dict(number=1, members={3,4}, collapsed=False, locked=False)}
table.apply_comment_folds()
table.show(); app.processEvents()
assert table._expanded_border_runs == [(1,2,3),(0,1,4)]
rects = table._expanded_border_rects()
assert rects[0][0] > rects[1][0]
assert rects[1][1] == table.rowViewportPosition(1)
assert rects[1][3] == table.rowViewportPosition(4) + table.rowHeight(4) - 1
for background, foreground in (('#ffffff','#000000'),('#101010','#ffffff')):
    palette = table.palette(); palette.setColor(QPalette.Base, QColor(background))
    table.setPalette(palette); app.processEvents()
    image = table.viewport().grab().toImage()
    left, top, right, bottom = table._expanded_border_rects()[1]
    assert image.pixelColor(left, top+8).name() == foreground
    assert image.pixelColor(right, top+8).name() == foreground
    assert image.pixelColor((left+right)//2, bottom).name() == foreground
old_right = table._expanded_border_rects()[1][2]
table.setColumnWidth(2, 310)
assert table._expanded_border_rects()[1][2] == old_right + 50
point = table.visualItemRect(table.item(0,2)).center()
for expected in ('折叠循环内容','展开循环内容'):
    def execute(menu, *args):
        actions = [a for a in menu.actions() if '循环内容' in a.text()]
        assert len(actions) == 1 and actions[0].text() == expected
        actions[0].trigger()
    with patch('anclicker.ui.instruction_table.exec_two_column_menu', execute):
        table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, point, table.viewport().mapToGlobal(point)))
    if expected.startswith('折叠'):
        assert not table._expanded_border_rects()
    else:
        assert len(table._expanded_border_rects()) == 2
# A disjoint range must leave unrelated visible rows outside the border.
table.loop_ranges = {}
table.step_groups = {1: dict(number=1,members={2,3,5},collapsed=False,locked=False)}
table.apply_comment_folds()
assert table._expanded_border_runs == [(0,1,2),(0,4,4)]
table.setColumnHidden(2, True)
assert table._expanded_border_rects() == []
table.close()
print('PASS: one-row loop menu, nested/disjoint borders, light/dark pixels, collapse, column resize and hide')
