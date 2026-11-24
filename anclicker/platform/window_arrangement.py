"""Native window enumeration, verified movement and a stoppable vacancy watcher."""
import ctypes
import json
import os
import sys
import threading
import time
from anclicker.domain.window_arrangement import layout_rectangles
from anclicker._imports import DeferredImports

_imports=DeferredImports(globals(),{
    'gui':('import','win32gui',(),False),
    'api':('import','win32api',(),False),
    'con':('import','win32con',(),False),
    'Windows':('from','anclicker.platform.background_runtime',('Windows',),0),
})


def native():
    if sys.platform!='win32':raise RuntimeError('窗口排布目前支持 Windows')
    return _imports.load('gui'),_imports.load('api'),_imports.load('con'),_imports.load('Windows')()


def list_screens():
    gui,api,con,windows=native();screens=[]
    for handle,_,_ in api.EnumDisplayMonitors():
        info=api.GetMonitorInfo(handle);scale=100
        try:
            dpi_x,dpi_y=ctypes.c_uint(),ctypes.c_uint()
            query=ctypes.WinDLL('shcore').GetDpiForMonitor
            query.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_uint),ctypes.POINTER(ctypes.c_uint)]
            if query(int(handle),0,ctypes.byref(dpi_x),ctypes.byref(dpi_y))==0:scale=round(dpi_x.value/96*100)
        except (OSError,AttributeError):pass
        screens.append({'id':info['Device'],'rect':list(info['Monitor']),'work':list(info['Work']),
                        'primary':bool(info.get('Flags',0)&1),'scale':scale})
    screens.sort(key=lambda item:(not item['primary'],item['rect'][0],item['rect'][1]))
    return screens


def choose_screen(value):
    screens=list_screens()
    if not screens:raise RuntimeError('没有可用屏幕')
    if value in ('主屏幕','',None):return next((item for item in screens if item['primary']),screens[0])
    found=next((item for item in screens if item['id']==value),None)
    if found is None:raise RuntimeError('所选屏幕已断开，请重新选择屏幕')
    return found


def describe_window(hwnd, windows=None, *, description=None):
    gui,api,con,backend=native();backend=windows or backend
    item=dict(description) if description is not None else backend.describe(int(hwnd));item['rect']=list(gui.GetWindowRect(int(hwnd)))
    client=gui.GetClientRect(int(hwnd));item['client_size']=[client[2],client[3]]
    item['minimized']=bool(gui.IsIconic(int(hwnd)))
    item['normal_rect']=list(gui.GetWindowPlacement(int(hwnd))[4])
    return item


def list_windows():
    gui,api,con,windows=native();found=[]
    handles=[]
    def collect(hwnd,_):
        # Exclude this process before GetWindowText: asking the GUI thread for
        # its caption while that thread joins the watcher would deadlock stop.
        if windows.process.GetWindowThreadProcessId(hwnd)[1]!=os.getpid() and gui.IsWindowVisible(hwnd):handles.append(hwnd)
    gui.EnumWindows(collect,None)
    for hwnd in handles:
        try:
            item=windows.describe(hwnd)
            if not item['窗口标题'].strip() or item['窗口类名'] in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):continue
            if gui.GetWindowLong(hwnd,con.GWL_EXSTYLE)&con.WS_EX_TOOLWINDOW:continue
            if gui.GetAncestor(hwnd,2)!=hwnd:continue
            try:
                cloaked=ctypes.c_uint()
                dwm=ctypes.WinDLL('dwmapi').DwmGetWindowAttribute
                dwm.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
                if dwm(hwnd,14,ctypes.byref(cloaked),ctypes.sizeof(cloaked))==0 and cloaked.value:continue
            except (OSError,AttributeError):pass
            found.append(describe_window(hwnd,windows,description=item))
        except (RuntimeError,OSError,gui.error):continue
    return found


def parse_targets(value):
    try:items=json.loads(value) if isinstance(value,str) else value
    except (ValueError,TypeError) as error:raise ValueError('窗口列表格式无效，请重新勾选窗口') from error
    if not isinstance(items,list) or not 1<=len(items)<=100:raise ValueError('请勾选 1 至 100 个窗口')
    if any(not isinstance(item,dict) or not item.get('窗口标题') for item in items):raise ValueError('窗口信息不完整，请重新勾选')
    if len({str(item.get('窗口句柄')) for item in items})!=len(items):raise ValueError('窗口列表有重复项')
    return items


def resolve_target(item):
    gui,api,con,windows=native()
    try:
        current=windows.describe(int(item.get('窗口句柄','0')))
        keys=('窗口类名','进程路径','进程ID')
        if current['进程ID']!=os.getpid() and all(not item.get(key) or str(current[key]).casefold()==str(item[key]).casefold() for key in keys):
            return describe_window(int(current['窗口句柄']),windows,description=current)
    except (ValueError,RuntimeError,OSError,gui.error):pass
    return describe_window(int(windows.resolve(item)['窗口句柄']),windows)


