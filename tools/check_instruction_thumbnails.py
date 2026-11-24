import sys, tempfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTableWidgetItem,QAbstractItemView
from anclicker.platform.qt_compat.QtGui import QImage,QColor,QPalette
from anclicker.platform.qt_compat.QtCore import Qt,QRect
from anclicker.platform.qt_compat.QtCore import QEventLoop,QTimer
class QTest:
 @staticmethod
 def qWait(ms):
  loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec_()
from anclicker.ui.instruction_table import InstructionTableWidget
from anclicker.ui.instruction_thumbnails import *
app=QApplication([])
with tempfile.TemporaryDirectory() as directory:
 p=Path(directory); img=QImage(80,38,QImage.Format_RGB32);img.fill(QColor('#22bbaa'));img.save(str(p/'图片.png'))
 refs=image_references('多图点击',{'图像路径':str(p/'无.png')+';'+str(p/'图片.png')})
 assert len(refs)==2
 assert image_references('截图保存',{'保存路径':'output.png'})==()
 assert image_references('窗口图像点击',{'图像路径':'abc.png'})==('abc.png',)
 assert image_references('后台图色操作',{'接口':'FindPic','参数':'{"pic_name":"a.bmp|b.bmp"}'})==('a.bmp','b.bmp')
 table=InstructionTableWidget(5,3);table.setEditTriggers(QAbstractItemView.NoEditTriggers);table.setHorizontalHeaderLabels(['序号','指令','参数']);table.resize(760,280)
 table.setColumnWidth(0,64);table.setColumnWidth(1,240);table.setColumnWidth(2,400)
 names=['窗口图像点击','多图点击','图像等待','图像点击','时间等待']
 keys=[((str(p/'图片.png'),),'',()),(refs,'',()),((str(p/'无.png'),),'',()),(('☾图片☽',),'',()),None]
 for row in range(5):
  table.setRowHeight(row,38)
  for col,value in enumerate([str(row+1),names[row],'测试参数']):table.setItem(row,col,QTableWidgetItem(value))
  table.item(row,1).setData(THUMBNAIL_ROLE,keys[row])
 table.show()
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  app.processEvents();QTest.qWait(20)
  if len(table.thumbnail_cache.entries)==4:break
 assert len(table.thumbnail_cache.entries)==4,table.thumbnail_cache.entries
 assert not table.thumbnail_cache.image(keys[0]).isNull()
 assert not table.thumbnail_cache.image(keys[1]).isNull()
 assert table.thumbnail_cache.image(keys[2]).isNull()
 assert table.thumbnail_cache.image(keys[3]).isNull()
 label,rect,badge=thumbnail_layout(QRect(0,0,240,38),table.fontMetrics(),names[0],img)
 assert rect.height()==36 and rect.right()<240
 table.setCurrentCell(1,1)
 Path('artifacts/validation').mkdir(parents=True,exist_ok=True)
 QTest.qWait(200);table.grab().save('artifacts/validation/instruction-thumbnails-light.png')
 palette=QPalette();palette.setColor(QPalette.Base,QColor('#25262b'));palette.setColor(QPalette.Text,QColor('#eeeeee'));palette.setColor(QPalette.Window,QColor('#303136'));palette.setColor(QPalette.WindowText,QColor('#eeeeee'));table.setPalette(palette)
 QTest.qWait(200);table.grab().save('artifacts/validation/instruction-thumbnails-dark.png')
 table.setRowHeight(0,60);table.setColumnWidth(1,60);app.processEvents();table.grab()
 table.setColumnWidth(1,240);table.horizontalHeader().moveSection(1,2);app.processEvents();table.grab()
 img.fill(QColor('#dd3300'));img.save(str(p/'无.png'))
 table.thumbnail_cache.entries[keys[2]]=(QImage(),0);table.thumbnail_cache.image(keys[2])
 deadline=time.monotonic()+5
 while table.thumbnail_cache.pending and time.monotonic()<deadline:QTest.qWait(20)
 assert not table.thumbnail_cache.image(keys[2]).isNull()
 from types import SimpleNamespace as NS
 from anclicker.ui.instruction_table import InstructionTableController
 from anclicker.platform.qt_compat.QtWidgets import QLabel
 command=NS(id=1,type_id='窗口图像点击',parameters={'图像路径':str(p/'图片.png')},repeat_count=1,error_policy='自动跳过',note='')
 snapshot=NS(commands=[command],nodes=[])
 model=InstructionTableWidget(0,7);model.update_comment_ranges=lambda snapshot:None
 db=NS(get_setting_value=lambda key:'project.xlsx',extract_resource_folder_path=lambda:[])
 class Workspace(NS):pass
 workspace=Workspace(command_table=model,table_state=QLabel(),window=NS(db=db),_current_graph_state=lambda:(snapshot,None),_apply_comment_row_colors=lambda snapshot:None,highlight_running_command=lambda *a,**k:None,running_command_id=None)
 controller=InstructionTableController(workspace);controller.refresh_table()
 assert model.item(0,2).data(THUMBNAIL_ROLE)[0]==(str(p/'图片.png'),)
 controller.refresh_table()
 db.get_setting_value=lambda key:'other.xlsx';controller.refresh_table()
 assert model.item(0,2).data(THUMBNAIL_ROLE)[1]=='other.xlsx'
 command.type_id='时间等待';command.parameters={};controller.refresh_table()
 assert model.item(0,2).data(THUMBNAIL_ROLE) is None
 model.close()
 table.close();table.thumbnail_cache.pool.waitForDone()
print('PASS: image inputs, multi-image fallback, missing/variable inputs, async decoding, changed images, row/column resizing, selection, light/dark rendering')
