"""Consistent compact icon buttons for the run-log header."""
from anclicker.platform.qt_compat.QtCore import QSize,Qt
from anclicker.ui.file_menu_icons import file_menu_icon


def configure_log_actions(window):
    for button,kind,label in ((window.toolButton_8,'export','导出运行日志'),
                              (window.toolButton_7,'clear','清空运行日志')):
        button.setIcon(file_menu_icon(kind,2.0))
        button.setIconSize(QSize(16,16))
        button.setFixedSize(24,24)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        button.setAutoRaise(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.setStyleSheet('''
            QToolButton { padding: 2px; margin: 0; border: 1px solid transparent;
                border-radius: 5px; background: transparent; }
            QToolButton:hover { background: rgba(239,68,68,24); border-color: rgba(239,68,68,65); }
            QToolButton:pressed { background: rgba(239,68,68,42); }
            QToolButton:focus { border-color: #ef4444; }
        ''')
