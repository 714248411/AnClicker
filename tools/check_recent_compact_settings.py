"""Exercise recent context removal, editable hints and compact size preferences."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch,Mock
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import QPoint, QPointF, QEvent, Qt
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent, QMouseEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QCheckBox
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.dialogs.设置窗口 import Setting
from anclicker.ui.compact_position import LAST_SIZE_SETTING,SIZE_MODE_SETTING,resize_compact_window,POSITION_SETTING,LAST_POSITION_SETTING,place_compact_window


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        folder=Path(directory);db=DatabaseOperation(str(folder/'task.db'))
        with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
            window=Main_window()
        window.register_global_shortcut_keys=lambda:None;window.unregister_global_shortcut_keys=lambda:None
        window.resize(1180,720);window.show();app.processEvents();view=window.view_workspace
        first=folder/'项目甲.xlsx';second=folder/'项目乙.xlsx'
        first.write_bytes(b'file one');second.write_bytes(b'file two');db.add_recent_files([str(first),str(second)])
        db.set_setting_value('当前文件路径',str(first));window.add_recent_to_fileMenu()
        picker=window.recent_project_picker;opened=Mock();picker.openRequested.connect(opened)
        picker.combo.showPopup();app.processEvents();row=picker.combo.findData(str(first));index=picker.combo.model().index(row,0)
        point=picker.combo.view().visualRect(index).center();surface=picker.combo.view().viewport()
        for kind in (QEvent.MouseButtonPress,QEvent.MouseButtonRelease):
            QApplication.sendEvent(surface,QMouseEvent(kind,QPointF(point),Qt.RightButton,Qt.RightButton if kind==QEvent.MouseButtonPress else Qt.NoButton,Qt.NoModifier))
        assert not opened.called
        with patch('anclicker.ui.recent_projects.recent_remove_menu',return_value=True):
            QApplication.sendEvent(surface,QContextMenuEvent(QContextMenuEvent.Mouse,point,surface.mapToGlobal(point)))
        app.processEvents();assert not opened.called
        assert str(first) not in db.get_recently_opened_file('文件列表') and picker.combo.findData(str(first))<0
        assert db.get_setting_value('当前文件路径')==str(first) and first.read_bytes()==b'file one'
        menu=window.menuzv;menu.popup(window.mapToGlobal(QPoint(20,40)));app.processEvents()
        action=next(a for a in menu.actions() if a.data()==str(second));point=menu.actionGeometry(action).center()
        with patch('anclicker.ui.recent_projects.recent_remove_menu',return_value=True):
            QApplication.sendEvent(menu,QContextMenuEvent(QContextMenuEvent.Mouse,point,menu.mapToGlobal(point)))
        app.processEvents();assert not db.get_recently_opened_file('文件列表') and second.read_bytes()==b'file two'
        print('PASS both recent lists remove records with real context events, stay synchronized, preserve current task and disk files',flush=True)
        for enabled in (False,True,False):
            view.docking.set_editable(enabled)
            widgets=[w for w in view.docking.host.findChildren(QWidget) if w.property('dockEditableHint')]
            assert len(widgets)>=6
            assert all(bool(w.toolTip())==enabled for w in widgets)
        print('PASS docking hover hints follow editable view immediately',flush=True)
        settings=Setting(window);settings.show();app.processEvents()
        assert settings.tabWidget.tabText(0)=='小窗口设置'
        assert len(settings.other_settings_page.findChildren(QCheckBox))==4
        assert settings.compact_position.count()==5
        assert settings.compact_last_size.isChecked() and not settings.compact_original_size.isChecked()
        settings.compact_original_size.click();assert settings.compact_original_size.isChecked() and not settings.compact_last_size.isChecked()
        settings.compact_last_size.click();assert settings.compact_last_size.isChecked() and not settings.compact_original_size.isChecked()
        settings.compact_last_size.click();assert settings.compact_last_size.isChecked()
        with patch('anclicker.ui.dialogs.设置窗口.global_hotkeys_supported',return_value=False):settings.save_setting_date()
        assert db.get_setting_value(SIZE_MODE_SETTING)=='last'
        proof=Path('artifacts/validation');proof.mkdir(parents=True,exist_ok=True)
        settings.grab().save(str(proof/'small-window-settings.png'));settings.close()
        normal_size=window.size();compact=view.compact
        compact.set_active(True);app.processEvents()
        assert window.pos()==window.screen().availableGeometry().topLeft()
        assert json.loads(db.get_setting_value(LAST_SIZE_SETTING))=={'width':340,'height':460}
        first_position=json.loads(db.get_setting_value(LAST_POSITION_SETTING))
        assert first_position=={'x':window.pos().x(),'y':window.pos().y()}
        remembered=window.screen().availableGeometry().topLeft()+QPoint(55,65)
        window.move(remembered)
        window.resize(410,510);app.processEvents();compact.set_active(False);app.processEvents()
        assert json.loads(db.get_setting_value(LAST_SIZE_SETTING))=={'width':410,'height':510}
        assert window.size()==normal_size,(window.size(),normal_size)
        compact.set_active(True);app.processEvents();assert (window.width(),window.height())==(410,510)
        assert window.pos()==remembered
        title_bottom=view.title_bar.geometry().bottom()+1
        top=window.groupBox_3.mapTo(window,QPoint()).y()
        assert abs(top-title_bottom-3)<=1,(top,title_bottom)
        window.grab().save(str(proof/'small-window-remembered.png'))
        compact.set_active(False);app.processEvents()
        assert view.restore_compact_size_action in view.layout_menu.actions()
        db.set_setting_value(SIZE_MODE_SETTING,'default')
        full_size=window.size();view.restore_compact_size_action.trigger()
        assert not compact.active and window.size()==full_size
        assert db.get_setting_value(SIZE_MODE_SETTING)=='last'
        compact.set_active(True);app.processEvents();assert (window.width(),window.height())==(340,460)
        assert window.pos()==remembered
        window.resize(380,480);app.processEvents();compact.set_active(False);app.processEvents()
        compact.set_active(True);app.processEvents();assert (window.width(),window.height())==(380,480)
        view.restore_compact_size_action.trigger();app.processEvents();assert (window.width(),window.height())==(340,460)
        assert db.get_setting_value(SIZE_MODE_SETTING)=='last'
        settings=Setting(window);assert settings.compact_last_size.isChecked() and not settings.compact_original_size.isChecked();settings.close()
        compact.set_active(False);app.processEvents();db.set_setting_value(SIZE_MODE_SETTING,'default')
        compact.set_active(True);app.processEvents();assert (window.width(),window.height())==(340,460)
        window.grab().save(str(proof/'small-window-default.png'));compact.set_active(False);app.processEvents()
        settings=Setting(window);settings.compact_original_size.click()
        with patch('anclicker.ui.dialogs.设置窗口.global_hotkeys_supported',return_value=False):settings.save_setting_date()
        settings.close()
        assert db.get_setting_value(SIZE_MODE_SETTING)=='default'
        db.set_setting_value(SIZE_MODE_SETTING,'last')
        window.showNormal();window.resize(1050,680);window.move(window.screen().availableGeometry().topLeft()+QPoint(75,85));app.processEvents()
        main_rect=window.geometry()
        compact_size=json.loads(db.get_setting_value(LAST_SIZE_SETTING));compact_position=db.get_setting_value(LAST_POSITION_SETTING)
        window.showMaximized();app.processEvents()
        compact.set_active(True);app.processEvents()
        assert not window.isMaximized()
        window.resize(390,490);window.move(window.screen().availableGeometry().topLeft()+QPoint(25,35));app.processEvents()
        small_rect=window.geometry()
        controller=window._window_state_controller;controller._saved=False;controller.save_window_state()
        saved_main=db.get_window_state(controller.window_name)
        assert tuple(saved_main['size'])==(main_rect.width(),main_rect.height()) and saved_main['maximized'],saved_main
        window.showMaximized();app.processEvents();window.showNormal();app.processEvents()
        assert window.geometry()==small_rect,(window.geometry(),small_rect)
        compact.set_active(False);app.processEvents();assert window.isMaximized()
        window.showNormal();app.processEvents();assert window.geometry()==main_rect,(window.geometry(),main_rect)
        saved_small_size=db.get_setting_value(LAST_SIZE_SETTING);saved_small_position=db.get_setting_value(LAST_POSITION_SETTING)
        window.resize(1100,700);window.move(window.screen().availableGeometry().topLeft()+QPoint(95,105));app.processEvents()
        newer_main_rect=window.geometry()
        assert db.get_setting_value(LAST_SIZE_SETTING)==saved_small_size and db.get_setting_value(LAST_POSITION_SETTING)==saved_small_position
        compact.set_active(True);app.processEvents();assert window.geometry()==small_rect,(window.geometry(),small_rect)
        controller._saved=False;controller.save_window_state();saved_main=db.get_window_state(controller.window_name)
        assert tuple(saved_main['size'])==(newer_main_rect.width(),newer_main_rect.height()) and not saved_main['maximized']
        compact.set_active(False);app.processEvents();assert window.geometry()==newer_main_rect
        print('PASS main/compact positions and sizes independent across resize, move, maximize/restore and close-state persistence',flush=True)
        test=QWidget();test.db=db;test.setMinimumSize(280,350)
        db.set_setting_value(SIZE_MODE_SETTING,'last')
        for bad in ('oops','{}','{"width":false,"height":400}','{"width":-1,"height":500}'):
            db.set_setting_value(LAST_SIZE_SETTING,bad);resize_compact_window(test);assert (test.width(),test.height())==(340,460)
        db.set_setting_value(POSITION_SETTING,'last')
        for bad in ('','{}','oops','[]','{"x":false,"y":20}'):
            db.set_setting_value(LAST_POSITION_SETTING,bad)
            test.move(test.screen().availableGeometry().topLeft()+QPoint(100,100))
            place_compact_window(test)
            assert test.pos()==test.screen().availableGeometry().topLeft()
        db.set_setting_value(LAST_SIZE_SETTING,json.dumps({'width':99999,'height':99999}));resize_compact_window(test)
        assert test.width()<=test.screen().availableGeometry().width()
        print('PASS small-window first tab, four other options, exclusive sizes, persisted resize/reentry, restored full window, 3px title gap and invalid size fallback',flush=True)
        test.close();window.close();window.ocr_pool.close();app.processEvents()
    return 0


if __name__=='__main__':raise SystemExit(main())
