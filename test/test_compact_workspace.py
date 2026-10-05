import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QSplitter, QStatusBar
from Window.mainwindow_ui import Ui_MainWindow
from window_chrome import install_title_bar
from compact_workspace import CompactWorkspace


@pytest.fixture
def compact():
    app = QApplication.instance() or QApplication([])
    class Window(QMainWindow, Ui_MainWindow):
        pass
    window = Window()
    window.setupUi(window)
    window.statusBar = QStatusBar(window)
    window.setStatusBar(window.statusBar)
    panel = QFrame(); layout = QVBoxLayout(panel); layout.addWidget(window.textEdit)
    splitter = QSplitter(); splitter.addWidget(QFrame()); splitter.addWidget(panel)
    bar = install_title_bar(window, QAction('主题', window))
    view = SimpleNamespace(window=window, title_bar=bar, tabs=window.tabWidget, table_splitter=splitter)
    controller = CompactWorkspace(view)
    window.show(); app.processEvents()
    yield app, window, view, controller
    controller.set_active(False)
    window.hide(); window.deleteLater(); splitter.deleteLater(); app.processEvents()


def test_compact_button_before_theme(compact):
    _, _, view, _ = compact
    bar = view.title_bar
    assert bar.layout().indexOf(bar.compact_button)+1 == bar.layout().indexOf(bar.theme_button)


def test_compact_keeps_same_controls_log_and_restores(compact):
    app, w, view, controller = compact
    original = w.size()
    w.checkBox_2.setChecked(True)
    w.textEdit.append('运行 25 次')
    for _ in range(3):
        controller.set_active(True); app.processEvents()
        assert view.tabs.isHidden()
        assert w.textEdit.isVisible()
        assert not w.checkBox_2.isChecked()
        assert not w.checkBox_2.isEnabled()
        assert w.pushButton_5.isVisible()
        w.resize(280, 350); app.processEvents()
        assert w.width() == 280
        assert w.pushButton_5.height() >= 14
        controller.set_active(False); app.processEvents()
        assert w.size() == original
        assert w.checkBox_2.isChecked()
        assert view.table_splitter.count() == 2
        assert w.textEdit.toPlainText() == '运行 25 次'


def test_compact_font_scales_and_live_log_is_preserved(compact):
    app, w, _, controller = compact
    controller.set_active(True)
    w.resize(280, 350); app.processEvents()
    small = w.groupBox_3.styleSheet()
    w.textEdit.append('仍然运行')
    w.resize(440, 600); app.processEvents()
    assert w.groupBox_3.styleSheet() != small
    assert '仍然运行' in w.textEdit.toPlainText()