def move_window(item, rectangle):
    gui,api,con,windows=native();current=resolve_target(item);hwnd=int(current['窗口句柄'])
    flags,show,minimum,maximum,normal=gui.GetWindowPlacement(hwnd)
    if gui.IsIconic(hwnd) or show==con.SW_SHOWMAXIMIZED:
        gui.SetWindowPlacement(hwnd,(flags,con.SW_SHOWNOACTIVATE,minimum,maximum,normal))
    x,y,width,height=map(int,rectangle)
    gui.SetWindowPos(hwnd,0,x,y,width,height,con.SWP_NOACTIVATE|con.SWP_NOZORDER|con.SWP_ASYNCWINDOWPOS)
    actual=gui.GetWindowRect(hwnd)
    for _ in range(40):
        if max(abs(a-b) for a,b in zip((x,y,x+width,y+height),actual))<=3:break
        time.sleep(.01);actual=gui.GetWindowRect(hwnd)
    return {'窗口标题':current['窗口标题'],'窗口句柄':str(hwnd),'目标位置':[x,y,width,height],
            '实际位置':[actual[0],actual[1],actual[2]-actual[0],actual[3]-actual[1]],
            '系统限制':any(abs(a-b)>3 for a,b in zip([x,y,width,height],[actual[0],actual[1],actual[2]-actual[0],actual[3]-actual[1]]))}


def apply_arrangement(parameters,context=None):
    selected=parse_targets(parameters.get('窗口列表','[]'))
    # Resolve all windows before moving any of them; a stale target cannot
    # silently turn a selected subset into a layout for arbitrary applications.
    targets=[resolve_target(item) for item in selected]
    if len({item['窗口句柄'] for item in targets})!=len(targets):raise RuntimeError('多个保存的窗口匹配到了同一窗口，请重新勾选')
    screen=choose_screen(parameters.get('屏幕','主屏幕'))
    rectangles=layout_rectangles(targets,screen['work'],parameters)
    if parameters.get('自动补位') and not all(item.get('进程路径') for item in targets):raise RuntimeError('无法读取所选程序的路径，不能安全启用自动补位')
    results=[]
    for index,(item,rectangle) in enumerate(zip(targets,rectangles)):
        if index and parameters.get('排布方式')=='堆叠':
            deadline=time.monotonic()+.1
            while time.monotonic()<deadline:
                if context is not None and context.stop_requested:return results
                time.sleep(min(.01,max(0,deadline-time.monotonic())))
        if context is not None and context.stop_requested:break
        results.append(move_window(item,rectangle))
    if len(results)==len(targets):
        if parameters.get('自动补位'):get_manager().start(targets,rectangles,parameters,context)
        else:get_manager().stop()
    return results


class ArrangementManager:
    def __init__(self):
        self._event=threading.Event();self._thread=None;self._lock=threading.RLock();self._status='自动补位未启动'
        self.targets=[];self.rectangles=[];self.families=set();self.ignored=set();self.parameters={};self.filled=0
    def status(self):
        with self._lock:return self._status
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()
    def stop(self):
        self._event.set()
        thread=self._thread
        if thread is not None and thread is not threading.current_thread():thread.join(timeout=2)
        if thread is not None and thread.is_alive():raise RuntimeError('正在等待窗口响应，稍后再停止自动补位')
        self._thread=None
        with self._lock:self._status='自动补位已停止'
    def start(self,targets,rectangles,parameters,context=None):
        self.stop()
        self.targets=[dict(item) for item in targets];self.rectangles=list(rectangles);self.parameters=dict(parameters)
        self.families={(item['进程路径'].casefold(),item['窗口类名']) for item in targets}
        handles={item['窗口句柄'] for item in targets}
        self.ignored={item['窗口句柄'] for item in list_windows()}-handles
        self.filled=0;self._event=threading.Event()
        with self._lock:self._status='自动补位运行中：'+str(len(targets))+' 个位置'
        self._thread=threading.Thread(target=self._watch,args=(context,),daemon=True,name='AnClickerWindowArrangement')
        self._thread.start()
    def _watch(self,context):
        while not self._event.wait(1):
            if context is not None and context.stop_requested:break
            try:self.tick()
            except Exception as error:
                with self._lock:self._status='自动补位暂停本轮：'+str(error)
        with self._lock:self._status='自动补位已停止'
    def tick(self):
        current=list_windows();by_handle={item['窗口句柄']:item for item in current}
        occupied=set();vacancies=[]
        for i,target in enumerate(self.targets):
            item=by_handle.get(target['窗口句柄']) if target else None
            if item and item['进程ID']==target['进程ID'] and item['窗口类名']==target['窗口类名']:
                occupied.add(item['窗口句柄'])
            else:vacancies.append(i);self.targets[i]=None
        candidates=[item for item in current if item['窗口句柄'] not in occupied|self.ignored and (item.get('进程路径','').casefold(),item['窗口类名']) in self.families]
        for index,(slot,item) in enumerate(zip(vacancies,candidates)):
            if index and self.parameters.get('排布方式')=='堆叠' and self._event.wait(.1):break
            if self._event.is_set():break
            rectangle=self.rectangles[slot]
            x,y,w,h=rectangle
            if int(self.parameters.get('排布版本',1))>=2 and self.parameters.get('排布方式') in ('对角线','水平层叠','垂直层叠','堆叠'):
                replacement=dict(self.parameters,起点X=x,起点Y=y)
                rectangle=layout_rectangles([item],(x,y,x+w,y+h),replacement)[0]
            elif self.parameters.get('保持比例'):
                rectangle=layout_rectangles([item],(x,y,x+w,y+h),{'排布方式':'堆叠','边距':0,'保持比例':True})[0]
            move_window(item,rectangle);self.targets[slot]=item;self.filled+=1
        with self._lock:self._status='自动补位运行中：'+str(len(self.targets))+' 个位置；已补位 '+str(self.filled)+' 次'


_manager=None
_manager_lock=threading.Lock()


def get_manager():
    global _manager
    with _manager_lock:
        if _manager is None:_manager=ArrangementManager()
        return _manager


def stop_auto_fill():
    if _manager is not None:_manager.stop()
