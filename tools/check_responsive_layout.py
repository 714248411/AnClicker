import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='responsive-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMenu
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
from anclicker.ui.layout_presets import LayoutPresets
from anclicker.ui.dynamic_presets import layout_band
app=QApplication([])
assert layout_band(1300,18)=='wide'
assert layout_band(1300,30)=='narrow'
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
    w=Main_window();w.resize(1500,900);w.show();app.processEvents()
    v=w.view_workspace;d=v.docking
    presets=v.layout_presets
    v.palette_collapsed=False
    d.sync_visibility()
    app.processEvents()
    before=w.workspace.repository.snapshot()
    for mode in ('dynamic1','dynamic2'):
        presets.apply(mode)
        for band in ('wide','medium','narrow','wide'):
            with patch('anclicker.ui.dynamic_presets.layout_band',return_value=band):
                presets.responsive.apply(force=True)
                app.processEvents()
            palette,controls=d.docks['palette'],d.docks['controls']
            assert not palette.isFloating() and not controls.isFloating()
            print(mode,band,[x.objectName() for x in d.host.tabifiedDockWidgets(palette)],palette.isHidden(),controls.isHidden(),flush=True)
            if band=='narrow':
                assert d.host.dockWidgetArea(palette)==Qt.BottomDockWidgetArea
                assert controls in d.host.tabifiedDockWidgets(palette)
            elif mode=='dynamic2':
                assert d.host.dockWidgetArea(palette)==Qt.RightDockWidgetArea
                assert (controls in d.host.tabifiedDockWidgets(palette))==(band=='medium')
            else:
                assert d.host.dockWidgetArea(palette)==Qt.LeftDockWidgetArea
                assert d.host.dockWidgetArea(controls)==(Qt.RightDockWidgetArea if band=='wide' else Qt.BottomDockWidgetArea)
            assert w.workspace.repository.snapshot()==before
    # A panel hidden at a breakpoint must join the tab group after it is shown.
    presets.apply('dynamic2')
    v.palette_collapsed=True
    d.sync_visibility()
    with patch('anclicker.ui.dynamic_presets.layout_band',return_value='narrow'):
        presets.responsive.apply(force=True)
        v.palette_collapsed=False
        d.sync_visibility()
        QTest.qWait(220)
        assert d.docks['controls'] in d.host.tabifiedDockWidgets(d.docks['palette'])
    # Real window resize and interface font changes schedule a reflow.
    presets.apply('dynamic1')
    w.resize(1500,900); QTest.qWait(250)
    w.resize(760,900); QTest.qWait(250)
    assert presets.responsive.last[1] == layout_band(d.host.width(), max(w.fontMetrics().height(), 18+v.interface_scale.offset))
    v.interface_scale.change(4); QTest.qWait(250)
    assert presets.responsive.last[1] == layout_band(d.host.width(), max(w.fontMetrics().height(), 18+v.interface_scale.offset))
    v.interface_scale.change(None)
    presets.save()
    assert presets.selected not in ('dynamic1','dynamic2')
    presets.apply('dynamic1')
    restored=LayoutPresets(v,QMenu(w))
    assert restored.selected=='dynamic1'
    presets.reset()
    assert presets.selected is None
    print('PASS both responsive schemes, three widths, transitions, font breakpoint, persistence, save/reset, unchanged commands',flush=True)
    os._exit(0)
