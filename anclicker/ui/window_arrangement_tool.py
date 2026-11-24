"""Settings-menu entry points for the window arrangement tool."""
import json
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.qt_compat.QtGui import QAction
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialogButtonBox,QMessageBox
from anclicker.platform.window_arrangement import stop_auto_fill
from anclicker._imports import DeferredImports

_imports=DeferredImports(globals(),{'Editor':('from','anclicker.ui.instruction_editors.其他.窗口排布',('InstructionEditor',),0)})


def open_window_arrangement(window):
    saved=window.db.get_setting_value('窗口排布设置')
    try:draft=json.loads(saved) if saved else None
    except (ValueError,TypeError):draft=None
    editor=_imports.load('Editor')(parent=window,draft=draft,context=ExecutionContext(metadata={'database':window.db}))
    editor.setWindowTitle('窗口排布')
    editor.ui.commonGroupBox.hide();editor.ui.testButton.hide();editor.runtime_advanced_button.hide()
    editor.ui.buttonBox.button(QDialogButtonBox.Ok).hide()
    editor.ui.buttonBox.button(QDialogButtonBox.Cancel).setText('关闭')
    try:editor.exec()
    finally:
        window.db.set_setting_value('窗口排布设置',json.dumps({'type_id':'窗口排布','parameters':editor._raw_parameters()},ensure_ascii=False))
        editor.deleteLater()


def install_window_arrangement_tool(window):
    window.menu_4.addSeparator()
    window.action_window_arrangement=QAction('窗口排布',window)
    window.action_window_arrangement.triggered.connect(lambda:open_window_arrangement(window))
    window.menu_4.addAction(window.action_window_arrangement)
    window.action_stop_arrangement=QAction('停止窗口自动补位',window)
    def stop():
        try:stop_auto_fill();window.statusBar.showMessage('窗口自动补位已停止。',4000)
        except Exception as error:QMessageBox.warning(window,'停止自动补位',str(error))
    window.action_stop_arrangement.triggered.connect(stop);window.menu_4.addAction(window.action_stop_arrangement)
    QApplication.instance().aboutToQuit.connect(stop_auto_fill)
