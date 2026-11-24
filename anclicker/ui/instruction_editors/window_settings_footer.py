"""Shared bottom actions for window keyboard/mouse editors."""
from anclicker.platform.qt_compat.QtWidgets import QHBoxLayout, QPushButton, QMessageBox


def add_window_footer(editor, layout, buttons):
    editor.button_box = buttons
    editor.test_button = QPushButton('测试指令', editor)
    editor.test_button.setAutoDefault(False)
    editor.test_button.setToolTip('使用当前设置执行一次；等待过程中可取消测试')

    def test_current():
        try:
            draft = editor.get_draft()
            if hasattr(editor, 'target') and not editor.target:
                raise ValueError('请先选择目标窗口')
            if draft.type_id == '窗口位置与大小' and draft.parameters.get('操作') in ('记录位置和大小', '恢复位置和大小') and not draft.parameters.get('记录名称'):
                raise ValueError('请填写记录变量名称')
        except (TypeError, ValueError) as error:
            QMessageBox.warning(editor, '参数不完整', str(error))
            return
        editor.test_requested.emit(draft)

    editor.test_button.clicked.connect(test_current)
    footer = QHBoxLayout()
    footer.addWidget(editor.test_button)
    footer.addStretch(1)
    buttons.setCenterButtons(False)
    footer.addWidget(buttons)
    layout.addStretch(1)
    layout.addLayout(footer)
