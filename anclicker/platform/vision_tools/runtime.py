"""Isolated capture, bounded analysis and cancellable background monitors."""
import math, threading, time, hashlib, json
from pathlib import Path
import cv2
import numpy as np
from anclicker.instructions.common import actions
from anclicker.domain.instruction_fields.vision_tools import fields_for
INPUT_LOCK = threading.Lock()

def data_path(value, context, default=''):
    database = getattr(getattr(context, 'runtime', None), 'database', None) or context.metadata.get('database')
    if database:
        root = Path(database.db_path).parent
    else:
        from anclicker.app.paths import DATA_FOLDER
        root = Path(DATA_FOLDER)
    path = Path(actions.substitute_variables(context, str(value or default)))
    return path if path.is_absolute() else root / path

def validate(name, values):
    p = {f.key:f.default for f in fields_for(name)}
    p.update(values)
    if name == '多线程血量判断' and p['操作'] == '停止监控':
        if not p['监控名'].strip(): raise ValueError('请填写监控名称')
        return p
    for f in fields_for(name):
        value = p[f.key]
        if f.required and not str(value).strip(): raise ValueError(f.label + '不能为空')
        if f.kind == 'choice' and value not in f.choices: raise ValueError(f.label + '无效')
        if f.kind in ('int','float'):
            n = float(value)
            if not math.isfinite(n) or not f.minimum <= n <= f.maximum or f.kind == 'int' and n != int(n):
                raise ValueError(f.label + '超出范围')
            p[f.key] = int(n) if f.kind == 'int' else n
    if name=='字库点击':
        from .glyph_colors import normalize_priorities
        p['优先颜色']=normalize_priorities(p.get('优先颜色','红色'))
    if name=='制作字库' and p.get('录入颜色'):
        from .glyph_colors import rgb_value
        rgb_value(p['录入颜色'])
    if name=='多线程血量判断' and p.get('检测方式')=='守护取点检测':
        from .guard_health import rules_from
        rows=rules_from(p['检测规则'],validate=p.get('守护启用')!='关闭')
        p['检测规则']=json.dumps(rows,ensure_ascii=False)
        if p.get('守护启用')!='关闭' and not any(row.get('enabled',False) for row in rows):
            raise ValueError('请启用至少一条血条检测规则')
        return p
    if '区域' in p:
        region = actions.region(p['区域'])
        if not region or region[2] <= 0 or region[3] <= 0: raise ValueError('请设置有效截图区域')
        if p['截图来源'] == '窗口' and not (p['窗口标题'].strip() or p['窗口句柄'].strip()): raise ValueError('请选择窗口或填写窗口标题')
    for key in ('偏移','点击位置','起始坐标','终点坐标'):
        if key in p:
            if not all(math.isfinite(float(n)) for n in actions.point(p[key])): raise ValueError(key+'无效')
    if '血量颜色' in p:
        color(p['血量颜色'])
        if p['响应']=='按键':
            from anclicker.platform.background_runtime import BackgroundInput
            keys=[key.strip() for key in p['按键'].split('+') if key.strip()]
            if not keys: raise ValueError('请设置触发按键')
            for key in keys: BackgroundInput._key(key)
    return p

def color(value):
    rgb = tuple(int(n.strip()) for n in str(value).split(','))
    if len(rgb) != 3 or any(n < 0 or n > 255 for n in rgb): raise ValueError('颜色须为 R,G,B，范围 0–255')
    return rgb

def window_handle(p):
    import win32gui
    hwnd = int(p.get('窗口句柄') or 0)
    title = p.get('窗口标题', '')
    if not hwnd or not win32gui.IsWindow(hwnd) or title and win32gui.GetWindowText(hwnd) != title:
        hwnd = win32gui.FindWindow(None, title) if title else 0
    if not hwnd or not win32gui.IsWindow(hwnd): raise ValueError('目标窗口不存在')
    return hwnd

