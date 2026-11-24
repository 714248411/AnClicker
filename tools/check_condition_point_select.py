"""Exercise type-specific widgets, dialogs, lossless reload and category switches."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import QDateTime
from anclicker.ui.flow_condition_editor import ConditionPanel
from anclicker.ui.condition_value_editor import ListValueDialog

app = QApplication.instance() or QApplication([])
panel = ConditionPanel()
panel.kind.setCurrentText('数字')
left = panel.value_editors['判断值']
right = panel.value_editors['比较值']
assert not left.number.isHidden() and left.combo.isHidden()
left.number.setValue(12.5)
right.number.setValue(10)
assert panel.parameters()['判断值'] == '12.5'
panel.controls['判断值'].setCurrentText('{{金额}}')
assert left.number.isHidden() and not left.combo.isHidden()
panel.controls['判断值'].setCurrentText('12345678901234567890.123456789')
assert not left.combo.isHidden()
assert panel.parameters()['判断值'] == '12345678901234567890.123456789'
panel.kind.setCurrentText('日期')
assert not left.date.isHidden() and left.number.isHidden()
left.date.setDateTime(QDateTime.fromString('2026-10-26 12:34:56', 'yyyy-MM-dd HH:mm:ss'))
assert panel.parameters()['判断值'] == '2026-10-26 12:34:56'
panel.kind.setCurrentText('数字')
assert panel.parameters()['判断值'] == '12345678901234567890.123456789'
panel.kind.setCurrentText('日期')
assert panel.parameters()['判断值'] == '2026-10-26 12:34:56'
panel.kind.setCurrentText('文件目录')
assert not left.buttons['file'].isHidden() and not left.buttons['folder'].isHidden()
assert panel.rows['比较值'].isHidden()
with patch('anclicker.ui.condition_value_editor.QFileDialog.getOpenFileName', return_value=('C:/test.txt', '')):
    left.buttons['file'].click()
assert panel.parameters()['判断值'] == 'C:/test.txt'
panel.controls['比较方式'].setCurrentText('是目录')
assert left.buttons['file'].isHidden() and not left.buttons['folder'].isHidden()
with patch('anclicker.ui.condition_value_editor.QFileDialog.getExistingDirectory', return_value='C:/folder'):
    left.buttons['folder'].click()
assert panel.parameters()['判断值'] == 'C:/folder'
panel.kind.setCurrentText('窗口存在')
assert not left.buttons['windows'].isHidden()
with patch('anclicker.ui.condition_value_editor.window_titles', return_value=['测试窗口']), patch(
        'anclicker.platform.qt_compat.QtWidgets.QInputDialog.getItem', return_value=('测试窗口', True)):
    left.buttons['windows'].click()
assert panel.parameters()['判断值'] == '测试窗口'
panel.kind.setCurrentText('列表')
assert not left.buttons['list'].isHidden()
dialog = ListValueDialog('[]')
dialog.add_item('甲')
dialog.add_item(3)
assert dialog.value() == '["甲", 3]'
dialog.table.selectRow(0)
dialog.remove_items()
assert dialog.value() == '[3]'
panel.controls['判断值'].setCurrentText(dialog.value())
panel.controls['比较方式'].setCurrentText('长度等于')
assert not right.number.isHidden() and right.number.decimals() == 0
right.number.setValue(1)
assert panel.parameters()['比较值'] == '1'
panel.controls['比较方式'].setCurrentText('为空')
assert panel.rows['比较值'].isHidden()
panel.kind.setCurrentText('文本')
assert not left.combo.isHidden() and left.date.isHidden() and left.number.isHidden()
panel.controls['判断值'].setCurrentText('  测试  ')
assert panel.parameters()['判断值'] == '  测试  '
panel.kind.setCurrentText('日期')
panel.resize(500, panel.sizeHint().height())
panel.show()
app.processEvents()
output = Path(__file__).resolve().parents[1] / 'artifacts' / 'condition-date-preview.png'
panel.grab().save(str(output))
dialog.close()
panel.close()
print('PASS: type-specific controls, numeric precision preservation, date selection, file/folder/window pickers, list builder, unary fields and switch restoration')
