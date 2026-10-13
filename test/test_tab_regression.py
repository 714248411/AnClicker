from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import QApplication, QLineEdit
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host

def test_parameter_tab(host):
    host.workspace.add_command('时间等待')
    d=host.view_workspace.docking
    editor=list(d.parameters.values())[-1]
    QTest.qWait(100)
    fields=editor.findChildren(QLineEdit)
    assert fields
    fields[0].setFocus()
    for i in range(30):
        target=QApplication.focusWidget() or fields[0]
        QTest.keyClick(target, Qt.Key_Tab)
        QApplication.processEvents()
    assert editor.isVisible()

def test_capture_tab(host):
    from instructions.common.input_controls import KeyCaptureDialog
    dialog=KeyCaptureDialog(host)
    dialog.show()
    QTest.qWait(50)
    QTest.keyClick(dialog, Qt.Key_Tab)
    assert dialog.value == 'tab'
    dialog.reject()
    # Open another editor after capture: global filters must not touch new widgets.
    host.workspace.add_command('按下键盘')
    QTest.qWait(50)
    editor=list(host.view_workspace.docking.parameters.values())[-1]
    for field in editor.findChildren(QLineEdit):
        QTest.keyClick(field, Qt.Key_Tab)
    dialog.deleteLater()

def test_table_tab(host):
    host.view_workspace.show_table()
    table=host.view_workspace.command_table
    table.setFocus()
    table.setCurrentCell(0,0)
    for i in range(50):
        QTest.keyClick(table, Qt.Key_Tab)
        QApplication.processEvents()
    assert table.rowCount() > 0

def test_custom_tab_guidance(host):
    from qt_compat.QtGui import QKeySequence
    action=next(a for a in host.menu_4.actions() if a.text() == '中文编程提示')
    action.setShortcut(QKeySequence('Tab'))
    host.view_workspace.interface_scale.change(-2)
    host.view_workspace.show_table()
    table=host.view_workspace.command_table
    host.show();host.activateWindow();QApplication.setActiveWindow(host);table.setFocus()
    QTest.qWait(100)
    palette=host.workspace.palette
    palette.command_added('打开网页')
    for i in range(10):
        before=palette.guidance_enabled
        QTest.keyClick(table, Qt.Key_Tab)
        QTest.qWait(20)
        assert palette.guidance_enabled != before
