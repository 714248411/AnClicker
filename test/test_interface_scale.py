from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
from qt_compat.QtCore import QSize
from test.test_hidden_stop import host


def test_menu_and_existing_new_dialogs_restore(host):
    v = host.view_workspace
    texts = [a.text() for a in host.menubar.actions()]
    assert texts.index('界面字号') == texts.index('视图') + 1
    actions = v.font_size_menu.actions()
    assert [a.text() for a in actions] == ['字号+', '字号-', '字号恢复默认']
    QTest.qWait(80)
    base = host.styleSheet()
    icon = host.toolBar.iconSize()
    actions[0].trigger(); QTest.qWait(80)
    assert 'font-size: 14px' in host.styleSheet()
    assert host.toolBar.iconSize().width() > icon.width()
    dialog = QDialog(host)
    layout = QVBoxLayout(dialog)
    label = QLabel('设置文字', dialog)
    label.setStyleSheet('font-size: 11px;')
    button = QPushButton('设置图标', dialog)
    button.setIconSize(QSize(20, 20))
    layout.addWidget(label); layout.addWidget(button)
    dialog.show(); QTest.qWait(80)
    assert label.font().pixelSize() == 12
    assert button.iconSize().width() > 20
    v._apply_theme(); QTest.qWait(80)
    assert 'font-size: 14px' in host.styleSheet()
    actions[1].trigger(); QTest.qWait(80)
    assert label.font().pixelSize() == 11
    assert button.iconSize() == QSize(20, 20)
    actions[0].trigger(); actions[0].trigger(); QTest.qWait(80)
    assert label.font().pixelSize() == 13
    actions[2].trigger(); QTest.qWait(80)
    assert label.font().pixelSize() == 11
    assert host.styleSheet() == base
    assert host.toolBar.iconSize() == icon
    assert host.db.get_setting_value('界面字号偏移') == '0'
    dialog.close()


def test_parameter_scaling_survives_resize(host):
    from instructions.models import InstructionDraft
    v = host.view_workspace
    v.interface_scale.change(1)
    command = host.workspace.repository.add_command(InstructionDraft('时间等待', {}), unconnected=True)
    host.workspace.edit_command(command.id)
    key = 'parameters_' + str(command.id)
    dock = v.docking.docks[key]
    editor = v.docking.parameters[key]
    dock.resize(800, 700); QTest.qWait(100)
    labels = [w for w in editor.findChildren(QLabel) if w.text() and not w.styleSheet()]
    assert labels and all(w.font().pixelSize() == 13 for w in labels), ([(w.objectName(), w.font().pixelSize()) for w in labels], editor.styleSheet(), editor._panel_scaler.base_style)
    dock.resize(350, 300); QTest.qWait(100)
    dock.resize(800, 700); QTest.qWait(100)
    assert all(w.font().pixelSize() == 13 for w in labels)
    v.interface_scale.change(); QTest.qWait(100)
    assert all(w.font().pixelSize() == 12 for w in labels)
    editor.reject()
