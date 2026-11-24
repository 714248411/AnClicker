"""Windowless project host; no editor, updater or scheduler is constructed."""
import json, os, sys
from pathlib import Path


def main(manifest, *, on_ready=None):
 manifest=Path(manifest).resolve();root=manifest.parent
 config=json.loads(manifest.read_text(encoding='utf8'))
 if config.get('format')!=1 or config.get('project')!='Data/project.xlsx':raise ValueError('独立应用配置无效')
 os.environ['ANCLICKER_DATA_DIR']=str(root/'Data')
 from anclicker.app.startup_environment import prepare_environment
 prepare_environment()
 from anclicker.platform.windows_runtime import configure_dpi
 configure_dpi()
 from anclicker.platform.qt_compat import configure_application,apply_application_style
 from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox
 from anclicker.platform.qt_compat.QtCore import QObject,Signal,QTimer,QLockFile,Qt,QAbstractNativeEventFilter
 configure_application();app=QApplication(sys.argv);apply_application_style(app);app.setQuitOnLastWindowClosed(False)
 lock=QLockFile(str(root/'Data'/'standalone.lock'))
 if not lock.tryLock(0):return 1
 from anclicker.storage.database import DatabaseOperation
 from anclicker.storage.graph_repository import GraphRepository
 from anclicker.app.main_work import CommandThread
 from openpyxl import load_workbook
 db=DatabaseOperation();project=root/config['project']
 book=load_workbook(project)
 try:GraphRepository(db.db_path).import_from_workbook(book,source_path=str(project))
 finally:book.close()
 db.set_setting_value('当前文件路径',str(project))
 from anclicker.app.standalone_export import control_keys
 keys=config['keys'];validated=control_keys({'结束运行':keys['exit'][0], '结束运行2':keys['exit'][1] if len(keys['exit'])>1 else [], '暂停和恢复':keys['pause']})
 class Host(QObject):
  def __init__(self):
   super().__init__();self.execution_services={};self.ocr_pool=None;self.pending=None;self.stopping=False
   self.worker=CommandThread(self)
   self.worker.send_message.connect(self.log)
   self.worker.error_requested.connect(self.error)
   self.worker.finished.connect(app.quit)
  def log(self,text):
   with (root/'Data/logs/standalone.log').open('a',encoding='utf8') as stream:stream.write(str(text)+'\n')
  def error(self,request):
   self.log(request['text'])
   if request.get('retry') and not self.stopping:
    self.pending=request;self.log('已暂停；按暂停/恢复快捷键重试，或按退出快捷键结束。')
   else:request['action']='stop';request['event'].set()
  def action(self,name):
   if name=='exit':
    self.stopping=True;self.worker.request_stop()
    if self.pending:self.pending['event'].set();self.pending=None
    if not self.worker.isRunning():app.quit()
   elif not self.stopping:
    if self.pending:
     request,self.pending=self.pending,None;request['action']='retry';request['event'].set()
    elif self.worker.is_paused:self.worker.resume();self.log('任务恢复')
    else:self.worker.pause();self.log('任务暂停')
 host=Host()
 class Hotkeys(QAbstractNativeEventFilter):
  def __init__(self):
   super().__init__()
   self.registered={}
   self.shared={}
   self.timer=QTimer()
   self.timer.setTimerType(Qt.PreciseTimer)
   self.timer.setInterval(15)
   self.timer.timeout.connect(self.poll_shared)
  def modifiers(self):
   import ctypes
   down=ctypes.windll.user32.GetAsyncKeyState
   return sum(mask for mask,keys in ((1,(0x12,)),(2,(0x11,)),(4,(0x10,)),(8,(0x5b,0x5c)))
              if any(down(key)&0x8000 for key in keys))
  def poll_shared(self):
   import ctypes
   modifiers=self.modifiers()
   for chord,(action,previous) in self.shared.items():
    vk,mods=chord
    down=bool(ctypes.windll.user32.GetAsyncKeyState(vk)&0x8000)
    self.shared[chord]=(action,down)
    if down and not previous and modifiers==mods:
     host.action(action)
  def register(self,keys,action):
   import ctypes
   from anclicker.platform.services import create_system_hotkey
   # Reuse the application's key-name parser, but register synchronously on
   # the Qt message thread so registration failure cannot leave a headless run.
   parser=create_system_hotkey();vk,mods=parser.parse_hotkeylist(parser.order_hotkey(keys))
   ident=0x5100+len(self.registered)
   user32=ctypes.WinDLL('user32',use_last_error=True)
   if not user32.RegisterHotKey(None,ident,mods|0x4000,vk):
    error=ctypes.get_last_error()
    if error!=1409:raise ctypes.WinError(error)
    self.shared[vk,mods]=(action,bool(ctypes.windll.user32.GetAsyncKeyState(vk)&0x8000))
    self.timer.start()
    host.log('快捷键已被占用，启用共享监听：'+'+'.join(keys))
    return
   self.registered[ident]=action
  def nativeEventFilter(self,event_type,message):
   import ctypes
   from ctypes.wintypes import MSG
   msg=MSG.from_address(int(message))
   if msg.message==0x0312 and msg.wParam in self.registered:
    host.action(self.registered[msg.wParam]);return True,0
   return False,0
  def close(self):
   import ctypes
   self.timer.stop()
   for ident in self.registered:ctypes.windll.user32.UnregisterHotKey(None,ident)
   self.registered.clear()
 hotkeys=Hotkeys()
 try:
  for key in validated['exit']:hotkeys.register(key,'exit')
  hotkeys.register(validated['pause'],'pause')
  app.installNativeEventFilter(hotkeys)
  host.worker.set_repeat_number(int(db.get_setting_value('运行重复次数') or '1'))
  host.worker.run_unconnected=db.get_setting_value('运行未连接模块')!='False'
  host.worker.prepare_for_start();QTimer.singleShot(0,host.worker.start)
  if on_ready is not None:on_ready(host,hotkeys)
  result=app.exec()
  return result
 except Exception as error:
  host.log('启动失败：'+str(error));QMessageBox.critical(None,'独立应用无法启动',str(error));return 1
 finally:
  hotkeys.close();app.removeNativeEventFilter(hotkeys);lock.unlock()
