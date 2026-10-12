import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from qt_compat.QtWidgets import QApplication
from qt_compat.QtCore import QCoreApplication,QEvent
from qt_compat.QtGui import QTextCursor
from 数据库操作 import DatabaseOperation
app=QApplication([])
class Hotkeys:
 def register(self,*a,**k):pass
 def unregister(self,*a,**k):pass
with tempfile.TemporaryDirectory() as temp:
 db=DatabaseOperation(str(Path(temp)/'guide.db'))
 with patch('Start_Win.DatabaseOperation',return_value=db),patch('main_work.DatabaseOperation',return_value=db),patch('Start_Win.SystemHotkey',Hotkeys),patch('Start_Win.is_hotkey_valid',return_value=True):
  from Start_Win import Main_window
  w=Main_window()
 w.resize(1450,900);w.show()
 for theme in ('light','dark'):
  w.view_workspace.theme_mode=theme;w.view_workspace._apply_theme()
  p=w.workspace.palette
  for i in range(p.tree.topLevelItemCount()):p.tree.topLevelItem(i).setExpanded(i==0)
  p.command_added('OCR复制')
  w.view_workspace.show_table();app.processEvents()
  w.grab().save('validation/guidance-'+theme+'.png')
  w.view_workspace.show_code()
  e=w.view_workspace.code_editor
  e.setPlainText('# 中文输入引导示例\n把文字粘贴到表格');e.moveCursor(QTextCursor.End);e.setFocus();e.show_suggestions();app.processEvents()
  w.grab().save('validation/code-guidance-'+theme+'.png')
  e.completer.popup().grab().save('validation/code-candidates-'+theme+'.png')
  e.completer.popup().hide()
 w.view_workspace._save_code()
 w.close();w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
print('Guidance previews saved')
