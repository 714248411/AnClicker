import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='dynamic-left-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMenu
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
from anclicker.ui.layout_presets import LayoutPresets,SETTING
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window(); w.resize(1500,900); w.show(); QTest.qWait(200)
 v=w.view_workspace; d=v.docking; presets=v.layout_presets
 v.palette_collapsed=False;d.sync_visibility();app.processEvents()
 names=[a.text() for a in presets.menu.actions()]
 assert names.count('动态方案1')==1
 actions=presets.menu.actions();index=names.index('动态方案1')
 assert actions[index-1].isSeparator() and actions[index+1].isSeparator()
 assert names[index-2]=='更名' and names[index+2]=='恢复默认界面布局'
 assert '动态方案2' not in names and '动态排版1' not in names
 before=w.workspace.repository.snapshot()
 presets.apply('dynamic2')
 assert next(a for a in presets.menu.actions() if a.objectName()=='layout-preset-dynamic2').text()=='动态方案1  ✓'
 for band in ('wide','medium','narrow','wide'):
  with patch('anclicker.ui.dynamic_presets.layout_band',return_value=band):
   presets.responsive.apply(force=True);app.processEvents()
  palette,controls=d.docks['palette'],d.docks['controls']
  assert d.host.dockWidgetArea(palette)==Qt.LeftDockWidgetArea,(band,'palette')
  assert d.host.dockWidgetArea(controls)==Qt.LeftDockWidgetArea,(band,'controls')
  assert controls in d.host.tabifiedDockWidgets(palette)
  assert w.workspace.repository.snapshot()==before
 v.palette_collapsed=True;d.sync_visibility()
 with patch('anclicker.ui.dynamic_presets.layout_band',return_value='narrow'):
  presets.responsive.apply(force=True)
  v.palette_collapsed=False;d.sync_visibility();QTest.qWait(220)
  assert d.docks['controls'] in d.host.tabifiedDockWidgets(d.docks['palette'])
 assert json.loads(w.db.get_setting_value(SETTING))['selected']=='dynamic2'
 w.db.set_setting_value(SETTING,json.dumps({'selected':'dynamic1','items':[],'next':1}))
 restored=LayoutPresets(v,QMenu(w))
 assert restored.selected=='dynamic2'
 restored.responsive.apply(force=True)
 assert d.host.dockWidgetArea(d.docks['palette'])==Qt.LeftDockWidgetArea
 assert d.host.dockWidgetArea(d.docks['controls'])==Qt.LeftDockWidgetArea
 print('PASS single renamed scheme, left panels, wide/medium/narrow, collapsed restore, legacy selection migration and workflow preservation',flush=True)
 os._exit(0)
