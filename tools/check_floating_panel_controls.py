"""Floating panel toolbar, topmost flags, relative movement and return."""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR'] = tempfile.mkdtemp(prefix='anclicker-floating-')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from anclicker.app.paths import ensure_data_directories
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import Qt, QPoint, QPointF, QEvent
from anclicker.platform.qt_compat.QtGui import QMouseEvent
from anclicker.app.Start_Win import Main_window
os.environ['ANCLICKER_DATA_DIR'] = tempfile.mkdtemp(prefix='anclicker-floating-')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ensure_data_directories()
configure_application()
app = QApplication([])
with patch.object(Main_window, 'register_global_shortcut_keys'), patch.object(Main_window, 'unregister_global_shortcut_keys'):
    window = Main_window(); window.resize(1300,850); window.show(); app.processEvents()
    manager = window.view_workspace.docking
    manager.float_panel('log', True); app.processEvents()
    dock = manager.docks['log']; dock.resize(390,540); dock.move(400,180); app.processEvents()
    dock.set_pinned(False); dock.set_follow_main(False); app.processEvents()
    controls = dock._embedded_title.floating_controls
    assert dock._embedded_title.height() == 0
    assert controls.parentWidget() is dock and controls.y() == 2
    assert controls.isVisible() and not controls.expanded
    assert not controls.pin.isVisible()
    controls.more.click(); app.processEvents()
    assert all(b.isVisible() for b in (controls.pin,controls.follow,controls.restore))
    def drag_more(delta):
        button = controls.more
        local = QPointF(button.rect().center()); global_pos = QPointF(button.mapToGlobal(button.rect().center()))
        QApplication.sendEvent(button, QMouseEvent(QEvent.MouseButtonPress, local, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(button, QMouseEvent(QEvent.MouseMove, local+QPointF(delta), global_pos+QPointF(delta), Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QApplication.sendEvent(button, QMouseEvent(QEvent.MouseButtonRelease, local+QPointF(delta), global_pos+QPointF(delta), Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
        app.processEvents()
    position = dock.pos(); drag_more(QPoint(42,31))
    assert dock.pos() == position + QPoint(42,31) and controls.expanded
    position = dock.pos(); size = dock.size()
    controls.pin.click(); app.processEvents()
    assert dock.pinned and dock.windowFlags() & Qt.WindowStaysOnTopHint
    assert dock.pos() == position and dock.size() == size and dock.isVisible()
    drag_more(QPoint(42,31))
    assert dock.pos() == position, 'Pinned dots must not drag the panel'
    controls.pin.click(); app.processEvents()
    assert not dock.pinned and not dock.windowFlags() & Qt.WindowStaysOnTopHint
    controls.follow.click()
    original = dock.pos(); main = window.pos()
    window.move(main + QPoint(31,27)); app.processEvents()
    assert dock.pos() == original + QPoint(31,27), (dock.pos(),original)
    # A manual move changes the relative offset used by the next main-window move.
    dock.move(dock.pos()+QPoint(11,-9)); app.processEvents(); original = dock.pos()
    window.move(window.pos()+QPoint(-19,13)); app.processEvents()
    assert dock.pos() == original + QPoint(-19,13)
    controls.follow.click(); original = dock.pos()
    window.move(window.pos()+QPoint(20,10)); app.processEvents()
    assert dock.pos() == original
    controls.pin.click(); controls.follow.click(); manager.save()
    options = json.loads(window.db.get_setting_value('五栏停靠布局'))['floating_options']['log']
    assert options == {'pinned':True,'follow':True}
    margins = dock.contentsMargins()
    assert (margins.left(),margins.top(),margins.right(),margins.bottom()) == (1,0,1,1)
    assert abs(controls.geometry().center().x()-dock.rect().center().x()) <= 1
    artifacts = Path('artifacts/validation/floating-panels'); artifacts.mkdir(parents=True, exist_ok=True)
    dock.grab().save(str(artifacts/'expanded.png'))
    controls.more.click(); app.processEvents(); dock.grab().save(str(artifacts/'collapsed.png'))
    controls.more.click(); controls.restore.click(); app.processEvents()
    assert 'log' not in manager.docks and 'log' not in manager.placeholders
    assert manager.pages['log'].parentWidget() is window.view_workspace.table_splitter
    manager.float_panel('palette',True); app.processEvents()
    palette = manager.docks['palette']; palette._embedded_title.floating_controls.restore.click(); app.processEvents()
    assert not palette.isFloating() and not palette._embedded_title.floating_controls.isVisible()
    print('PASS collapsed/expanded toolbar, topmost toggle without jumps, relative follow and manual offsets, persistence, compact margins and return',flush=True)
os._exit(0)
