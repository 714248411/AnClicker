import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
import pytest
from qt_compat.QtGui import QAction
from qt_compat.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QSplitter, QStatusBar
from Window.mainwindow_ui import Ui_MainWindow
from window_chrome import install_title_bar, FramelessMainWindow as QMainWindow
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
    from view_workspace import ViewWorkspace
    view = SimpleNamespace(window=window, title_bar=bar, tabs=window.tabWidget,
                           table_splitter=splitter, theme_mode='light', THEMES=ViewWorkspace.THEMES)
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
        assert w.checkBox_2.isChecked()
        assert w.checkBox_2.isEnabled()
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


def test_compact_retains_edited_hide_preference(compact):
    _, window, _, controller = compact
    window.checkBox_2.setChecked(False)
    controller.set_active(True)
    window.checkBox_2.setChecked(True)
    controller.set_active(False)
    assert window.checkBox_2.isChecked() and window.checkBox_2.isEnabled()
