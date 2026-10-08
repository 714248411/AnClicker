"""Exercise actual mouse events, not the palette's private signal helper."""
import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from node_editor.palette import InstructionPalette
from test.test_hidden_stop import host


@pytest.fixture
def palette():
    app = QApplication.instance() or QApplication([])
    widget = InstructionPalette({"wait": {"title": "Wait", "category": "Timing"}})
    widget.resize(300, 300)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def leaf_position(palette):
    tree = palette.tree
    return tree.visualItemRect(tree.topLevelItem(0).child(0)).center()


@pytest.mark.parametrize("first_click", [False, True])
def test_double_click_activates_once(palette, first_click):
    activated = []
    palette.instructionActivated.connect(activated.append)
    pos = leaf_position(palette)
    if first_click:
        QTest.mouseClick(palette.tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QTest.mouseDClick(palette.tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QTest.mouseRelease(palette.tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QApplication.processEvents()
    assert activated == ["wait"]


def test_small_mouse_movement_obeys_system_drag_threshold(palette):
    pos = leaf_position(palette)
    previous = QApplication.startDragDistance()
    QApplication.setStartDragDistance(24)
    try:
        QTest.mousePress(palette.tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        moved = pos + QPoint(9, 0)
        event = QMouseEvent(QEvent.Type.MouseMove, QPointF(moved),
                            QPointF(palette.tree.viewport().mapToGlobal(moved)),
                            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
                            Qt.KeyboardModifier.NoModifier)
        with patch("node_editor.palette.QDrag") as drag:
            QApplication.sendEvent(palette.tree.viewport(), event)
            assert not drag.called
    finally:
        QTest.mouseRelease(palette.tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        QApplication.setStartDragDistance(previous)


def test_category_and_right_double_click_do_not_add_commands(palette):
    activated = []
    palette.instructionActivated.connect(activated.append)
    tree = palette.tree
    QTest.mouseDClick(tree.viewport(), Qt.MouseButton.RightButton,
                     pos=leaf_position(palette))
    category = tree.topLevelItem(0)
    pos = tree.visualItemRect(category).center()
    QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QTest.mouseDClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    QApplication.processEvents()
    assert not category.isExpanded()
    assert activated == []


def test_native_drag_keeps_instruction_mime_and_copy_action(palette):
    from node_editor.palette import INSTRUCTION_MIME_TYPE

    tree = palette.tree
    tree.setCurrentItem(tree.topLevelItem(0).child(0))
    with patch("node_editor.palette.QDrag") as drag:
        tree.startDrag(Qt.DropAction.CopyAction)
        mime = drag.return_value.setMimeData.call_args.args[0]
        assert bytes(mime.data(INSTRUCTION_MIME_TYPE)) == b"wait"
        drag.return_value.exec.assert_called_once_with(Qt.DropAction.CopyAction)
    tree.setCurrentItem(tree.topLevelItem(0))
    with patch("node_editor.palette.QDrag") as drag:
        tree.startDrag(Qt.DropAction.CopyAction)
        assert not drag.called


@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.parametrize("view_index", [1, 2])
def test_double_click_editor_save_updates_table_and_graph(host, accept, view_index):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QDialogButtonBox

    host.workspace.repository.clear()
    host.workspace.reload_graph()
    host.view_workspace.refresh_all()
    host.tabWidget.setCurrentIndex(view_index)
    palette = host.workspace.palette
    palette.search_edit.setText("时间等待")
    QApplication.processEvents()
    tree = palette.tree
    item = next(tree.topLevelItem(i).child(j)
                for i in range(tree.topLevelItemCount())
                for j in range(tree.topLevelItem(i).childCount())
                if tree.topLevelItem(i).child(j).text(0) == "时间等待")
    tree.scrollToItem(item)
    pos = tree.visualItemRect(item).center()
    opened = []

    def finish_editor():
        dialog = QApplication.activeModalWidget()
        if dialog is None:
            return
        opened.append(dialog.windowTitle())
        if hasattr(dialog, "button_box"):
            role = (QDialogButtonBox.StandardButton.Ok if accept
                    else QDialogButtonBox.StandardButton.Cancel)
            QTest.mouseClick(dialog.button_box.button(role), Qt.MouseButton.LeftButton)
        else:
            dialog.reject()

    timer = QTimer()
    timer.timeout.connect(finish_editor)
    timer.start(20)
    try:
        QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        QTest.mouseDClick(tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        QTest.mouseRelease(tree.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        QApplication.processEvents()
    finally:
        timer.stop()
    assert opened == ["时间等待"]
    commands = host.workspace.repository.list_commands()
    assert len(commands) == int(accept)
    assert host.view_workspace.command_table.rowCount() == int(accept)
    assert len(host.workspace.repository.snapshot().nodes) == 2 + int(accept)
    if accept:
        assert host.view_workspace.command_table.item(0, 1).text() == f"#{commands[0].id}"
