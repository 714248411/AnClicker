"""Recent-project export UI; file operations run outside the GUI thread."""
import json,os
from pathlib import Path
from anclicker.platform.qt_compat.QtCore import QThread,Signal,Qt
from anclicker.platform.qt_compat.QtWidgets import QFileDialog,QMessageBox,QProgressDialog
from anclicker.app.standalone_export import export_application,control_keys

class ExportWorker(QThread):
 progress=Signal(str)
 def __init__(self,arguments):
  super().__init__();self.arguments=arguments;self.result=None;self.error=None
 def run(self):
  try:self.result=export_application(**self.arguments,progress=self.progress.emit)
  except Exception as error:self.error=str(error)

class ExportProgress(QProgressDialog):
 def finish_export(self):
  if self.worker.error is not None:
   self.reject()
   return
  self.setAutoReset(False)
  self.setAutoClose(False)
  self.setRange(0,100)
  self.setValue(100)
  self.setWindowTitle('打包成功')
  self.setLabelText(self.success_text+'\n\n保存位置：'+str(self.worker.result))
  self.setCancelButtonText('确定')
 def reject(self):
  if not self.worker.isRunning():super().reject()
 def closeEvent(self,event):
  if self.worker.isRunning():event.ignore()
  else:super().closeEvent(event)

def export_recent_application(parent,path):
 owner=parent
 while owner is not None and not hasattr(owner,'db'):owner=owner.parentWidget()
 if owner is None:return
 if os.name!='nt':QMessageBox.warning(owner,'打包独立应用','当前仅支持 Windows 独立应用。');return
 if getattr(owner,'_standalone_export_active',False):return
 try:
  shortcuts=owner.db.get_global_shortcut();control_keys(shortcuts)
  controls={}
  from anclicker.ui.project_run_controls import CACHE_KEY,project_key
  cache=json.loads(owner.db.get_setting_value(CACHE_KEY) or '{}')
  controls={k:v for k,v in cache.get(project_key(path),{}).items() if k in ('运行重复次数','运行未连接模块')}
  filename,_=QFileDialog.getSaveFileName(owner,'保存独立应用 EXE',str(Path(path).with_name(Path(path).stem+'-独立应用.exe')),'Windows 可执行程序 (*.exe)')
  if not filename:return
  target=Path(filename)
  if target.suffix.lower()!='.exe':target=target.with_suffix('.exe')
  worker=ExportWorker(dict(project=path,target=target,shortcuts=shortcuts,controls=controls,resource_root=Path(owner.db.db_path).parent))
  dialog=ExportProgress('准备打包已保存的项目…',None,0,0,owner);dialog.worker=worker
  dialog.setWindowTitle('打包为独立运行应用');dialog.setWindowModality(Qt.ApplicationModal);dialog.setMinimumDuration(0)
  keys=control_keys(shortcuts)
  dialog.success_text=('封装完毕，独立应用已成功生成。双击 EXE 即可运行。\n退出：'
                       +' / '.join('+'.join(k) for k in keys['exit'])
                       +'\n暂停/恢复：'+'+'.join(keys['pause']))
  worker.progress.connect(dialog.setLabelText);worker.finished.connect(dialog.finish_export)
  owner._standalone_export_active=True;worker.start();dialog.exec();worker.wait()
  if worker.error is not None:raise RuntimeError(worker.error)
 except Exception as error:QMessageBox.warning(owner,'打包失败',str(error))
 finally:owner._standalone_export_active=False