def capture(p, context):
    service = context.service('离线视觉截图')
    if service: return service(p)
    region = tuple(map(int, actions.region(p['区域'])))
    x,y,w,h = region
    hwnd = None
    if p['截图来源'] == '窗口':
        import win32gui, win32ui, ctypes
        from PIL import Image
        hwnd = window_handle(p)
        left,top,right,bottom = win32gui.GetClientRect(hwnd)
        width,height = right-left,bottom-top
        if win32gui.IsIconic(hwnd): raise ValueError('请先恢复目标窗口再截图')
        if min(x,y) < 0 or x+w > width or y+h > height: raise ValueError('截图区域超出窗口客户区')
        dc = win32gui.GetDC(hwnd); source = win32ui.CreateDCFromHandle(dc)
        memory = source.CreateCompatibleDC(); bitmap = win32ui.CreateBitmap()
        try:
            bitmap.CreateCompatibleBitmap(source,width,height); memory.SelectObject(bitmap)
            if not ctypes.windll.user32.PrintWindow(hwnd,memory.GetSafeHdc(),3): raise RuntimeError('窗口截图失败')
            image = Image.frombuffer('RGB',(width,height),bitmap.GetBitmapBits(True),'raw','BGRX',0,1)
            if all(high == 0 for low,high in image.getextrema()):
                raise RuntimeError('目标窗口返回黑色截图，请使用屏幕截图或调整目标窗口渲染方式')
            image = image.crop((x,y,x+w,y+h))
        finally:
            memory.DeleteDC(); source.DeleteDC(); win32gui.ReleaseDC(hwnd,dc)
            if bitmap.GetHandle(): win32gui.DeleteObject(bitmap.GetHandle())
    else:
        image = actions.pyautogui_module().screenshot(region=region)
    return cv2.cvtColor(np.asarray(image.convert('RGB')),cv2.COLOR_RGB2BGR), (x,y), hwnd

def send_action(p, context, point=None, hwnd=None, guard=None):
    with INPUT_LOCK:
        if context.stop_requested or guard is not None and not guard(): return
        service = context.service('离线视觉输入')
        if service: return service(p,point,hwnd)
        if hwnd:
            import win32gui, win32con
            if not win32gui.IsWindow(hwnd): raise RuntimeError('目标窗口已关闭')
            if point is not None:
                x,y = map(int,point); width,height = win32gui.GetClientRect(hwnd)[2:]
                if not (0 <= x < width and 0 <= y < height): raise ValueError('点击位置超出窗口')
                right = p.get('动作') == '右键单击'
                down,up,flag = (win32con.WM_RBUTTONDOWN,win32con.WM_RBUTTONUP,win32con.MK_RBUTTON) if right else (win32con.WM_LBUTTONDOWN,win32con.WM_LBUTTONUP,win32con.MK_LBUTTON)
                for _ in range(2 if p.get('动作') == '左键双击' else 1):
                    win32gui.PostMessage(hwnd,down,flag,(y<<16)|(x&65535))
                    win32gui.PostMessage(hwnd,up,0,(y<<16)|(x&65535))
            else:
                from anclicker.platform.background_runtime import BackgroundInput
                keys = [BackgroundInput._key(k.strip()) for k in p['按键'].split('+') if k.strip()]
                if not keys: raise ValueError('请填写按键')
                pressed=[]
                try:
                    for key in keys:
                        win32gui.PostMessage(hwnd,win32con.WM_KEYDOWN,key,0); pressed.append(key)
                finally:
                    for key in reversed(pressed): win32gui.PostMessage(hwnd,win32con.WM_KEYUP,key,0)
        elif point is not None:
            actions.mouse_action(p.get('动作','左键单击'),*point)
        else:
            actions.pyautogui_module().hotkey(*[k.strip() for k in p['按键'].split('+') if k.strip()])

def health_percent(image, rgb, tolerance):
    diff = np.abs(image.astype(np.int16)-np.array(rgb[::-1],dtype=np.int16))
    mask = np.all(diff <= tolerance,axis=2)
    # A column counts as blood when at least one third of its pixels match.
    return float(np.mean(np.mean(mask,axis=0) >= 1/3)*100)

