"""Shared, wrapping control groups for desktop and browser recording."""
from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy
from responsive_layout import FlowLayout


def panel(parent, title):
    group = QFrame(parent)
    group.setObjectName("recordingControls")
    group.setAccessibleName(title)
    group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    layout = QVBoxLayout(group)
    layout.setContentsMargins(6, 5, 6, 5)
    layout.setSpacing(4)
    return group, layout


def control_row():
    row = FlowLayout(center_rows=True)
    row.setSpacing(6)
    return row


def inline_group(*widgets):
    group = QWidget()
    group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    row = QHBoxLayout(group)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(5)
    for widget in widgets:
        row.addWidget(widget, 0, Qt.AlignVCenter)
    return group


def setup_page(layout):
    layout.parentWidget().setProperty("compactRecording", True)
    layout.setContentsMargins(6, 4, 6, 6)
    layout.setSpacing(10)
