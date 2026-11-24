import sys,tempfile,base64,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from PIL import Image
from anclicker.platform.qt_compat.QtWidgets import QApplication,QFileDialog,QMessageBox,QDialog
from anclicker.platform.qt_compat.QtCore import QEventLoop,QTimer
from anclicker.ui.instruction_editors.extensions.image_save_range import ImageSaveRangeDialog,BatchImageDownloadWorker
from anclicker.ui.instruction_editors.extensions.crawl_preview import CrawlResultDialog
app=QApplication([])
def wait():
 loop=QEventLoop();QTimer.singleShot(30,loop.quit);loop.exec_()
buf=io.BytesIO();Image.new('RGB',(20,20),'green').save(buf,format='PNG');data=buf.getvalue()
url='data:image/png;base64,'+base64.b64encode(data).decode()
images=[{'url':url,'alt':'同名图片'} for _ in range(5)]
selection=ImageSaveRangeDialog(images)
assert selection.indices()==[0,1,2,3,4] and not selection.first.isEnabled()
selection.single.setChecked(True);selection.number.setValue(3);assert selection.indices()==[2]
selection.range.setChecked(True);selection.first.setValue(2);selection.last.setValue(4)
assert selection.indices()==[1,2,3] and selection.first.isEnabled() and not selection.number.isEnabled()
selection.first.setValue(5);selection.last.setValue(2)
with patch.object(QMessageBox,'warning') as warning:
 selection.accept();warning.assert_called_once();assert selection.result()!=QDialog.Accepted
selection.first.setValue(2);selection.last.setValue(4);selection.show();wait()
selection.grab().save('artifacts/validation/image-save-range.png');selection.close()
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);worker=BatchImageDownloadWorker(None,images,[1,2,3],root,'');worker.run()
 assert len(list(root.glob('*.png')))==3 and all(p.read_bytes()==data for p in root.glob('*.png'))
 assert {p.name[:3] for p in root.glob('*.png')}=={'002','003','004'}
 worker=BatchImageDownloadWorker(None,images,[1,2,3],root,'');worker.run()
 assert len(list(root.glob('*.png')))==6 and len(worker.report)==4
 # A failed item is reported without stopping subsequent files.
 bad=[{'url':'blob:missing','alt':'坏图'},images[0]]
 worker=BatchImageDownloadWorker(None,bad,[0,1],root,'');worker.run()
 assert '成功 1 张，失败 1 张' in worker.summary
 cancelled=BatchImageDownloadWorker(None,images,list(range(5)),root,'');cancelled.cancelled=True;cancelled.run()
 assert '成功 0 张' in cancelled.summary and '未保存 5 张' in cancelled.summary
 # Actual save button selects range and directory, starts worker and restores controls.
 dialog=CrawlResultDialog({'images':images})
 def choose_range(d):
  d.range.setChecked(True);d.first.setValue(2);d.last.setValue(3);return QDialog.Accepted
 with patch.object(ImageSaveRangeDialog,'exec',choose_range),patch.object(QFileDialog,'getExistingDirectory',return_value=str(root)):
  dialog.image_save.click()
 for _ in range(100):
  wait()
  if dialog.video_worker is None:break
 assert dialog.video_worker is None and '成功 2 张' in dialog.video_status.text()
 assert dialog.image_save.isEnabled() and not dialog.video_cancel.isEnabled() and not dialog.report_button.isHidden()
 assert len(dialog.download_report)==3
 dialog.close()
print('PASS all/single/inclusive range, invalid bounds, original indices, collision-safe repeated saves, partial failure continuation, cancellation, UI range/directory integration and download report')
