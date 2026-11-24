"""Screenshot plus offline OCR evidence; never equate capture with success."""
import json
import time
import uuid
from pathlib import Path
from anclicker.app.paths import TEMP_FOLDER
from anclicker.execution import actions
from anclicker.platform.local_ocr import OcrSession, validated_rows, normalized_text
from anclicker._imports import DeferredImports
_imports=DeferredImports(globals(), {'win32gui':('import','win32gui',(),False),'win32con':('import','win32con',(),False),'win32ui':('import','win32ui',(),False),'ctypes':('import','ctypes',(),False),'Image':('from','PIL',('Image',),0)})

def render_window_client(target):
    gui=_imports.load('win32gui');ui=_imports.load('win32ui');ctypes=_imports.load('ctypes');Image=_imports.load('Image')
    gui.SendMessageTimeout(target,0,0,0,2,1000)
    left,top,right,bottom=gui.GetClientRect(target);width,height=right-left,bottom-top
    if width<=0 or height<=0:raise RuntimeError('窗口客户区为空')
    handle=gui.GetDC(target);source=None;memory=None;bitmap=None
    try:
        source=ui.CreateDCFromHandle(handle);memory=source.CreateCompatibleDC();bitmap=ui.CreateBitmap();bitmap.CreateCompatibleBitmap(source,width,height);memory.SelectObject(bitmap)
        if not ctypes.windll.user32.PrintWindow(target,memory.GetSafeHdc(),3):raise RuntimeError('窗口不支持客户区渲染截图')
        image=Image.frombytes('RGB',(width,height),bitmap.GetBitmapBits(True),'raw','BGRX')
        if max(v[1] for v in image.getextrema())==0:raise RuntimeError('窗口渲染返回空白图像')
        return image
    finally:
        if bitmap is not None:gui.DeleteObject(bitmap.GetHandle())
        if memory is not None:memory.DeleteDC()
        if source is not None:source.DeleteDC()
        gui.ReleaseDC(target,handle)


def capture_target(context, window_title='', region='', window_handle=None):
    bounds=actions.region(region) if region else None
    target=None;rendered=None
    if window_title or window_handle:
        gui=_imports.load('win32gui');con=_imports.load('win32con');matches=[]
        deadline=time.monotonic()+5
        while True:
            matches=[]
            if window_handle:
                if gui.IsWindow(window_handle) and gui.IsWindowVisible(window_handle):matches=[window_handle]
            else:gui.EnumWindows(lambda h,_: matches.append(h) if gui.IsWindowVisible(h) and gui.GetWindowText(h)==window_title else None,None)
            if matches or time.monotonic()>=deadline:break
            if not actions.wait_interruptibly(context,.2):raise InterruptedError('已停止')
        if len(matches)!=1:raise ValueError('目标窗口标题必须唯一且完整；找到 '+str(len(matches))+' 个')
        target=matches[0]
        if gui.IsIconic(target):gui.ShowWindow(target,con.SW_RESTORE)
        try:rendered=render_window_client(target)
        except Exception:
            if gui.GetForegroundWindow()!=target:
                try:gui.SetForegroundWindow(target)
                except Exception as error:raise RuntimeError('窗口无法渲染截图，也无法置前，请手动切换后重试') from error
            if not actions.wait_interruptibly(context,.4):raise InterruptedError('已停止')
            if gui.GetForegroundWindow()!=target:raise RuntimeError('目标窗口未置前，不能用遮挡截图验证')
        left,top,right,bottom=gui.GetClientRect(target)
        x,y=gui.ClientToScreen(target,(left,top))
        bounds=(x,y,right-left,bottom-top)
    if not bounds or bounds[2]<=0 or bounds[3]<=0:raise ValueError('请指定目标窗口完整标题或截图区域 x,y,w,h，避免识别到对话中的预期文字')
    path=Path(TEMP_FOLDER)/'agent-evidence'/('verify-'+uuid.uuid4().hex+'.png')
    path.parent.mkdir(parents=True,exist_ok=True)
    capture=context.service('agent_screenshot')
    image=capture(bounds) if capture else rendered if rendered is not None else actions.pyautogui_module().screenshot(region=bounds)
    context.metadata['_agent_capture_method']='window-client-render' if rendered is not None else 'screen-region'
    image.save(path)
    if target is not None and rendered is None and gui.GetForegroundWindow()!=target:raise RuntimeError('截图时焦点发生变化，核验无效')
    return path

def recognize_window_header(session,path,context,timeout,minimum_score):
    # Long breadcrumb paths can depress confidence for an otherwise clear final name.
    # OCR overlapping crops of the actual header; preserve source and crop artifacts.
    Image=_imports.load('Image');rows=[];artifacts=[]
    with Image.open(path) as source:
        width,height=source.size
        for left in range(0,width,240):
            if context.stop_requested:raise InterruptedError('已停止')
            crop=source.crop((left,0,min(width,left+360),min(height,180)))
            tile=path.with_name(path.stem+'-header-'+str(left)+'.png');crop.save(tile);artifacts.append(str(tile))
            recognized=validated_rows(session.recognize(tile,'RapidOCR',{},context,timeout),minimum_score=minimum_score)
            for row in recognized:
                row=dict(row)
                if row.get('box'):row['box']=[[p[0]+left,p[1]] for p in row['box']]
                if row.get('center'):row['center']=[row['center'][0]+left,row['center'][1]]
                rows.append(row)
    return rows,artifacts


def verify_screen(context, expected_text, window_title='', region='', timeout=20, minimum_score=.7, attempts=2, window_handle=None):
    if not isinstance(expected_text,list) or not expected_text or any(not isinstance(x,str) or not x.strip() for x in expected_text):raise ValueError('预期文字必须为非空字符串列表')
    result={'verified':False,'status':'unconfirmed','expected_text':expected_text,'window_title':window_title,'region':region}
    with OcrSession() as session:
        for attempt in range(attempts):
            if context.stop_requested:raise InterruptedError('已停止')
            try:
                path=capture_target(context,window_title,region,window_handle);result['screenshot']=str(path);result['capture_method']=context.metadata.get('_agent_capture_method','screen-region')
                service=context.service('agent_ocr')
                rows=service(path) if service else session.recognize(path,'RapidOCR',{},context,timeout)
                rows=validated_rows(rows,minimum_score=minimum_score)
                text='\n'.join(row['text'] for row in rows)
                # Match within OCR rows; do not concatenate unrelated distant labels.
                missing=[word for word in expected_text if not any(normalized_text(word) in normalized_text(row['text']) for row in rows)]
                if missing and not service and (window_title or window_handle):
                    extra,artifacts=recognize_window_header(session,path,context,timeout,minimum_score)
                    rows.extend(extra);text='\n'.join(row['text'] for row in rows)
                    missing=[word for word in expected_text if not any(normalized_text(word) in normalized_text(row['text']) for row in rows)]
                    result['supplemental_ocr']=artifacts
                result.update(text=text,rows=rows,missing=missing,attempts=attempt+1,verified=not missing,status='passed' if not missing else 'unconfirmed')
                if not missing:break
            except InterruptedError:raise
            except Exception as error:
                result.update(error=str(error),status='unconfirmed',verified=False);break
            if attempt+1<attempts and not actions.wait_interruptibly(context,.5):raise InterruptedError('已停止')
    if 'screenshot' in result:
        Path(result['screenshot']).with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    context.metadata['agent_verification']=result
    return result
