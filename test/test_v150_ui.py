"""Real Qt layout, settings and help regressions for 1.5.0."""
from pathlib import Path
import pytest
from qt_compat.QtCore import Qt, QTimer
from qt_compat.QtWidgets import QApplication, QDialog, QLabel, QCheckBox, QWidget, QToolButton, QTextBrowser
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host

@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_all_pages_resize_and_restore(host, theme):
    view = host.view_workspace
    view.theme_mode = theme
    view._apply_theme()
    for index in range(host.tabWidget.count()):
        host.tabWidget.setCurrentIndex(index)
        for width, height in ((1000,700),(1500,900),(1180,720)):
            host.resize(width,height)
            QApplication.processEvents()
            bar=view.title_bar
            assert bar.width()==host.width()
            for button in (bar.minBtn,bar.maxBtn,bar.closeBtn):
                assert bar.rect().contains(button.geometry())
            assert host.pushButton_5.isVisible()
            assert view.controls_scroll.viewport().width()>0
    original=host.size()
    for _ in range(3):
        host.showMaximized(); QApplication.processEvents()
        view.compact.set_active(True); QApplication.processEvents()
        view.compact.set_active(False); QApplication.processEvents()
        assert host.isMaximized()
        host.showNormal(); QApplication.processEvents()
        assert host.size()==original

@pytest.mark.parametrize('theme', ['light','dark'])
def test_shortcut_settings_labels_and_theme(host,theme):
    host.view_workspace.theme_mode=theme
    host.view_workspace._apply_theme()
    observations=[]
    def inspect():
        dialog=QApplication.activeModalWidget()
        try:
            body=dialog.findChild(QWidget,'settingsBody')
            observations.append((body.palette().window().color().name(),
                [x.text() for x in body.findChildren(QLabel)],
                [x.text() for x in body.findChildren(QCheckBox)]))
            output=Path(__file__).resolve().parents[1]/'validation'/('v150-shortcuts-'+theme+'.png')
            dialog.grab().save(str(output))
        finally: dialog.reject()
    QTimer.singleShot(100,inspect)
    host.open_view_shortcut_settings()
    background,labels,checks=observations[0]
    assert background==host.view_workspace.THEMES[theme]['surface']
    assert '主界面' in labels
    assert checks and all(x=='启用' for x in checks)

@pytest.mark.parametrize('page_name',['recording_page','web_recording_page'])
def test_book_opens_complete_help(host,page_name):
    page=getattr(host.view_workspace,page_name)
    book=page.findChild(QToolButton,'recordingHelpBook')
    seen=[]
    def inspect():
        dialog=QApplication.activeModalWidget()
        try: seen.append(dialog.findChild(QTextBrowser).toPlainText())
        finally: dialog.reject()
    QTimer.singleShot(100,inspect)
    book.click()
    assert '接续录制' in seen[0] and '写入' in seen[0] and '停止' in seen[0]
