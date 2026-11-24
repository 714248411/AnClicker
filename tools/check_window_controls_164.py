"""Verify window settings and native Z order on an owned test window."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import win32gui,win32con

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.background_runtime import Windows
from anclicker.instructions.其他.窗口控制.executor import InstructionExecutor
from anclicker.domain.instructions import InstructionDraft, CommandRecord, ExecutionContext
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.web_anchor_editor import WebAnchorDialog
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.web_locators import parse_anchor_config


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    module=importlib.import_module('anclicker.ui.instruction_editors.其他.窗口控制')
    editor=module.InstructionEditor()
    assert editor.ui.titlePickerLayout.itemAt(editor.ui.titlePickerLayout.count()-1).widget() is editor.ui.pickWindowButton
    operations=editor._controls['操作']
    assert all(operations.findText(value)>=0 for value in ('置顶','置底'))
    picked={'窗口标题':'测试窗口','窗口句柄':'123','窗口类名':'test','进程ID':42}
    assert editor._apply_window_selection(picked)
    assert not editor._apply_window_selection(None)
    operations.setCurrentText('置顶');draft=editor.get_draft()
    assert draft.parameters['窗口定位']==picked
    editor.load_draft({'类型标识':'窗口控制','参数JSON':draft.parameters_json()})
    assert editor.get_draft().parameters['窗口定位']==picked
    editor._controls['标题包含'].setText('手动标题');editor._controls['标题包含'].textEdited.emit('手动标题')
    assert '窗口定位' not in editor.get_draft().parameters
    editor.show();app.processEvents()
    proof=Path(__file__).resolve().parents[1]/'artifacts/validation/window-controls-164.png'
    editor.grab().save(str(proof));editor.close()
    print('PASS first-row picker, new operations, selection/cancel, JSON draft roundtrip, manual title reset',flush=True)
    picks=iter([{'css':'input[name="amount"]','anchorSelector':'input[name="amount"]','tag':'INPUT'},
                {'css':'#label','text':'数量','tag':'LABEL'}])
    previews=[]
    wizard=WebAnchorDialog({'selector':'input','anchor':'#old','anchorRel':'右侧'},lambda:next(picks),lambda p:previews.append(p) or {'reason':'成功','count':1,'anchors':[{'count':1}]})
    wizard._pick_target();wizard._pick_anchor()
    params=wizard.parameters();conf=parse_anchor_config(params['anchor'])
    assert params['selector']=='input[name="amount"]' and len(conf['anchors'])==2
    assert conf['anchors'][1]['selector']=='数量'
    wizard._preview();assert len(previews)==1 and '目标候选 1' in wizard.status.text()
    wizard.table.selectRow(0);wizard._remove();assert wizard.table.rowCount()==1
    wizard.show();app.processEvents();wizard.grab().save(str(proof.with_name('web-anchor-dialog-164.png')));wizard.close()
    click_editor=get_instruction_spec('点击元素').create_editor()
    assert click_editor.anchor_wizard.text()=='锚点向导'
    assert click_editor.locator_preview.text()=='预览定位'
    click_editor.close()
    print('PASS anchor wizard add/pick/remove, legacy roundtrip, preview and instruction editor integration',flush=True)
    helper=r'''
from PySide2.QtWidgets import QApplication,QWidget
app=QApplication([]);window=QWidget();window.setWindowTitle('AnClicker 1.6.4 Z Order Test')
window.setGeometry(120,120,340,200);window.show();app.processEvents()
peer=QWidget();peer.setWindowTitle('AnClicker Z Order Peer');peer.setGeometry(500,120,200,150);peer.show();app.processEvents()
print(str(int(window.winId()))+','+str(int(peer.winId())),flush=True)
app.exec_()
'''
    process=subprocess.Popen([sys.executable,'-u','-c',helper],stdout=subprocess.PIPE,text=True)
    try:
        hwnd,peer=map(int,process.stdout.readline().strip().split(','))
        identity=Windows().describe(hwnd)
        rectangle=win32gui.GetWindowRect(hwnd)
        context=ExecutionContext()
        executor=InstructionExecutor()
        for operation,topmost in [('置顶',True),('置底',False)]:
            command=CommandRecord(None,'窗口控制',{'标题包含':identity['窗口标题'],'窗口定位':identity,'操作':operation,'报错':True})
            assert executor.execute_once(context,command)
            for _ in range(50):
                if bool(win32gui.GetWindowLong(hwnd,win32con.GWL_EXSTYLE)&win32con.WS_EX_TOPMOST)==topmost:break
                time.sleep(.02)
            assert bool(win32gui.GetWindowLong(hwnd,win32con.GWL_EXSTYLE)&win32con.WS_EX_TOPMOST)==topmost, (operation, win32gui.GetWindowLong(hwnd,win32con.GWL_EXSTYLE))
            assert win32gui.GetWindowRect(hwnd)==rectangle
        z_order=[]
        win32gui.EnumWindows(lambda handle,_:z_order.append(handle),None)
        assert z_order.index(hwnd)>z_order.index(peer),'test window was not sent below the peer window'
        print('PASS real Windows picked identity, topmost/bottom native ordering and unchanged geometry',flush=True)
    finally:
        process.terminate();process.wait(timeout=10)
    print('PASS window and anchor settings regression',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
