"""FF-style multi-point health guard, isolated from its Tk/browser UI."""
import json, math, time, threading
import numpy as np
from . import runtime as vision

MAX_ROWS = 20

def rules_from(value, validate=True):
    rows = json.loads(value) if isinstance(value,str) else value
    if not isinstance(rows,list) or len(rows)>MAX_ROWS:
        raise ValueError('血条检测最多 20 项')
    result=[]
    for index, raw in enumerate(rows):
        if not isinstance(raw,dict):raise ValueError('检测规则格式无效')
        row=dict(raw)
        if validate and row.get('enabled',False):
            try:
                point=vision.actions.point(row.get('pos',''))
                if not str(row.get('pos','')).strip() or not all(math.isfinite(float(n)) and int(n)==float(n) for n in point):
                    raise ValueError('请填写整数检测坐标 x,y')
                vision.color(str(row.get('color','')).replace('，',','))
                key=str(row.get('key','')).strip().lower()
                if not key:raise ValueError('请填写触发按键')
                for part in key.split('+'):key_code(part.strip())
                if row.get('source','屏幕') not in ('屏幕','窗口'):raise ValueError('截图来源无效')
                if row.get('source')=='窗口' and not (row.get('window') or row.get('hwnd')):
                    raise ValueError('请先选择截图窗口')
                tolerance=int(row.get('tolerance',0))
                if not 0<=tolerance<=255:raise ValueError('容差须为 0–255')
                row.update(pos=','.join(str(int(n)) for n in point),color=','.join(map(str,vision.color(str(row['color']).replace('，',',')))),key=key,tolerance=tolerance)
            except Exception as error:raise ValueError('检测 '+str(index+1)+'：'+str(error)) from error
        result.append(row)
    return result


def key_code(key):
    special={'nummultiply':106,'numadd':107,'numsubtract':109,'numdecimal':110,'numdivide':111,'numenter':13,'xbutton1':5,'xbutton2':6}
    if key in special:return special[key]
    if key.startswith('num') and len(key)==4 and key[-1].isdigit():return 96+int(key[-1])
    from anclicker.platform.background_runtime import BackgroundInput
    return BackgroundInput._key(key)


def sample(row, context):
    x,y=map(int,vision.actions.point(row['pos']))
    parameters={'截图来源':row.get('source','屏幕'),'区域':f'{x},{y},1,1',
                '窗口标题':row.get('window',''),'窗口句柄':str(row.get('hwnd','') or '')}
    image,_,hwnd=vision.capture(parameters,context)
    if image is None or image.size==0:raise ValueError('没有获取到检测点图像')
    current=tuple(int(n) for n in image[0,0,::-1])
    expected=vision.color(row['color'])
    changed=any(abs(a-b)>row.get('tolerance',0) for a,b in zip(current,expected))
    return current,changed,hwnd


def press(row,context,hwnd,guard):
    if not hwnd and (row.get('window') or row.get('hwnd')):
        hwnd=vision.window_handle({'窗口标题':row.get('window',''),'窗口句柄':str(row.get('hwnd','') or '')})
    p={'按键':row['key'],'响应':'按键'}
    # Keep the existing injectable input service and global input serialization.
    service=context.service('离线视觉输入')
    with vision.INPUT_LOCK:
        if context.stop_requested or not guard():return
        if service:return service(p,None,hwnd)
        import ctypes
        keys=[key_code(key.strip()) for key in row['key'].split('+')]
        pressed=[]
        def send(vk,down):
            if hwnd:
                import win32gui,win32con
                if vk in (5,6):
                    message=0x020B if down else 0x020C
                    win32gui.PostMessage(hwnd,message,((vk-4)<<16) | ((0x20 if vk==5 else 0x40) if down else 0),0)
                else:win32gui.PostMessage(hwnd,win32con.WM_KEYDOWN if down else win32con.WM_KEYUP,vk,0)
            elif vk in (5,6):
                ctypes.windll.user32.mouse_event(0x0080 if down else 0x0100,0,0,vk-4,0)
            else:ctypes.windll.user32.keybd_event(vk,0,0 if down else 2,0)
        try:
            for vk in keys:
                if not guard():break
                send(vk,True);pressed.append(vk)
        finally:
            for vk in reversed(pressed):send(vk,False)


class GuardHealthMonitor(vision.HealthMonitor):
    def run(self):
        rows=rules_from(self.p['检测规则']);counts=[0]*len(rows);last=[-math.inf]*len(rows)
        errors={}
        while not self.stop.is_set() and not self.context.stop_requested:
            if vision.paused(self.context):
                counts=[0]*len(rows);self.stop.wait(.05);continue
            generation=vision.pause_generation(self.context)
            valid=lambda: (not self.stop.is_set() and not self.context.stop_requested
                           and not vision.paused(self.context) and generation==vision.pause_generation(self.context))
            results={}
            for index,row in enumerate(rows):
                if not valid():break
                if not row.get('enabled',False):continue
                try:
                    current,changed,hwnd=sample(row,self.context)
                    if not valid():counts[index]=0;break
                    results[str(index+1)]={'颜色':list(current),'触发':changed}
                    counts[index]=counts[index]+1 if changed else 0
                    if counts[index]>=self.p['连续次数'] and time.monotonic()-last[index]>=self.p['冷却']:
                        press(row,self.context,hwnd,valid)
                        if valid():
                            last[index]=time.monotonic();counts[index]=0
                            self.context.emit('['+self.p['监控名']+'] 血条检测 '+str(index+1)+' 颜色变化，触发 '+row['key'])
                    errors.pop(index,None)
                except Exception as error:
                    counts[index]=0;message=str(error)
                    if errors.get(index)!=message:
                        self.context.emit('['+self.p['监控名']+'] 检测 '+str(index+1)+'：'+message)
                        errors[index]=message
                    results[str(index+1)]={'错误':message}
            if valid():self.context.set_variable(self.p['变量'],results)
            else:counts=[0]*len(rows)
            self.stop.wait(self.p['间隔'])


def preview(p,context,trigger=False):
    if p.get('守护启用')=='关闭':return {}
    results={}
    generation=vision.pause_generation(context)
    guard=lambda:not context.stop_requested and not vision.paused(context) and generation==vision.pause_generation(context)
    for index,row in enumerate(rules_from(p['检测规则'])):
        if not row.get('enabled',False) or not guard():continue
        current,changed,hwnd=sample(row,context)
        if not guard():break
        results[str(index+1)]={'颜色':list(current),'触发':changed}
        if trigger and changed:press(row,context,hwnd,guard)
    context.set_variable(p['变量'],results)
    return results