def paused(context):
    owner = getattr(getattr(getattr(context,'runtime',None),'wait',None),'__self__',None)
    return bool(getattr(owner,'suspended',False) or getattr(owner,'is_paused',False)
                or getattr(owner,'schedule_pause_requested',False))

def pause_generation(context):
    owner = getattr(getattr(getattr(context,'runtime',None),'wait',None),'__self__',None)
    control = getattr(owner, 'control', None)
    generations = [context.metadata.get('visual_input_generation', 0)]
    while control is not None:
        active = getattr(control, '_active_context', None)
        generations.append(active.metadata.get('visual_input_generation', 0) if active else 0)
        control = getattr(control, 'parent', None)
    return tuple(generations)

class HealthMonitor:
    def __init__(self,p,context):
        self.p,self.context = p,context
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run,name='health-'+p['监控名'],daemon=True)
    def close(self):
        self.stop.set(); self.thread.join(5)
        if self.thread.is_alive(): raise RuntimeError('血量监控截图未退出')
    def run(self):
        consecutive=0; last=-math.inf
        try:
            while not self.stop.is_set() and not self.context.stop_requested:
                if paused(self.context):
                    consecutive=0; self.stop.wait(.05); continue
                generation = pause_generation(self.context)
                image,offset,hwnd = capture(self.p,self.context)
                if (self.stop.is_set() or self.context.stop_requested or paused(self.context)
                        or generation != pause_generation(self.context)):
                    consecutive = 0
                    continue
                value = health_percent(image,color(self.p['血量颜色']),self.p['容差'])
                self.context.set_variable(self.p['变量'],value)
                consecutive = consecutive+1 if value < self.p['阈值'] else 0
                if consecutive >= self.p['连续次数'] and time.monotonic()-last >= self.p['冷却']:
                    if not self.stop.is_set() and not self.context.stop_requested and not paused(self.context):
                        point = actions.point(self.p['点击位置']) if self.p['响应']=='鼠标点击' else None
                        send_action(self.p,self.context,point,hwnd,lambda: not self.stop.is_set() and not paused(self.context) and generation == pause_generation(self.context))
                        last=time.monotonic(); consecutive=0
                self.stop.wait(self.p['间隔'])
        except Exception as error:
            self.context.emit('血量监控已停止：'+str(error))
            self.context.set_variable(self.p['变量']+'_错误',str(error))

def close_monitors(context):
    monitors = list(context.metadata.pop('vision_monitors',{}).values())
    for monitor in monitors: monitor.stop.set()
    error = None
    for monitor in monitors:
        try: monitor.close()
        except Exception as failure: error = error or failure
    if error: raise error

