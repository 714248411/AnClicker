import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from unittest.mock import Mock, patch

import pytest
from qt_compat.QtCore import QPoint, Qt, QCoreApplication, QEvent
from qt_compat.QtGui import QAction
from qt_compat.QtWidgets import QApplication, QMainWindow
from window_chrome import install_title_bar, FramelessMainWindow as QMainWindow
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
    assert bar.layout().indexOf(bar.theme_button) + 1 == bar.layout().indexOf(bar.minBtn)
    assert bar.theme_button.x() < bar.minBtn.x() < bar.maxBtn.x() < bar.closeBtn.x()
    assert not action.icon().isNull()
    assert bar.theme_button.toolTip() == '切换浅色主题'
    bar.theme_button.click()
    callback.assert_called_once()
    bar.apply_theme('light', ViewWorkspace.THEMES['light'])
    assert bar.theme_button.toolTip() == '切换深色主题'
    assert menu.actions()[0].text() == '文件'
    assert menu.isVisible()
    window.setWindowTitle('Updated title')
    from info import APP_NAME, CURRENT_VERSION
    assert bar.titleLabel.text() == APP_NAME
    assert bar.versionLabel.text() == CURRENT_VERSION


@patch('window_chrome.toggleMaxState', side_effect=lambda window: window.showNormal() if window.isMaximized() else window.showMaximized())
def test_window_buttons_preserve_maximize_minimize_and_close_veto(toggle, chrome):
    app, window, bar, *_ = chrome
    bar.maxBtn.click()
    app.processEvents()
    assert window.isMaximized()
    assert bar.maxBtn.kind == 'restore'
    bar.maxBtn.click()
    app.processEvents()
    assert not window.isMaximized()
    bar.minBtn.click()
    assert window.isMinimized()
    window.showNormal()
    bar.closeBtn.click()
    assert window.close_count == 1
    assert window.isVisible()


def test_title_drag_leaves_controls_alone(chrome):
    app, window, bar, *_ = chrome
    assert not bar.canDrag(bar.minBtn.geometry().center())
    assert not bar.canDrag(bar.closeBtn.geometry().center())


def test_dark_palette_matches_neutral_reference():
    colors = ViewWorkspace.THEMES['dark']
    assert colors['bg'] == '#09090b'
    assert colors['surface'] == '#18181b'
    assert colors['accent'] == '#0088ff'
