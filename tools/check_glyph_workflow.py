import os,sys,tempfile,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtGui import QFont
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.ui.instruction_editors.vision_tools import GlyphLibraryTool
from anclicker.ui.instruction_editors.glyph_library_manager import GlyphLibraryManager
from anclicker.platform.vision_tools.runtime import validate,find_glyphs,execute
from anclicker.platform.vision_tools.glyphs import GlyphLibrary
from anclicker.ui.theme import THEMES
from anclicker.ui.settings_theme import apply_settings_theme
app=QApplication([]);app.setFont(QFont('Microsoft YaHei',10))
output=Path('artifacts/validation/glyph-workflow');output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);calls=[]
    context=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(folder/'test.db'))},services={'离线视觉截图':lambda p:(_ for _ in ()).throw(AssertionError('must save frozen frame')),'离线视觉输入':lambda *a:calls.append(a)})
    image=Image.new('RGB',(180,55),'black');draw=ImageDraw.Draw(image)
    draw.text((10,5),'灯笼',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24),fill='white')
    tool=GlyphLibraryTool(context=context,parameters={'目标文字':'灯笼'})
    tool.remember_capture(image,(0,0,180,55));tool.save_glyphs()
    lib=GlyphLibrary(str(folder/'glyphs'));assert set(lib.labels())=={'灯','笼'}
    # Different glyph size records a second sample without replacing the first.
    image2=Image.new('RGB',(180,55),'black');ImageDraw.Draw(image2).text((10,5),'灯笼',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28),fill='yellow')
    tool.remember_capture(image2,(0,0,180,55));tool.save_glyphs()
    lib=GlyphLibrary(str(folder/'glyphs'));assert len(lib.samples('灯'))==2
    manager=GlyphLibraryManager(folder/'glyphs');manager.confirmed=lambda text:True
    manager.labels.setCurrentRow(1);label=manager.current();manager.move_label(-1)
    assert GlyphLibrary(str(folder/'glyphs')).labels()[0]==label
    manager.samples.setCurrentRow(1);before=manager.library.samples(label);manager.move_sample(-1)
    assert GlyphLibrary(str(folder/'glyphs')).samples(label)==list(reversed(before))
    manager.delete_sample();assert len(GlyphLibrary(str(folder/'glyphs')).samples(label))==1
    assert not list((folder/'glyphs'/'phrases').glob('*.png'))
    # Recognize Chinese from character samples, without exact-phrase cache.
    p=validate('字库点击',{'区域':'0,0,180,55','目标文字':'不存在;灯笼','相似度':.78})
    frame=np.asarray(image)[:,:,::-1].copy();matches=find_glyphs(frame,p,context)
    assert matches,matches
    assert not calls
    p['目标文字']='灯';p['匹配方式']='包含文字';assert find_glyphs(frame,p,context)
    context.services['离线视觉截图']=lambda p:(frame,(100,200),None)
    p['偏移']='3,7';point=execute('字库点击',p,context);assert calls and point[0]>100 and point[1]>200
    tool._controls['区域'].setText('1,1,100,30')
    try:tool.save_glyphs();raise AssertionError('changed selection must be rejected')
    except ValueError as e:assert '重新框选' in str(e)
    host=QMainWindow();host.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode='light')
    for mode in ('light','dark'):
        host.view_workspace.theme_mode=mode
        for name,dialog in [('制作字库',tool),('字库管理',manager)]:
            apply_settings_theme(dialog,host);dialog.setAttribute(Qt.WA_DontShowOnScreen,True);dialog.show();app.processEvents();dialog.grab().save(str(output/(name+'-'+mode+'.png')));dialog.hide()
    manager.close();tool.close()
    # Read original library through an isolated copy. Never modify source user data.
    original=Path(r'E:/111/202610.15anclickerFF助手/ffly_all/glyphs')
    if original.exists():
        copied=folder/'original';shutil.copytree(original,copied)
        old=GlyphLibrary(str(copied));browser=GlyphLibraryManager(copied)
        assert browser.labels.count()==len(old.labels()) and len(old)>0
        assert all(Path(old.sample_path(label,sample)).is_file() for label in old.labels() for sample in old.samples(label))
        print(f'PASS original library compatibility: {len(old.labels())} labels, {len(old)} samples');browser.close()
print('PASS frozen-frame creation, multiple Chinese samples, ordering/deletion persistence, cache invalidation, any-color recognition, multiple targets, contains matching, offset click, light/dark UI')
