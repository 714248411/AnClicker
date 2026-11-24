from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QToolButton
from anclicker.ui.file_menu_icons import file_menu_icon

"""Background-only toolbar tint; geometry and button states stay in theme.py."""
def toolbar_stylesheet(mode):
    background = '#111215' if mode == 'dark' else '#f0f1f4'
    return f'QMenuBar, QToolBar {{ background: {background}; }}'


def configure_toolbar_icons(toolbar):
    """Align toolbar content without changing shared menu actions or geometry."""
    kinds={'actionx':'save','actionImportProjectFolder':'folder',
           'actions_2':'settings','actionhelp':'guide','actionabout':'about'}
    for action in toolbar.actions():
        kind=kinds.get(action.objectName())
        button=toolbar.widgetForAction(action)
        if not isinstance(button,QToolButton):continue
        if kind:
            button.setIcon(file_menu_icon(kind,2.0))
        text_only=button.icon().isNull() or button.toolButtonStyle()==Qt.ToolButtonStyle.ToolButtonTextOnly
        if button.property('toolbarTextOnly')!=text_only:
            button.setProperty('toolbarTextOnly',text_only)
            button.style().unpolish(button)
            button.style().polish(button)
            button.updateGeometry()