def save_image(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    ok,data=cv2.imencode('.png',image)
    if not ok: raise ValueError('图片编码失败')
    data.tofile(str(path))

def load_image(path):
    image=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None: raise ValueError('无法读取图片：'+str(path))
    return image

def execute(name, values, context):
    p=validate(name,values)
    if name == '多线程血量判断':
        monitors=context.metadata.setdefault('vision_monitors',{})
        old=monitors.get(p['监控名'])
        if p['操作']=='启动监控' and old and old.thread.is_alive() and old.p==p:
            return p['监控名']
        if p['操作']!='单次判断':
            if old: old.close()
            monitors.pop(p['监控名'],None)
        if p['操作']=='停止监控': return None
        if p.get('检测方式')=='守护取点检测':
            from .guard_health import GuardHealthMonitor, preview
            if p.get('守护启用')=='关闭':return None
            if p['操作']=='单次判断':return preview(p,context,trigger=True)
            for key,monitor in list(monitors.items()):
                if not monitor.thread.is_alive():monitors.pop(key,None)
            if len(monitors)>=8:raise ValueError('同时最多运行8个血量监控')
            monitor=GuardHealthMonitor(p,context);monitors[p['监控名']]=monitor;monitor.thread.start()
            return p['监控名']
        if p['操作']=='单次判断':
            image,_,hwnd=capture(p,context)
            value=health_percent(image,color(p['血量颜色']),p['容差'])
            context.set_variable(p['变量'],value)
            if value < p['阈值']: send_action(p,context,actions.point(p['点击位置']) if p['响应']=='鼠标点击' else None,hwnd)
            return value
        for key, monitor in list(monitors.items()):
            if not monitor.thread.is_alive(): monitors.pop(key,None)
        if len(monitors)>=8: raise ValueError('同时最多运行8个血量监控')
        # Capture on the monitor worker; never block the launching flow on PrintWindow.
        monitor=HealthMonitor(p,context); monitors[p['监控名']]=monitor; monitor.thread.start()
        return p['监控名']
    if name in ('制作字库','字库点击'):
        from .glyphs import GlyphLibrary, any_text_mask, red_text_mask, _char_boxes, _norm_glyph
        directory=data_path(p['字库目录'],context,'glyphs')
        if name=='字库点击' and not (directory/'index.json').is_file():
            raise ValueError('字库尚未制作：'+str(directory)+'。请先打开“制作字库”工具保存文字。')
        library=GlyphLibrary(str(directory))
        image,offset,hwnd=capture(p,context)
        if name=='制作字库':
            if p.get('录入颜色'):
                from .glyph_colors import rgb_value,color_fraction
                if color_fraction(image,rgb_value(p['录入颜色']))<.1:raise ValueError('框选文字中没有吸取的颜色，请重新吸取文字笔画的颜色')
            mask = red_text_mask(image) if p['颜色模式']=='红字' else any_text_mask(image)
            pixels = cv2.findNonZero(mask) if mask is not None else None
            if pixels is None: raise ValueError('选区没有可辨识文字')
            x,y,w,h = cv2.boundingRect(pixels)
            count,detail=library.capture_text(image,(0,0,image.shape[1],image.shape[0]),p['目标文字'],color_mode='red' if p['颜色模式']=='红字' else 'any')
            if not count: raise ValueError(str(detail))
            phrase_dir=Path(library.dir)/'phrases';phrase_dir.mkdir(exist_ok=True)
            token=hashlib.sha256(p['目标文字'].encode('utf-8')).hexdigest()
            # Keep a background border: tight crops distort color estimation and morphology.
            save_image(phrase_dir/(token+'.png'),image[max(0,y-4):min(image.shape[0],y+h+4),max(0,x-4):min(image.shape[1],x+w+4)])
            from .glyph_colors import record_variant,rgb_value
            alias=record_variant(directory,p['目标文字'],image,rgb_value(p['录入颜色']) if p.get('录入颜色') else None,p.get('颜色名称',''))
            context.metadata['glyph_saved_alias']=alias
            context.emit('字库已保存：'+alias+'，'+str(count)+'个字'); return count
        matches=find_glyphs(image,p,context)
        found=matches[0] if matches else None
        if found is None: raise ValueError('字库中未找到匹配文字')
        x0,y0,x1,y1=found[2]; dx,dy=actions.point(p['偏移'])
        point=(offset[0]+(x0+x1)/2+dx,offset[1]+(y0+y1)/2+dy)
        send_action(p,context,point,hwnd); context.set_variable(p['变量'],list(point));return point
    if name=='小地图拼接制作大地图':
        from .maps import WorldTracker
        tracker=WorldTracker(stitch_size=p['画布大小'])
        tracker.auto_mm_scale=False
        accepted=0
        for index in range(p['帧数']):
            if not actions.wait_interruptibly(context,0 if index==0 else p['间隔']): return None
            image,_,_=capture(p,context)
            _,response,_=tracker.update(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),response_min=p['配准阈值'])
            if index==0 or response>=p['配准阈值']:
                tracker.add_minimap_image(image); accepted+=1
        if accepted<2: raise ValueError('有效地图帧不足，无法可靠拼接；请保持小地图缩放和朝向一致')
        path=data_path(p['保存路径'],context)
        save_image(path,tracker.stitch_image(disp=0)); tracker.save(str(path.with_suffix('.json')))
        context.set_variable(p['变量'],str(path));return str(path)
    return plan_path(p,context)

