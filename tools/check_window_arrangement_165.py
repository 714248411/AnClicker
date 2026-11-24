"""Regression: native Z order, six layouts, saved selection and auto-fill."""
import json
from pathlib import Path
import subprocess
import sys
import time
import win32gui
import win32con
from unittest.mock import patch

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import CommandRecord,ExecutionContext
from anclicker.domain.window_arrangement import LAYOUT_MODES,layout_rectangles
from anclicker.platform.window_zorder import set_window_zorder
from anclicker.platform.window_arrangement import describe_window,list_windows,list_screens,apply_arrangement,get_manager,stop_auto_fill
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
from anclicker.instructions.registry import get_instruction_spec


def helper():
    configure_application();app=QApplication([]);app.setQuitOnLastWindowClosed(False)
    windows=[]
    def create(title):
        window=QWidget();window.setWindowTitle(title);window.setMinimumSize(80,60);window.setGeometry(120+len(windows)*30,120,340,240);window.show();windows.append(window);app.processEvents();return int(window.winId())
    handles=[create('AC165 Layout '+str(i)) for i in range(4)]
    wc=win32gui.WNDCLASS();wc.lpszClassName='AC165InactiveNative';wc.lpfnWndProc=win32gui.DefWindowProc;win32gui.RegisterClass(wc)
    native=win32gui.CreateWindow(wc.lpszClassName,'AC165 Inactive Native',win32con.WS_OVERLAPPEDWINDOW,150,150,340,240,0,0,0,None);win32gui.ShowWindow(native,win32con.SW_SHOWNOACTIVATE)
    print(json.dumps({'handles':handles,'native':native}),flush=True)
    # A timer on the helper GUI thread processes a simple file mailbox; it
    # avoids mixing Qt window creation with a network/background thread.
    from_queue=Path(sys.argv[2]);last=''
    def poll():
        nonlocal last
        if not from_queue.exists():return
        text=from_queue.read_text(encoding='utf-8')
        if not text or text==last:return
        last=text;request=json.loads(text)
        if request['action']=='close':windows[request['index']].close();app.processEvents();response=True
        elif request['action']=='create':response=create(request['title'])
        else:response=False
        print(json.dumps(response),flush=True)
    timer=__import__('anclicker.platform.qt_compat.QtCore',fromlist=['QTimer']).QTimer();timer.timeout.connect(poll);timer.start(30)
    app.exec()


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    windows=[{'rect':[0,0,600,400],'client_size':[584,360]} for _ in range(6)]
    for mode in LAYOUT_MODES:
        boxes=layout_rectangles(windows,(-1920,-300,0,780),{'排布方式':mode,'行数':2,'列数':3,'边距':8,'间距':8})
        assert len(boxes)==6
        assert all(x>=-1912 and y>=-292 and x+w<=-8 and y+h<=772 and min(w,h)>0 for x,y,w,h in boxes),(mode,boxes)
    row=layout_rectangles(windows,(0,0,1920,1080),{'排布方式':'网格','行数':2,'列数':3})
    col=layout_rectangles(windows,(0,0,1920,1080),{'排布方式':'网格','行数':2,'列数':3,'排布方向':'纵向优先'})
    assert row[1][1]==row[0][1] and col[1][0]==col[0][0]
    ratio=layout_rectangles(windows[:1],(0,0,500,500),{'排布方式':'堆叠','保持比例':True})[0]
    assert abs((ratio[2]-16)/(ratio[3]-40)-584/360)<.01
    try:layout_rectangles(windows,(0,0,1000,800),{'排布方式':'网格','行数':1,'列数':1})
    except ValueError:pass
    else:raise AssertionError('grid overflow not rejected')
    print('PASS six layout geometries, negative screen origins, direction, client aspect ratio and overflow',flush=True)
    mailbox=Path('artifacts/validation/layout-helper-request.json').resolve();mailbox.unlink(missing_ok=True)
    process=subprocess.Popen([sys.executable,'-u',__file__,'--helper',str(mailbox)],stdout=subprocess.PIPE,text=True,encoding='utf-8')
    try:
        data=json.loads(process.stdout.readline());handles=data['handles'];native=data['native'];sequence=0
        def command(action,**extra):
            nonlocal sequence
            sequence+=1;temporary=mailbox.with_suffix('.tmp');temporary.write_text(json.dumps({'action':action,'seq':sequence,**extra}),encoding='utf-8');temporary.replace(mailbox)
            return json.loads(process.stdout.readline())
        rectangle=win32gui.GetWindowRect(native)
        # Inactive native windows reproduced the previous false-success path.
        set_window_zorder(native,'置顶');assert win32gui.GetWindowLong(native,-20)&8
        assert win32gui.GetWindowRect(native)==rectangle
        set_window_zorder(native,'置底');assert not win32gui.GetWindowLong(native,-20)&8
        win32gui.ShowWindow(handles[0],win32con.SW_MINIMIZE);set_window_zorder(handles[0],'置顶');assert not win32gui.IsIconic(handles[0]);assert win32gui.GetWindowLong(handles[0],-20)&8;set_window_zorder(handles[0],'置底')
        print('PASS inactive native window and minimized Qt window verified topmost/bottom',flush=True)
        selected=[describe_window(hwnd) for hwnd in handles[:3]]
        base={'窗口列表':json.dumps(selected,ensure_ascii=False),'屏幕':'主屏幕','行数':2,'列数':2,'边距':16,'间距':10}
        untouched=win32gui.GetWindowRect(handles[3])
        for mode in LAYOUT_MODES:
            results=apply_arrangement({**base,'排布方式':mode})
            assert len(results)==3 and not any(item['系统限制'] for item in results),(mode,results)
        custom=apply_arrangement({**base,'排布方式':'网格','窗口大小':'自定义','宽度':320,'高度':220})
        assert all(result['实际位置'][2:]==[320,220] for result in custom)
        assert win32gui.GetWindowRect(handles[3])==untouched
        # Resolve every target first; no partial movement on a stale selection.
        invalid=[*selected,{'窗口句柄':'0','窗口标题':'AC165 nonexistent','窗口类名':'missing'}]
        before=win32gui.GetWindowRect(handles[0])
        try:apply_arrangement({**base,'窗口列表':json.dumps(invalid)})
        except RuntimeError:pass
        else:raise AssertionError('stale target was silently accepted')
        assert win32gui.GetWindowRect(handles[0])==before
        print('PASS native six layouts, custom dimensions, unselected window preserved and stale target atomic validation',flush=True)
        editor=get_instruction_spec('窗口排布').create_editor()
        editor.load_draft({'type_id':'窗口排布','parameters':{**base,'排布方式':'网格'}})
        assert len(editor._checked())==3
        editor.ui.searchEdit.setText('Layout 0');editor._select_visible(False);assert len(editor._checked())==2
        editor.ui.searchEdit.clear();editor._select_visible(True)
        # Select only the isolated helper windows for the screenshot/draft.
        for index in range(editor.ui.windowTree.topLevelItemCount()):
            item=editor.ui.windowTree.topLevelItem(index);item.setCheckState(0,Qt.Checked if item.data(0,Qt.UserRole)['窗口句柄'] in {str(h) for h in handles[:3]} else Qt.Unchecked)
        draft=editor.get_draft();assert len(json.loads(draft.parameters['窗口列表']))==3
        editor.load_draft(draft);assert len(editor._checked())==3
        editor._auto_grid();editor.show();app.processEvents();editor.grab().save('artifacts/validation/window-arrangement-ui.png');editor.close()
        print('PASS keyword filtering preserves hidden checks, saved selection roundtrip, monitor identity and preview',flush=True)
        watched=[describe_window(hwnd) for hwnd in handles[:2]]
        active={**base,'窗口列表':json.dumps(watched),'排布方式':'网格','行数':1,'列数':2,'自动补位':True}
        results=apply_arrangement(active);slot=results[0]['目标位置'];manager=get_manager()
        command('close',index=0);new_handle=command('create',title='AC165 Layout Replacement')
        deadline=time.monotonic()+5
        while manager.filled==0 and time.monotonic()<deadline:app.processEvents();time.sleep(.05)
        assert manager.filled==1,manager.status()
        actual=win32gui.GetWindowRect(new_handle)
        assert [actual[0],actual[1],actual[2]-actual[0],actual[3]-actual[1]]==slot
        assert win32gui.GetWindowRect(handles[3])==untouched
        stop_auto_fill();assert not manager._thread
        print('PASS automatic replacement fills a vacancy, preserves initially unselected windows, stops cleanly',flush=True)
    finally:
        try:stop_auto_fill()
        finally:process.terminate();process.wait(timeout=10);mailbox.unlink(missing_ok=True)
    print('PASS window arrangement regression',flush=True)
    return 0

if __name__=='__main__':
    if '--helper' in sys.argv:helper()
    else:raise SystemExit(main())
