import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'QCoreApplication_QEvent': ('from', 'anclicker.platform.qt_compat.QtCore', ('QCoreApplication', 'QEvent'), 0),
    'QTextCursor': ('from', 'anclicker.platform.qt_compat.QtGui', ('QTextCursor',), 0),
    'DatabaseOperation': ('from', 'anclicker.storage.database', ('DatabaseOperation',), 0),
    'Main_window': ('from', 'anclicker.app.Start_Win', ('Main_window',), 0),
})

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
os.environ['QT_QPA_PLATFORM']='windows'
QApplication = _module_imports.load('QApplication')
QCoreApplication, QEvent = _module_imports.load('QCoreApplication_QEvent')
QTextCursor = _module_imports.load('QTextCursor')
DatabaseOperation = _module_imports.load('DatabaseOperation')
app=QApplication([])
class Hotkeys:
 def register(self,*a,**k):pass
 def unregister(self,*a,**k):pass
with tempfile.TemporaryDirectory() as temp:
 db=DatabaseOperation(str(Path(temp)/'guide.db'))
 with patch('Start_Win.DatabaseOperation',return_value=db),patch('main_work.DatabaseOperation',return_value=db),patch('Start_Win.SystemHotkey',Hotkeys),patch('Start_Win.is_hotkey_valid',return_value=True):
  Main_window = _module_imports.load('Main_window')
  w=Main_window()
 w.resize(1450,900);w.show()
 for theme in ('light','dark'):
  w.view_workspace.theme_mode=theme;w.view_workspace._apply_theme()
  p=w.workspace.palette
  for i in range(p.tree.topLevelItemCount()):p.tree.topLevelItem(i).setExpanded(i==0)
  p.command_added('OCR复制')
  w.view_workspace.show_table();app.processEvents()
  w.grab().save('artifacts/validation/guidance-'+theme+'.png')
  w.view_workspace.show_code()
  e=w.view_workspace.code_editor
  e.setPlainText('# 中文输入引导示例\n把文字粘贴到表格');e.moveCursor(QTextCursor.End);e.setFocus();e.show_suggestions();app.processEvents()
  w.grab().save('artifacts/validation/code-guidance-'+theme+'.png')
  e.completer.popup().grab().save('artifacts/validation/code-candidates-'+theme+'.png')
  e.completer.popup().hide()
 w.view_workspace._save_code()
 w.close();w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
print('Guidance previews saved')