def plan_path(p,context):
    from .maps import astar_path
    image=load_image(data_path(p['地图路径'],context)); h,w=image.shape[:2]; cell=p['网格大小']
    sx,sy=map(int,actions.point(p['起始坐标']));gx,gy=map(int,actions.point(p['终点坐标']))
    if not (0<=sx<w and 0<=gx<w and 0<=sy<h and 0<=gy<h): raise ValueError('起点或终点超出地图')
    cols,rows=math.ceil(w/cell),math.ceil(h/cell)
    if rows*cols>1000000: raise ValueError('网格过密，请增大网格像素')
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blocked=set()
    for y in range(rows):
        if context.stop_requested: return None
        for x in range(cols):
            if np.min(gray[y*cell:min(h,(y+1)*cell),x*cell:min(w,(x+1)*cell)])<p['通行阈值']:
                blocked.add((x,y))
    path=astar_path((sx//cell,sy//cell),(gx//cell,gy//cell),blocked,bounds=(0,0,cols-1,rows-1),max_nodes=rows*cols,cancel=lambda:context.stop_requested)
    if context.stop_requested: return None
    if not path: raise ValueError('起终点间没有可通行路线')
    points=[(min(w-1,x*cell+cell//2),min(h-1,y*cell+cell//2)) for x,y in path]
    points[0]=(sx,sy)
    if len(points)==1 and (sx,sy)!=(gx,gy):points.append((gx,gy))
    else:points[-1]=(gx,gy)
    preview=image.copy(); cv2.polylines(preview,[np.array(points,np.int32)],False,(0,180,255),2)
    cv2.circle(preview,(sx,sy),4,(0,220,0),-1);cv2.circle(preview,(gx,gy),4,(0,0,255),-1)
    save_image(data_path(p['保存路径'],context),preview)
    context.set_variable(p['变量'],points);return points

def _find_glyph_shapes(image,p,context):
    """Shared pure detection for preview and execution; never sends input."""
    from .glyphs import GlyphLibrary,any_text_mask,red_text_mask
    directory=data_path(p['字库目录'],context,'glyphs')
    if not (directory/'index.json').is_file():raise ValueError('字库尚未制作：'+str(directory))
    cache=context.metadata.setdefault('glyph_match_cache',{})
    key=str(directory.resolve())
    library=cache.get(key)
    if library is None:
        if len(cache)>=4:cache.pop(next(iter(cache)))
        library=GlyphLibrary(str(directory));cache[key]=library
    else:library.reload_if_changed()
    targets=[text.strip() for text in p['目标文字'].replace('；',';').split(';') if text.strip()]
    targets=list(dict.fromkeys(targets))
    if not targets:raise ValueError('请填写至少一个目标文字')
    if len(targets)>64 or any(len(t)>24 for t in targets):raise ValueError('最多64个目标，每个目标最多24个字')
    if context.stop_requested:return []
    contains=p.get('匹配方式','包含文字')=='包含文字'
    matches=library.scan(image,min_score=p['相似度'],color_mode='red' if p['颜色模式']=='红字' else 'any',allow_single=True)
    missing=[target for target in targets if not any(target in m[0] if contains else target==m[0] for m in matches)]
    exact_components=glyph_components(image,library,p,missing) if missing else []
    found=[]
    for target in targets:
        if context.stop_requested:return []
        selected=[m for m in matches if (target in m[0] if contains else target==m[0])]
        if not selected:
            selected=[m for m in exact_components if m[0]==target]
            if not contains:
                selected=[candidate for candidate in selected if not any(len(run[0])>len(target) and run[2][0]<=candidate[2][0] and run[2][1]<=candidate[2][1] and run[2][2]>=candidate[2][2] and run[2][3]>=candidate[2][3] for run in matches)]
        # Exact phrase masks recover connected characters; character templates retain priority.
        phrase=directory/'phrases'/(hashlib.sha256(target.encode('utf-8')).hexdigest()+'.png')
        if not selected and phrase.is_file() and all(char in library.index for char in target):
            # Phrase matching keeps thin strokes; morphological opening changes small fonts after zoom.
            from .glyphs import _bg_color_of
            def raw_any(frame):
                return (np.max(np.abs(frame.astype(np.int16)-_bg_color_of(frame).astype(np.int16)),axis=2)>45).astype(np.uint8)
            mask_fn=red_text_mask if p['颜色模式']=='红字' else raw_any
            source=mask_fn(image).astype(np.float32);original=load_image(phrase)
            smooth_source=cv2.GaussianBlur(source,(3,3),.65)
            # Bounded multi-scale fallback for text captured at a different UI zoom.
            for scale in (1.,.8,1.25,.9,1.1,.75,1.5):
                if context.stop_requested:return []
                resized=cv2.resize(original,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
                template=mask_fn(resized).astype(np.float32);th,tw=template.shape
                if min(th,tw)<3 or th>source.shape[0] or tw>source.shape[1] or not template.any():continue
                ink_x,ink_y,ink_w,ink_h=cv2.boundingRect(cv2.findNonZero(template.astype(np.uint8)))
                smooth_template=cv2.GaussianBlur(template,(3,3),.65)
                scores=cv2.matchTemplate(smooth_source,smooth_template,cv2.TM_SQDIFF_NORMED)
                for _ in range(100):
                    score,_,position,_=cv2.minMaxLoc(scores)
                    similarity=1-score/2
                    if similarity<p['相似度']:break
                    x,y=position
                    # A correct first character must not hide a wrong second character.
                    patch=smooth_source[y:y+th,x:x+tw]
                    per_char=[]
                    for ci in range(len(target)):
                        left=ink_x+int(ci*ink_w/len(target));right=ink_x+int((ci+1)*ink_w/len(target))
                        a=patch[:,left:right];b=smooth_template[:,left:right]
                        denominator=float(np.sum(a*a)+np.sum(b*b))
                        per_char.append(float(2*np.sum(a*b)/denominator) if denominator else 0.)
                    confidence=min([similarity]+per_char)
                    if confidence>=p['相似度']:selected.append((target,confidence,[x+ink_x,y+ink_y,x+ink_x+ink_w,y+ink_y+ink_h]))
                    scores[max(0,y-th+1):min(scores.shape[0],y+th),max(0,x-tw+1):min(scores.shape[1],x+tw)]=2
        # Apply exact-word boundaries to every source, including phrase fallback.
        if not contains:
            selected=[candidate for candidate in selected if not any(len(run[0])>len(target) and run[2][0]<=candidate[2][0] and run[2][1]<=candidate[2][1] and run[2][2]>=candidate[2][2] and run[2][3]>=candidate[2][3] for run in matches)]
        for match in sorted(selected,key=lambda m:(-m[1],m[2][1],m[2][0])):
            if not any(glyph_box_overlap(match[2],old[2])>=.65 for old in found):found.append(match)
    return found

def glyph_components(image,library,p,targets):
    """Match complete glyphs even when Chinese radicals are disconnected."""
    from .glyphs import any_text_mask,red_text_mask,_char_boxes,_norm_glyph
    mask=red_text_mask(image) if p['颜色模式']=='红字' else any_text_mask(image)
    boxes=_char_boxes(mask)
    if len(boxes)>2000:raise ValueError('识别区域内容过多，请缩小找字区域')
    candidates=[];seen=set();candidate_boxes=[]
    for a in boxes:
        # Keep the neighbourhood local; grouping by x alone mixes separate text rows.
        near=[b for b in boxes if b[0]>=a[0] and b[0]<=a[0]+max(a[3],b[3])*1.5 and abs((b[1]+b[3]/2)-(a[1]+a[3]/2))<max(a[3],b[3])*.5]
        near.sort(key=lambda b:b[0])
        for count in range(1,min(4,len(near))+1):
            group=near[:count];x=min(b[0] for b in group);y=min(b[1] for b in group)
            w=max(b[0]+b[2] for b in group)-x;h=max(b[1]+b[3] for b in group)-y
            if w>h*1.6 or (x,y,w,h) in seen:continue
            seen.add((x,y,w,h));candidate_boxes.append((x,y,w,h))
    scores=library.match_glyphs([_norm_glyph(mask,box) for box in candidate_boxes],p['相似度'])
    for box,(label,score) in zip(candidate_boxes,scores):
        if label:candidates.append((label,score,box))
    output=[]
    for target in targets:
        chains=[([item],item[1]) for item in candidates if item[0]==target[0]]
        for char in target[1:]:
            next_chains=[]
            for chain,score in chains:
                x,y,w,h=chain[-1][2]
                for item in candidates:
                    bx,by,bw,bh=item[2]
                    if item[0]==char and bx>=x+w-1 and bx-(x+w)<=max(h,bh) and abs((by+bh/2)-(y+h/2))<=max(h,bh)*.4:
                        next_chains.append((chain+[item],min(score,item[1])))
            chains=sorted(next_chains,key=lambda c:-c[1])[:100]
        for chain,score in chains:
            bounds=[item[2] for item in chain]
            output.append((target,score,[min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[0]+b[2] for b in bounds),max(b[1]+b[3] for b in bounds)]))
    return output

def glyph_box_overlap(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/max(1,union)

def find_glyphs(image,p,context):
    from .glyph_colors import load_variants,color_fraction,rgb_value
    records=load_variants(data_path(p['字库目录'],context,'glyphs'))
    requested=list(dict.fromkeys(t.strip() for t in p['目标文字'].replace('；',';').split(';') if t.strip()))
    aliases={r['alias']:r for r in records}
    # A base name searches every recorded color; a suffixed alias selects its own color.
    targets=[aliases[t]['text'] if t in aliases else t for t in requested]
    shape_p=dict(p);shape_p['目标文字']=';'.join(targets)
    matches=_find_glyph_shapes(image,shape_p,context)
    from .glyph_colors import priority_groups,priority_tokens
    try:configuration=json.loads(p.get('优先色配置','[]') or '[]')
    except (ValueError,TypeError):raise ValueError('优先色表格配置无效，请重新打开选择优先色')
    if not isinstance(configuration,list):raise ValueError('优先色表格配置无效')
    custom={item['name']:item for item in configuration if isinstance(item,dict) and item.get('enabled',True) and 'name' in item and 'rgb' in item}
    color_records=[r for r in records if r['color'] not in custom]+[{'color':name,'rgb':row['rgb']} for name,row in custom.items()]
    preferred=priority_groups(p.get('优先颜色','红色'),color_records) if p.get('颜色优先','优先颜色')=='优先颜色' else []
    tokens=priority_tokens(p.get('优先颜色','红色'))
    ranked=[]
    for match in matches:
        x0,y0,x1,y1=map(int,match[2]);crop=image[max(0,y0-2):min(image.shape[0],y1+2),max(0,x0-2):min(image.shape[1],x1+2)]
        if not crop.size:continue
        tolerance=p.get('颜色容差',45)
        for index,(request,target) in enumerate(zip(requested,targets)):
            if not (target in match[0] if p.get('匹配方式','包含文字')=='包含文字' else target==match[0]):continue
            record=aliases.get(request)
            if record and request!=record['text'] and color_fraction(crop,record['rgb'],tolerance)<.35:continue
            priority=next((rank for rank,group in enumerate(preferred) if any(color_fraction(crop,rgb,int(custom.get(tokens[rank],{}).get('tolerance',tolerance)))>=.35 for rgb in group)),len(preferred))
            ranked.append((priority,index,-match[1],match[2][1],match[2][0],match));break
    ranked.sort(key=lambda row:row[:5])
    return [row[-1] for row in ranked]
