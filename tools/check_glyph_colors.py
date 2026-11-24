import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.vision_tools.runtime import execute,validate,find_glyphs
from anclicker.platform.vision_tools.glyph_colors import load_variants,color_name,rgb_value
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
def sample(color):
    image=Image.new('RGB',(100,60),'black');ImageDraw.Draw(image).text((10,5),'灯笼',font=font,fill=color)
    return np.asarray(image)[:,:,::-1].copy()
with tempfile.TemporaryDirectory() as temp:
    folder=Path(temp);current=[sample('yellow')];clicks=[]
    ctx=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(folder/'test.db'))},services={'离线视觉截图':lambda p:(current[0],(0,0),None),'离线视觉输入':lambda p,point,hwnd:clicks.append(point)})
    for color,expected in [('yellow','灯笼1'),('red','灯笼'),('blue','灯笼2'),('yellow','灯笼1')]:
        current[0]=sample(color);execute('制作字库',{'区域':'0,0,100,60','目标文字':'灯笼'},ctx)
        assert ctx.metadata['glyph_saved_alias']==expected,(color,ctx.metadata)
    records=load_variants(folder/'glyphs');assert len(records)==3
    assert {r['color'] for r in records}=={'红色','黄色','蓝色'}
    scene=Image.new('RGB',(450,70),'black');draw=ImageDraw.Draw(scene)
    for x,color in [(10,'yellow'),(170,'red'),(330,'blue')]:draw.text((x,5),'灯笼',font=font,fill=color)
    current[0]=np.asarray(scene)[:,:,::-1].copy()
    p=validate('字库点击',{'区域':'0,0,450,70','目标文字':'灯笼','相似度':.78})
    point=execute('字库点击',p,ctx);assert 170<point[0]<240,point
    p['优先颜色']='红色；蓝色；黄色'
    original=current[0].copy()
    current[0][:,160:260]=0
    assert execute('字库点击',p,ctx)[0]>330
    current[0][:,320:450]=0
    assert execute('字库点击',p,ctx)[0]<100
    current[0]=original
    import json
    p['优先颜色']='优先蓝;红色';p['优先色配置']=json.dumps([{'name':'优先蓝','rgb':[0,0,255],'tolerance':30,'enabled':True}])
    assert execute('字库点击',p,ctx)[0]>330
    p['优先颜色']='蓝色';point=execute('字库点击',p,ctx);assert point[0]>330,point
    p['优先颜色']='255,255,0';point=execute('字库点击',p,ctx);assert point[0]<100,point
    p['目标文字']='灯笼2';p['优先颜色']='红色';point=execute('字库点击',p,ctx);assert point[0]>330,point
    p['目标文字']='灯笼1';point=execute('字库点击',p,ctx);assert point[0]<100,point
    current[0]=sample('red');assert not find_glyphs(current[0],p,ctx)
    assert color_name(rgb_value('#FF0000'))=='红色' and color_name((0,255,255))=='青色'
    # Same archive data copied elsewhere keeps aliases and priority usable.
    import shutil
    copied=folder/'Data1';shutil.copytree(folder/'glyphs',copied/'glyphs')
    moved=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(copied/'test.db'))})
    p['目标文字']='灯笼';assert find_glyphs(current[0],p,moved)
print('PASS red base name, other colors numbered, repeat color reuse, red/blue/picked-yellow priority, exact alias color restriction, missing color no match, portable Data copy')
