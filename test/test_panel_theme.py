import pytest
from qt_compat.QtWidgets import QApplication
from test.test_hidden_stop import host

@pytest.mark.parametrize('mode',['light','dark'])
def test_panel_themes_views_and_compact_controls(host,mode):
    view=host.view_workspace
    view.theme_mode=mode
    view._apply_theme()
    stylesheet=host.styleSheet()
    for selector in ('QTabWidget::pane','QFrame#workspacePanel','QTableWidget#commandTable','QTextEdit#textEdit','QTreeWidget#instructionTree'):
        rule=stylesheet.split(selector+' {',1)[1].split('}',1)[0]
        assert 'border: none' in rule
    for index in range(host.tabWidget.count()):
        host.tabWidget.setCurrentIndex(index)
        QApplication.processEvents()
        assert host.tabWidget.currentWidget().isVisible()
        assert host.run_unconnected_checkbox.isVisible()
    view.compact.set_active(True)
    QApplication.processEvents()
    assert host.run_unconnected_checkbox.isVisible()
    assert host.pushButton_5.isVisible()
    view.compact.set_active(False)
