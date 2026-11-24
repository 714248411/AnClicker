"""Portable color variants: names are aliases, never literal extra glyphs."""
import colorsys,json,hashlib,threading
from pathlib import Path
import cv2,numpy as np
from .glyphs import GlyphLibrary,_bg_color_of
LOCK=threading.RLock()
NAMED_COLORS={'红色':(255,0,0),'蓝色':(0,0,255),'黄色':(255,255,0),'绿色':(0,255,0),'青色':(0,255,255),'紫色':(128,0,255),'橙色':(255,128,0),'粉色':(255,0,255),'白色':(255,255,255),'黑色':(0,0,0),'灰色':(128,128,128)}
def color_name(rgb):
    r,g,b=[v/255 for v in rgb];h,s,v=colorsys.rgb_to_hsv(r,g,b)
    if v<.18:return '黑色'
    if s<.18:return '白色' if v>.78 else '灰色'
    hue=h*360
    if hue<18 or hue>=345:return '红色'
    if hue<45:return '橙色'
    if hue<75:return '黄色'
    if hue<165:return '绿色'
    if hue<200:return '青色'
    if hue<260:return '蓝色'
    if hue<310:return '紫色'
    return '粉色'
def rgb_value(value):
    text=str(value).strip().replace('，',',').replace('；',';')
    if text.startswith('#') and len(text)==7:return tuple(int(text[i:i+2],16) for i in (1,3,5))
    values=tuple(int(n.strip()) for n in text.split(','))
    if len(values)!=3 or any(n<0 or n>255 for n in values):raise ValueError('颜色应为 R,G,B 或 #RRGGBB')
    return values

def foreground(image):
    return np.max(np.abs(image.astype(np.int16)-_bg_color_of(image).astype(np.int16)),axis=2)>45

def detect_color(image):
    pixels=image[foreground(image)]
    if len(pixels)==0:raise ValueError('没有可吸取的文字颜色，请点选文字笔画')
    # Quantized dominant foreground avoids averaging different colors into a nonexistent one.
    bins=(pixels//32).astype(np.int32);keys=bins[:,0]*64+bins[:,1]*8+bins[:,2]
    key=np.bincount(keys,minlength=512).argmax();selected=pixels[keys==key]
    return tuple(int(v) for v in np.median(selected,axis=0)[::-1])

def load_variants(directory):
    path=Path(directory)/'colors.json'
    if not path.exists():return []
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,list):raise ValueError('颜色字库索引格式错误')
        for item in data:
            if not isinstance(item,dict) or not all(key in item for key in ('alias','text','rgb','color')):raise ValueError('颜色字库记录不完整')
            rgb_value(','.join(map(str,item['rgb'])))
        return data
    except Exception as error:raise ValueError('无法读取颜色字库：'+str(error)) from error

def record_variant(directory,text,image,rgb=None,name=''):
    rgb=tuple(rgb or detect_color(image));name=name.strip() or color_name(rgb)
    directory=Path(directory)
    with LOCK:
        records=load_variants(directory)
        existing=next((r for r in records if r['text']==text and (max(abs(a-b) for a,b in zip(r['rgb'],rgb))<=24 or color_name(rgb)=='红色' and color_name(r['rgb'])=='红色')),None)
        if existing:
            alias=existing['alias'];existing['color']=name
        else:
            used={r['alias'] for r in records}
            alias=text if color_name(rgb)=='红色' else text+'1'
            number=1
            while alias in used:
                number+=1;alias=text+str(number)
            records.append({'alias':alias,'text':text,'rgb':list(rgb),'color':name})
        folder=directory/'color_samples';folder.mkdir(parents=True,exist_ok=True)
        token=hashlib.sha256(alias.encode('utf-8')).hexdigest()+'.png'
        ok,encoded=cv2.imencode('.png',image)
        if not ok:raise ValueError('颜色样本编码失败')
        encoded.tofile(str(folder/token))
        GlyphLibrary._atomic_json(str(directory/'colors.json'),records)
    return alias

def color_fraction(image,rgb,tolerance=45):
    mask=foreground(image);pixels=image[mask]
    if not len(pixels):return 0.
    reference=np.array(rgb[::-1],np.float32)
    # Allow darker/anti-aliased strokes of the same hue, but keep neutral colors distinct.
    hsv=cv2.cvtColor(pixels.reshape(-1,1,3),cv2.COLOR_BGR2HSV).reshape(-1,3).astype(float)
    target=cv2.cvtColor(np.array([[reference]],np.uint8),cv2.COLOR_BGR2HSV)[0,0].astype(float)
    if target[1]<45:
        matches=(hsv[:,1]<55)&(np.abs(hsv[:,2]-target[2])<=tolerance)
    else:
        delta=np.abs(hsv[:,0]-target[0]);delta=np.minimum(delta,180-delta)
        matches=(delta<=max(3,tolerance/5))&(hsv[:,1]>=max(50,target[1]*.45))&(hsv[:,2]>=35)
    return float(matches.mean())

def priority_tokens(value):
    import re
    text=str(value).replace('；',';').replace('，',',')
    tokens=re.findall(r'#[0-9a-fA-F]{6}|[0-9]+\s*,\s*[0-9]+\s*,\s*[0-9]+|[^,;]+',text)
    result=[]
    for token in tokens:
        token=token.strip()
        if not token:continue
        if token.startswith('#') or ',' in token:
            token=','.join(map(str,rgb_value(token)))
        elif token.isdigit():raise ValueError('RGB 颜色需要三个数值，例如 192,40,21；多个颜色用分号分隔')
        if token not in result:result.append(token)
    return result

def normalize_priorities(value):
    return ';'.join(priority_tokens(value))

def priority_groups(value,records):
    groups=[]
    for token in priority_tokens(value):
        group=[r['rgb'] for r in records if r['color']==token]
        if not group and token in NAMED_COLORS:group=[NAMED_COLORS[token]]
        if not group:
            try:group=[rgb_value(token)]
            except (ValueError,TypeError):pass
        groups.append(group)
    return groups
