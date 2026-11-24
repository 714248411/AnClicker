"""Mode-specific settings, exact coordinates and Qt 5 hidden-row regression."""
import json
from pathlib import Path
import subprocess
import sys
import time
import win32gui
from unittest.mock import patch

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.window_arrangement import layout_rectangles,LAYOUT_MODES,MODE_ROWS
from anclicker.platform.window_arrangement import describe_window,list_windows,native,apply_arrangement,get_manager,stop_auto_fill
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QApplication,QAbstractSpinBox,QLineEdit
from anclicker.instructions.registry import get_instruction_spec
from tools.check_window_arrangement_165 import helper


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    area=(-1200,-200,0,600)
    windows=[{'rect':[0,0,300+i*20,200+i*10],'client_size':[284+i*20,160+i*10]} for i in range(3)]
    base={'排布版本':2,'起点X':-1000,'起点Y':-100,'X间距':35,'Y间距':-20,'对角间距':24,'行数':1,'列数':3,'边距':0,'间距':0}
    ignored={**base,'排布方式':'堆叠','窗口大小':'自定义','宽度':50,'高度':50,'保持比例':True,'行数':0,'边距':999,'间距':999}
    result=layout_rectangles(windows,area,ignored)
    assert result==[(-1000+i*35,-100-i*20,300+i*20,200+i*10) for i in range(3)]
    assert layout_rectangles(windows,area,{**ignored,'X间距':0,'Y间距':0})[2][:2]==(-1000,-100)
    for mode,dx,dy in [('对角线',24,24),('水平层叠',35,0),('垂直层叠',0,-20)]:
        result=layout_rectangles(windows,area,{**base,'排布方式':mode})
        assert result==[(-1000+i*dx,-100+i*dy,300+i*20,200+i*10) for i in range(3)],(mode,result)
    tiled=layout_rectangles(windows,area,{**base,'排布方式':'平铺','窗口大小':'自定义','宽度':50,'高度':50})
    assert tiled==[(-1200+i*400,-200,400,800) for i in range(3)]
    rows=layout_rectangles(windows,area,{**base,'排布方式':'平铺','行数':3,'列数':1})
    assert rows[0][2:]==(1200,266) and rows[1][1]==66,rows
    grid=layout_rectangles(windows,area,{**base,'排布方式':'网格','窗口大小':'自定义','宽度':200,'高度':120})
    assert grid[0]==(-1100,140,200,120),grid
    minimized=[{'rect':[-32000,-32000,-31840,-31972],'minimized':True,'normal_rect':[10,20,510,320]}]
    assert layout_rectangles(minimized,area,{**base,'排布方式':'堆叠'})[0][2:]==(500,300)
    print('PASS v2 independent tile rows/columns, exact stack coordinates/offsets, signed steps, hidden settings ignored, minimized original size',flush=True)
    mailbox=Path('artifacts/validation/layout-166-helper-request.json').resolve();mailbox.unlink(missing_ok=True)
    process=subprocess.Popen([sys.executable,'-u',__file__,'--helper',str(mailbox)],stdout=subprocess.PIPE,text=True,encoding='utf-8')
    try:
        handles=json.loads(process.stdout.readline())['handles'];seq=0
        def command(action,**extra):
            nonlocal seq
            seq+=1;temporary=mailbox.with_suffix('.tmp');temporary.write_text(json.dumps({'action':action,'seq':seq,**extra}),encoding='utf-8');temporary.replace(mailbox)
            return json.loads(process.stdout.readline())
        backend_type=type(native()[3]); original=backend_type.describe; calls=[]
        def counted(backend,hwnd):
            calls.append(hwnd);return original(backend,hwnd)
        with patch.object(backend_type,'describe',counted):
            snapshot=list_windows()
        assert snapshot and len(calls)==len(set(calls)),calls
        print('PASS window scan reads process identity once per window; no stale cross-scan cache',flush=True)
        selected=[describe_window(hwnd) for hwnd in handles[:3]]
        params={'排布版本':2,'窗口列表':json.dumps(selected),'屏幕':'主屏幕','行数':1,'列数':3,'起点X':100,'起点Y':90,'X间距':45,'Y间距':30,'对角间距':40,'边距':8,'间距':8}
        for mode in LAYOUT_MODES:
            before=[describe_window(hwnd) for hwnd in handles[:3]]
            p={**params,'排布方式':mode}
            results=apply_arrangement(p)
            assert not any(item['系统限制'] for item in results),(mode,results)
            if mode not in ('平铺','网格'):
                for i,item in enumerate(results):
                    expected_dx=40 if mode=='对角线' else 45 if mode in ('堆叠','水平层叠') else 0
                    expected_dy=40 if mode=='对角线' else 30 if mode in ('堆叠','垂直层叠') else 0
                    assert item['实际位置'][:2]==[100+i*expected_dx,90+i*expected_dy]
                    old=before[i]['rect'];assert item['实际位置'][2:]==[old[2]-old[0],old[3]-old[1]]
        print('PASS six native v2 layouts match their own controls and preserve positioned-window sizes',flush=True)
        selected=[describe_window(hwnd) for hwnd in handles[:3]];params['窗口列表']=json.dumps(selected)
        editor=get_instruction_spec('窗口排布').create_editor(draft={'type_id':'窗口排布','parameters':params})
        editor.show();app.processEvents();editor.resize(900,650);app.processEvents()
        for mode in (*LAYOUT_MODES,'堆叠','平铺'):
            editor._controls['排布方式'].setCurrentText(mode);app.processEvents()
            active={key for key,row in editor.ui.modeRowWidgets.items() if not row.isHidden()}
            expected=set(MODE_ROWS[mode])|{'screen','mode','hint','auto_fill'}
            expected.discard('custom_size')
            if mode in ('对角线','水平层叠','垂直层叠'):expected.discard('aspect')
            assert active==expected,(mode,active,expected)
            # Hidden Qt 5 form rows previously left blank strips between fields.
            visible=[row for row in editor.ui.modeRowWidgets.values() if not row.isHidden()]
            for first,second in zip(visible,visible[1:]):
                gap=second.y()-(first.y()+first.height())
                assert 0<=gap<=12,(mode,gap)
            for spin in editor.findChildren(QAbstractSpinBox):
                if not spin.isVisible():continue
                line=spin.findChild(QLineEdit);assert line.height()>=line.fontMetrics().height(),(mode,spin.objectName())
            assert editor.ui.applyButton.isVisible() and editor.ui.buttonBox.isVisible()
            if mode=='堆叠':
                assert editor.preview.isHidden(),'small window should prioritize settings'
                viewport=editor.ui.settingsScroll.viewport()
                for key in ('起点X','起点Y','X间距','Y间距'):
                    control=editor._controls[key];point=control.mapTo(viewport,control.rect().bottomRight())
                    assert 0<=point.x()<viewport.width() and 0<=point.y()<viewport.height(),(key,point,viewport.size())
            editor.grab().save('artifacts/validation/layout-166-'+mode+'.png')
        editor.ui.previewTitle.click();app.processEvents();assert not editor.preview.isHidden()
        editor.ui.previewTitle.click();app.processEvents();assert editor.preview.isHidden()
        editor._controls['排布方式'].setCurrentText('堆叠');editor._controls['起点X'].setValue(-330);editor._controls['X间距'].setValue(-17)
        draft=editor.get_draft();assert draft.parameters['排布版本']==2
        editor.load_draft(draft);assert editor._controls['起点X'].value()==-330 and editor._controls['X间距'].value()==-17
        assert editor.preview.rectangles[1][0]==-347
        editor.close()
        print('PASS mode-specific rows collapse cleanly at 900x650, visible digits/buttons, negative coordinate draft/preview roundtrip',flush=True)
        watched=[describe_window(hwnd) for hwnd in handles[:2]]
        active={**params,'排布方式':'堆叠','窗口列表':json.dumps(watched),'自动补位':True,'保持比例':True,'窗口大小':'自定义','宽度':50,'高度':50}
        results=apply_arrangement(active);slot=results[0]['目标位置'];manager=get_manager()
        command('close',index=0);new_handle=command('create',title='AC166 Mode Replacement')
        deadline=time.monotonic()+5
        while manager.filled==0 and time.monotonic()<deadline:app.processEvents();time.sleep(.03)
        assert manager.filled==1,manager.status()
        actual=win32gui.GetWindowRect(new_handle)
        assert [actual[0],actual[1]]==slot[:2]
        assert actual[2]-actual[0]!=50 and actual[3]-actual[1]!=50
        stop_auto_fill()
        print('PASS stack auto-fill uses the slot origin and replacement original size, ignoring hidden custom-size/aspect settings',flush=True)
    finally:
        try:stop_auto_fill()
        finally:process.terminate();process.wait(timeout=10);mailbox.unlink(missing_ok=True)
    print('PASS mode settings and display regression',flush=True)
    return 0

if __name__=='__main__':
    if '--helper' in sys.argv:helper()
    else:raise SystemExit(main())
