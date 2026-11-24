import sys, tempfile, threading, io, base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from unittest.mock import patch
from PIL import Image
from anclicker.platform.image_download import download_image
from anclicker.platform.qt_compat.QtWidgets import QApplication,QInputDialog,QFileDialog
from anclicker.platform.qt_compat.QtCore import QEventLoop,QTimer
from anclicker.ui.instruction_editors.extensions.crawl_preview import CrawlResultDialog
buffer=io.BytesIO();Image.new('RGB',(80,30),'red').save(buffer,format='PNG');data=buffer.getvalue()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/redirect':
   self.send_response(302);self.send_header('Location','/image');self.end_headers();return
  body=b'<html>login</html>' if self.path=='/bad' else data
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)
app=QApplication([])
def select_single(dialog):
 dialog.single.setChecked(True);return dialog.Accepted
def wait():
 loop=QEventLoop();QTimer.singleShot(30,loop.quit);loop.exec_()
try:
 with tempfile.TemporaryDirectory() as directory:
  root=Path(directory)
  target=download_image('/redirect',root/'无扩展名',url)
  assert target.suffix=='.png' and target.read_bytes()==data
  assert download_image('data:image/png;base64,'+base64.b64encode(data).decode(),root/'inline.png').read_bytes()==data
  old=root/'existing.png';old.write_bytes(b'keep')
  try:download_image(url+'/bad',old)
  except ValueError:pass
  else:raise AssertionError('HTML accepted')
  assert old.read_bytes()==b'keep'
  try:download_image(url+'/image',old,cancelled=lambda:True)
  except InterruptedError:pass
  else:raise AssertionError('cancel ignored')
  assert old.read_bytes()==b'keep' and not list(root.glob('*.part'))
  dialog=CrawlResultDialog({'title':'图片另存为验证','url':url,'images':[{'url':url+'/image','alt':'红色示例图'}]},selected='图片')
  assert dialog.image_save.isEnabled() and not dialog.video_save.isEnabled()
  with patch('anclicker.ui.instruction_editors.extensions.image_save_range.ImageSaveRangeDialog.exec',select_single),patch.object(QFileDialog,'getSaveFileName',return_value=(str(root/'界面保存.png'),'')):
   dialog.image_save.click()
  for _ in range(200):
   wait()
   if dialog.video_worker is None:break
  assert dialog.video_worker is None
  assert (root/'界面保存.png').read_bytes()==data
  assert dialog.image_save.isEnabled() and not dialog.video_save.isEnabled() and not dialog.video_cancel.isEnabled()
  assert '已保存' in dialog.video_status.text()
  dialog.show();wait();dialog.grab().save('artifacts/validation/crawl-image-save.png');dialog.close()
  # Closing during an active download waits for cancellation before deleting QThread.
  slow=CrawlResultDialog({'url':url,'images':[{'url':url+'/image','alt':'测试'}]})
  def slow_download(url,path,referer,cancelled,progress):
   import time
   while not cancelled():time.sleep(.01)
   raise InterruptedError('已取消下载')
  with patch('anclicker.platform.image_download.download_image',side_effect=slow_download),patch('anclicker.ui.instruction_editors.extensions.image_save_range.ImageSaveRangeDialog.exec',select_single),patch.object(QFileDialog,'getSaveFileName',return_value=(str(old),'')):
   slow.show();slow.image_save.click();slow.reject()
   for _ in range(200):
    wait()
    if slow.video_worker is None:break
   assert slow.video_worker is None and not slow.isVisible() and old.read_bytes()==b'keep'
  empty=CrawlResultDialog({});assert not empty.image_save.isEnabled();empty.close()
 print('PASS original bytes, redirect/relative/data URL, automatic extension, HTML rejection, cancellation/no overwrite, actual UI save and button states')
finally:server.shutdown();server.server_close()
