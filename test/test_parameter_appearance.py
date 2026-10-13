import pytest
from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import QScrollArea, QLabel
from qt_compat.QtTest import QTest
from instructions.models import InstructionDraft
from test.test_hidden_stop import host


@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_parameter_background_and_smaller_font(host, theme):
    v = host.view_workspace
    host.resize(1200, 850)
    v.theme_mode = theme
    v._apply_theme()
    v.show_table()
    command = host.workspace.repository.add_command(InstructionDraft('时间等待', {}), unconnected=True)
    v.refresh_table()
    row = next(r for r in range(v.command_table.rowCount()) if v.command_table.item(r, 0).data(Qt.UserRole) == command.id)
    v.command_table.cellDoubleClicked.emit(row, 2)
    QTest.qWait(120)
    key = 'parameters_' + str(command.id)
    dock = v.docking.docks[key]
    editor = v.docking.parameters[key]
    dock.resize(800, 650)
    QTest.qWait(100)
    assert editor._panel_scaler.last_size == 13
    labels = [label for label in editor.findChildren(QLabel) if label.text() and not label.styleSheet()]
    assert labels and all(label.font().pixelSize() == 13 for label in labels)
    for floating in (True, False):
        if not floating:
            v.docking.move_panel(key, 'right')
            QTest.qWait(100)
        expected = v.THEMES[theme]['bg'].lower()
        for area in dock.findChildren(QScrollArea):
            viewport = area.viewport()
            assert viewport.palette().color(viewport.backgroundRole()).name() == expected
        picture = dock.grab().toImage()
        if floating:
            assert picture.pixelColor(0, 0).alpha() == 0
            assert picture.pixelColor(1, picture.height()-2).alpha() == 0
            assert dock._embedded_title.indent() >= 8
        else:
            assert picture.pixelColor(1, picture.height()-2).name() == expected
        dock.grab().save('validation/parameters-' + theme + ('-floating' if floating else '-embedded') + '.png')
    editor.reject()
    QTest.qWait(30)
