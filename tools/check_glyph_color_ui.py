import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='offscreen'
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog
from anclicker.domain.instructions import ExecutionContext
from anclicker.ui.instruction_editors.vision_tools import GlyphLibraryTool
from anclicker.ui.instruction_editors.glyph_color_picker import GlyphColorPicker
from anclicker.ui.instruction_editors.glyph_library_manager import GlyphLibraryManager
app=QApplication([])
with tempfile.TemporaryDirectory() as tmp:
    context=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(Path(tmp)/'test.db'))})
    tool=GlyphLibraryTool(context=context,parameters={'目标文字':'灯笼'})
    image=Image.new('RGB',(100,60),'black');ImageDraw.Draw(image).text((10,5),'灯笼',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24),fill='blue')
    tool.remember_capture(image,(0,0,100,60))
    def select_blue(dialog):
        dialog.canvas.point=(20,20);dialog.add_color((0,0,255));return QDialog.Accepted
    with patch.object(GlyphColorPicker,'exec',select_blue):tool.pick_glyph_color()
    assert tool._controls['颜色名称'].text()=='蓝色' and tool._controls['录入颜色'].text()=='0,0,255'
    tool.save_glyphs();assert '灯笼1' in tool.ui.status.text()
    manager=GlyphLibraryManager(Path(tmp)/'glyphs');assert '灯笼1（蓝色' in manager.colorVersions.itemText(0)
    tool._controls['录入颜色'].setText('255,0,0')
    try:tool.save_glyphs();raise AssertionError('mismatching picked color must not be saved')
    except ValueError as e:assert '没有吸取的颜色' in str(e)
    manager.close();tool.close()
print('PASS eyedropper populates color name/RGB, saved alias displayed in tool and manager, wrong picked color rejected')
