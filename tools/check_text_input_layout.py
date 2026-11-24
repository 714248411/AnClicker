import sys,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory();os.environ['ANCLICKER_DATA_DIR']=sandbox.name
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox,QLabel,QComboBox
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
from anclicker.instructions.registry import get_instruction_spec
app=QApplication([]);db=DatabaseOperation(str(Path(sandbox.name)/'test.db'))
with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
 w=Main_window()
w.register_global_shortcut_keys=lambda:None;w.unregister_global_shortcut_keys=lambda:None
w.show();app.processEvents()
view=w.view_workspace
from anclicker.instructions.registry import iter_instruction_specs
from anclicker.platform.qt_compat.QtCore import QTimer
from PIL import Image,ImageDraw
pictures=[]
for spec in [get_instruction_spec('文本输入')]:
 if spec.type_id=='窗口键鼠':continue
 editor=spec.create_editor(parent=w)
 key='parameters_'+spec.type_id
 w.workspace._run_parameter_editor(editor,lambda d:None,key)
 app.processEvents();app.processEvents()
 view.theme_mode='dark';view._apply_theme();app.processEvents()
 dock=view.docking.docks[key];dock.resize(740,660);app.processEvents();app.processEvents()
 filename=Path('artifacts/validation')/(spec.type_id+'-appearance.png')
 dock.grab().save(str(filename));pictures.append((spec.type_id,filename))
 editor.reject();app.processEvents()
canvas=Image.new('RGB',(540*4,550*((len(pictures)+3)//4)),'#ddd');draw=ImageDraw.Draw(canvas)
for index,(name,filename) in enumerate(pictures):
 im=Image.open(filename);im.thumbnail((530,520));x=index%4*540;y=index//4*550
 canvas.paste(im,(x,y+20));draw.text((x,y),str(index)+' '+filename.name,fill='black')
canvas.save('artifacts/validation/window-settings-contact.png')
view.interface_scale.stop();w.ocr_pool.close();w.hide();app.processEvents()
w.deleteLater()
from anclicker.platform.qt_compat.QtCore import QCoreApplication,QEvent
QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
print('PASS rendered',len(pictures))
