import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPoint, Qt, QCoreApplication, QEvent
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow
from window_chrome import install_title_bar
from view_workspace import ViewWorkspace


@pytest.fixture
def chrome():
    app = QApplication.instance() or QApplication([])
    class Window(QMainWindow):
        close_count = 0
        def closeEvent(self, event):
            self.close_count += 1
            event.ignore()  # Preserve the normal application veto/save path.
    window = Window()
    window.setWindowTitle('An Clicker test')
    window.setMinimumSize(400, 260)
    window.resize(800, 500)
    menu = window.menuBar()
    menu.addMenu('文件')
    action = QAction('切换主题', window)
    callback = Mock()
    action.triggered.connect(callback)
    bar = install_title_bar(window, action)
    bar.apply_theme('dark', ViewWorkspace.THEMES['dark'])
    window.show()
    app.processEvents()
    yield app, window, bar, action, callback, menu
    window.hide()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_theme_icon_is_immediately_left_of_minimize(chrome):
    app, window, bar, action, callback, menu = chrome
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert bar.layout().indexOf(bar.theme_button) + 1 == bar.layout().indexOf(bar.minimize_button)
    assert bar.theme_button.x() < bar.minimize_button.x() < bar.maximize_button.x() < bar.close_button.x()
    assert not action.icon().isNull()
    assert bar.theme_button.accessibleName() == '切换浅色主题'
    bar.theme_button.click()
    callback.assert_called_once()
    bar.apply_theme('light', ViewWorkspace.THEMES['light'])
    assert bar.theme_button.accessibleName() == '切换深色主题'
    assert menu.actions()[0].text() == '文件'
    assert menu.isVisible()
    window.setWindowTitle('Updated title')
    assert bar.title.text() == 'Updated title'


def test_window_buttons_preserve_maximize_minimize_and_close_veto(chrome):
    app, window, bar, *_ = chrome
    bar.maximize_button.click()
    app.processEvents()
    assert window.isMaximized()
    assert bar.maximize_button.accessibleName() == '还原窗口'
    assert not bar.edges_at(QPoint(1, 1))
    bar.maximize_button.click()
    app.processEvents()
    assert not window.isMaximized()
    bar.minimize_button.click()
    assert window.isMinimized()
    window.showNormal()
    bar.close_button.click()
    assert window.close_count == 1
    assert window.isVisible()


def test_eight_resize_regions_leave_controls_alone(chrome):
    app, window, bar, *_ = chrome
    assert bar.edges_at(QPoint(1, 1)) == Qt.Edge.LeftEdge | Qt.Edge.TopEdge
    assert bar.edges_at(QPoint(window.width()-1, window.height()-1)) == Qt.Edge.RightEdge | Qt.Edge.BottomEdge
    assert not bar.edges_at(QPoint(100, 20))


def test_dark_palette_matches_neutral_reference():
    colors = ViewWorkspace.THEMES['dark']
    assert colors['bg'] == '#09090b'
    assert colors['surface'] == '#18181b'
    assert colors['accent'] == '#0088ff'
