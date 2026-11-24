import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='windows';os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='ac-theme-180-')
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QImage,QPainter,QColor
from anclicker.platform.qt_compat.QtCore import Qt,QRect,QEvent
from anclicker.app.Start_Win import Main_window
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.domain.instructions import ExecutionContext
from anclicker.ui.settings_theme import apply_settings_theme
app=QApplication([]);out=ROOT/'artifacts/validation/v1.8.0/theme';out.mkdir(parents=True,exist_ok=True)
errors=[];rows=[];pictures={}
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
 w=Main_window();w.resize(1200,800);w.show();app.processEvents();v=w.view_workspace
 for mode in ('light','dark'):
  v.theme_mode=mode;v._apply_theme();app.processEvents()
  for i in range(v.tabs.count()):
   v.tabs.setCurrentIndex(i);app.processEvents();w.grab().save(str(out/f'main-{mode}-{i}.png'))
  pictures[mode]=[]
  for i,spec in enumerate(INSTRUCTION_SPECS):
   editor=None
   try:
    editor=spec.create_editor(parent=w,context=ExecutionContext(metadata={'database':w.db}));apply_settings_theme(editor,w)
    editor.resize(740,620);editor.show();app.processEvents()
    image=editor.grab().toImage();image.save(str(out/f'editor-{mode}-{i:03}.png'))
    pictures[mode].append((spec.type_id,image));rows.append({'theme':mode,'type':spec.type_id,'width':editor.width(),'height':editor.height()})
   except Exception as e:errors.append({'theme':mode,'type':spec.type_id,'error':str(e)})
   finally:
    if editor is not None:editor.hide();editor.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
  for page in range((len(pictures[mode])+11)//12):
   sheet=QImage(1600,1050,QImage.Format_RGB32);sheet.fill(QColor('#777777'));p=QPainter(sheet)
   for j,(name,img) in enumerate(pictures[mode][page*12:(page+1)*12]):
    x=j%4*400;y=j//4*350;p.setPen(QColor('white'));p.drawText(QRect(x+8,y,384,25),Qt.AlignLeft|Qt.AlignVCenter,name)
    scaled=img.scaled(392,317,Qt.KeepAspectRatio,Qt.SmoothTransformation);p.drawImage(x+4,y+27,scaled)
   p.end();sheet.save(str(out/f'contact-{mode}-{page:02}.png'))
  for offset in (-2,3):
   v.interface_scale.change(None);v.interface_scale.change(offset);w.resize(1000,700);app.processEvents();w.grab().save(str(out/f'main-{mode}-font{offset}.png'))
  v.interface_scale.change(None)
 (out/'report.json').write_text(json.dumps({'editors':rows,'errors':errors},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'checked':len(rows),'errors':errors},ensure_ascii=False),flush=True)
 w.ocr_pool.close();w.hide()
 os._exit(1 if errors else 0)
