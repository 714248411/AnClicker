"""Release-only checks of actual loaded instruction dialogs, without input replay."""
from PySide6.QtWidgets import QApplication, QAbstractSpinBox, QLineEdit
from instructions.registry import INSTRUCTION_SPECS
from instructions.models import ExecutionContext


def validate_instruction_editors(window):
    app = QApplication.instance()
    view = window.view_workspace
    original_theme = view.theme_mode
    checked = 0
    image_layout = False
    try:
        for theme in ('light', 'dark'):
            view.theme_mode = theme
            view._apply_theme()
            for spec in INSTRUCTION_SPECS:
                editor = spec.create_editor(window, context=ExecutionContext(metadata={'database': window.db}))
                try:
                    editor.show()
                    app.processEvents()
                    if spec.type_id == '图像点击':
                        image_layout = (hasattr(editor, 'folder_combo')
                                        and editor.ui.auxiliary_6.text() == '调整点击位置'
                                        and editor.capture_button.isVisible())
                        if not image_layout:
                            raise RuntimeError('Packaged image-click editor has obsolete layout')
                    for spin in editor.findChildren(QAbstractSpinBox):
                        if spin.isHidden():
                            continue
                        line = spin.findChild(QLineEdit)
                        if line is not None and line.height() < line.fontMetrics().height():
                            raise RuntimeError(f'{theme}/{spec.type_id}/{spin.objectName()}: '
                                               f'clipped digits: {line.height()} < {line.fontMetrics().height()}')
                        checked += 1
                finally:
                    editor.hide()
                    editor.deleteLater()
            app.processEvents()
    finally:
        view.theme_mode = original_theme
        view._apply_theme()
    return {'spinboxes_checked': checked, 'image_click_layout': image_layout}
