import sys,tempfile,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from unittest.mock import patch
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.vision_tools.glyphs import GlyphLibrary,_glyph_score,STRICT_MIN_SCORE,PRIORITY_TIE_EPS
from anclicker.platform.vision_tools.runtime import execute,validate,find_glyphs,save_image
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);image=Image.new('RGB',(180,60),'black');ImageDraw.Draw(image).text((10,5),'灯笼',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24),fill='white')
    frame=np.asarray(image)[:,:,::-1].copy();inputs=[]
    ctx=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(root/'test.db'))},services={'离线视觉截图':lambda p:(frame,(0,0),None),'离线视觉输入':lambda *a:inputs.append(a)})
    execute('制作字库',{'区域':'0,0,180,60','目标文字':'灯笼'},ctx)
    p=validate('字库点击',{'区域':'0,0,180,60','目标文字':'灯笼','相似度':.78})
    assert p['匹配方式']=='包含文字'
    assert validate('字库点击',{'区域':'0,0,180,60','目标文字':'灯笼','匹配方式':'完整匹配'})['匹配方式']=='完整匹配'
    assert find_glyphs(frame,p,ctx)
    lib=next(iter(ctx.metadata['glyph_match_cache'].values()))
    with patch.object(lib,'_load_index',side_effect=AssertionError('unchanged library must be reused')):
        assert find_glyphs(frame,p,ctx)
    assert next(iter(ctx.metadata['glyph_match_cache'].values())) is lib
    other=GlyphLibrary(str(root/'glyphs'));other.set_first('笼');find_glyphs(frame,p,ctx);assert lib.labels()[0]=='笼'
    # Batch score/priority equivalence to the independent scalar definition.
    templates=lib._load_templates();glyphs=[g for samples in templates.values() for g in samples]
    glyphs += [np.zeros((24,24),np.float32),np.ones((24,24),np.float32)]
    for strict in (True,False):
        lib.strict=strict
        for glyph,(label,score) in zip(glyphs,lib.match_glyphs(glyphs,.78)):
            values={name:max(_glyph_score(glyph,sample) for sample in templates[name]) for name in lib.labels()}
            best=max(values.values());expected=None
            if best>=.78:
                if strict:expected=next((name for name in lib.labels() if values[name]>=max(.78,STRICT_MIN_SCORE,best-PRIORITY_TIE_EPS)),None)
                if expected is None:expected=next(name for name in lib.labels() if values[name]>=max(.78,best-PRIORITY_TIE_EPS))
            assert label==expected and abs(score-(values[label] if label else best))<1e-5
    # Verify scaled actual Chinese pixels, not just normalized sample arrays.
    for scale in (.8,1.,1.25):
        scaled=cv2.resize(frame,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
        assert find_glyphs(scaled,p,ctx),scale
    for wrong in ('灯花','花笼','灯灯','笼笼'):
        negative=Image.new('RGB',(180,60),'black');ImageDraw.Draw(negative).text((10,5),wrong,font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24),fill='white')
        assert not find_glyphs(np.asarray(negative)[:,:,::-1].copy(),p,ctx),wrong
    assert not find_glyphs(np.zeros_like(frame),p,ctx)
    p['目标文字']='不存在';assert not find_glyphs(frame,p,ctx)
    try:execute('字库点击',p,ctx);raise AssertionError('missing text must not click')
    except ValueError:pass
    assert not inputs
    p['目标文字']=' ; ； '
    try:find_glyphs(frame,p,ctx);raise AssertionError('empty targets')
    except ValueError:pass
    # Exact matching cannot bypass known word boundaries using the phrase cache.
    p['目标文字']='灯笼';p['匹配方式']='完整匹配'
    with patch.object(lib,'scan',return_value=[('灯笼花',.99,[0,0,170,60])]):
        assert not find_glyphs(frame,p,ctx)
        p['匹配方式']='包含文字';assert find_glyphs(frame,p,ctx)[0][0]=='灯笼花'
    p['目标文字']='笼;灯';p['匹配方式']='完整匹配'
    with patch.object(lib,'scan',return_value=[('灯',.99,[5,5,20,30]),('笼',.9,[50,5,70,30]),('笼',.89,[51,5,71,30])]):
        matches=find_glyphs(frame,p,ctx);assert [m[0] for m in matches]==['笼','灯']
    ctx.stop_requested=True;assert not find_glyphs(frame,p,ctx)
print('PASS batch/scalar equivalence, hot reload/cache reuse, Chinese 0.8/1/1.25 scale, blank/wrong targets no input, exact fallback boundaries, target priority, overlap suppression, cancellation')
