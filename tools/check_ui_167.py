"""Regression coverage for 1.6.7 chrome, compact placement and responsive actions."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys,tempfile
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import QPoint
from anclicker.platform.qt_compat.QtGui import QPixmap
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QLabel,QPushButton,QMenu
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.theme import THEMES
from anclicker.ui.agent_view import AgentView
from anclicker.ui.local_model_dialog import LocalModelDialog
from anclicker.ui.dialogs.设置窗口 import Setting
from anclicker.ui.information_dialogs import DonationDialog
from anclicker.ui.compact_position import POSITION_SETTING,LAST_POSITION_SETTING,place_compact_window,save_compact_position
from anclicker.execution.execution_timing import AdvancedTimingDialog
from anclicker.ui.context_menu_style import style_context_menu

class Host(QWidget):
    def unregister_global_shortcut_keys(self):pass
    def register_global_shortcut_keys(self):pass
    def open_view_shortcut_settings(self,*args):pass
class Library:
    def list(self):return [{'active':True,'file':'test-v5.gguf','bytes':350000000}]
    def active(self):return 'test-v5.gguf'


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        host=Host();host.db=DatabaseOperation(str(Path(folder)/'test.db'))
        with patch.object(AgentView,'_activate_local_model',lambda self:None),patch.object(AgentView,'refresh_resources',lambda self:None):
            view=AgentView(host);view.setParent(None);view.show()
            for mode in ('light','dark'):
                host.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode=mode)
                view.apply_theme(mode);view.badge.setText('GPU · RAM 581 MB')
                for width,height in ((1000,720),(680,520),(420,400),(340,300),(1000,720)):
                    view.setFixedSize(width,height);app.processEvents();app.processEvents()
                    expected=11 if width==340 else 12 if width==420 else 13
                    assert view.new_button.font().pixelSize()==view.badge.font().pixelSize()==expected
                    assert abs(view.action_bar.mapTo(view,view.action_bar.rect().topRight()).x()-(view.width()-15))<=2
                    for index,b in enumerate(view.header_buttons):
                        assert b.width()>=b.fontMetrics().horizontalAdvance(b.text())+8
                        assert view.rect().contains(b.mapTo(view,b.rect().bottomRight()))
                        for other in view.header_buttons[index+1:]:assert not b.geometry().intersects(other.geometry())
                view.session.drafts=[];view.render_drafts();app.processEvents()
                settings=Setting(host);settings.show();app.processEvents()
                assert [settings.tabWidget.tabText(i) for i in range(settings.tabWidget.count())]==['小窗口设置','快捷键','OCR接口设置','更改快捷键','其他设置']
                settings.keySequenceEdit.setKeySequence('F8');settings.restore_shortcuts_button.click()
                assert settings.keySequenceEdit.keySequence().toString()=='F10'
                assert settings.compact_position.count()==5
                assert THEMES[mode]['text'] in settings.titleBar.titleLabel.styleSheet();settings.close()
                dialog=LocalModelDialog(view,Library());dialog.show();app.processEvents()
                assert THEMES[mode]['text'] in dialog.titleBar.titleLabel.styleSheet()
                dialog.worker=object();dialog.titleBar.closeBtn.click();assert dialog.isVisible()
                dialog.worker=None;dialog.titleBar.closeBtn.click();assert not dialog.isVisible()
                timing=AdvancedTimingDialog(host,host.db);timing.show();app.processEvents()
                assert THEMES[mode]['text'] in timing.titleBar.titleLabel.styleSheet();timing.close()
                donation=DonationDialog(QPixmap('resources/images/windows/donation_qr.png'),host,mode);donation.show();app.processEvents()
                assert not donation.findChildren(QPushButton)
                hint=donation.findChild(QLabel,'informationHint');layout=donation.content_scroll.widget().layout()
                assert layout.itemAt(layout.count()-1).widget() is hint
                assert donation.content_scroll.verticalScrollBar().maximum()==0;donation.close()
                menu=QMenu('界面字号',host);menu.setProperty('topBarMenu',True)
                for text in ('字号+','字号-','字号恢复默认'):menu.addAction(text)
                style_context_menu(menu,host);menu.show();app.processEvents();assert menu.width()<164;menu.close()
            view.resource_timer.stop();view.history_timer.stop();view.close();view.session.close()
        window=QWidget();window.db=host.db;window.resize(340,460);window.show();app.processEvents()
        for mode in ('top_left','bottom_left','top_right','bottom_right'):
            host.db.set_setting_value(POSITION_SETTING,mode);place_compact_window(window);app.processEvents()
            assert window.screen().availableGeometry().contains(window.frameGeometry())
        host.db.set_setting_value(POSITION_SETTING,'last');point=window.screen().availableGeometry().topLeft()+QPoint(60,50)
        window.move(point);save_compact_position(window);window.move(point+QPoint(30,30));place_compact_window(window)
        assert window.pos()==point and host.db.get_setting_value(LAST_POSITION_SETTING)
        window.close()
    print('PASS UI 1.6.7: responsive 13/12/11px actions, themes, settings/reset, model busy guard, donation, font menu and compact position')

if __name__=='__main__':main()
