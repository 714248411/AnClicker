"""Regression for paced stacking and explicit multi-window web locators."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform import window_arrangement as arrangement
from anclicker.platform.rpa_bridge import RpaBridge
from anclicker.domain.instructions import InstructionDraft
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.instruction_editors.网页自动化.点击元素 import InstructionEditor
from anclicker.ui.web_anchor_editor import WebAnchorDialog


def main():
    targets=[{'窗口标题':str(i),'窗口句柄':str(i)} for i in range(3)]
    moments=[]
    with patch.object(arrangement,'resolve_target',side_effect=lambda item:item),patch.object(arrangement,'choose_screen',return_value={'work':(0,0,1000,800)}),patch.object(arrangement,'move_window',side_effect=lambda *args:moments.append(time.monotonic())),patch.object(arrangement,'get_manager',return_value=MagicMock()):
        arrangement.apply_arrangement({'窗口列表':targets,'排布方式':'堆叠'})
        assert all(b-a>=.099 for a,b in zip(moments,moments[1:])),moments
        moments.clear()
        arrangement.apply_arrangement({'窗口列表':targets,'排布方式':'平铺'})
        assert moments[-1]-moments[0]<.09,moments
    stopped=SimpleNamespace(stop_requested=False)
    def cancel_move(*args):
        stopped.stop_requested=True
        return {'stopped':True}
    with patch.object(arrangement,'resolve_target',side_effect=lambda item:item),patch.object(arrangement,'choose_screen',return_value={'work':(0,0,1000,800)}),patch.object(arrangement,'move_window',side_effect=cancel_move):
        assert len(arrangement.apply_arrangement({'窗口列表':targets,'排布方式':'堆叠'},stopped))==1
    print('PASS stack wait honors stop requests',flush=True)
    print('PASS stack intervals >= 0.1s; tiled operations remain unpaced',flush=True)
    app=QApplication.instance() or QApplication([])
    chosen={'id':1,'url':'http://example.test','title':'测试','engine':'内置'}
    editor=InstructionEditor(draft=InstructionDraft(type_id='点击元素',parameters={'selector':'#field','browserWindow':chosen}))
    assert editor.web_window.selection()==chosen
    assert editor.get_draft().parameters['browserWindow']==chosen
    dialog=WebAnchorDialog(editor._locator_parameters(),lambda target: {'css':'#field','tag':'INPUT'},lambda p:None,editor,list_windows=lambda:[chosen])
    dialog.window_selector.refresh();dialog._pick_target();dialog.add_anchor({'selector':'名称','by':'文本内容','relation':'右侧'})
    assert dialog.parameters()['browserWindow']==chosen
    assert dialog.target.text()=='#field'
    dialog.close();editor.close()
    print('PASS editor save/reopen and anchor wizard retain selected window',flush=True)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=('<meta charset="utf-8"><title>'+self.path+'</title><label>名称</label><input id="field">').encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
        def log_message(self,*_):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    bridge=RpaBridge('web-windows-check')
    previous=os.environ.get('ANCLICKER_DATA_DIR')
    try:
        with tempfile.TemporaryDirectory(prefix='anclicker-windows-',ignore_cleanup_errors=True) as folder:
            os.environ['ANCLICKER_DATA_DIR']=folder
            def run(kind,params=None):return bridge.execute({'id':kind,'params':params or {}},timeout=45)
            for name in ('one','two'):
                run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}/'+name,'target':'新窗口','waitType':'加载完成'})
            pages=run('acListBrowserWindows')['result'];assert len(pages)==2,pages
            one,two=pages
            run('input',{'selector':'#field','by':'CSS选择器','text':'first','browserWindow':one})
            run('input',{'selector':'#field','by':'锚点定位','anchor':'text=名称','anchorRel':'右侧','text':'second','browserWindow':two})
            for page,expected in ((one,'first'),(two,'second')):
                result=run('getText',{'selector':'#field','by':'CSS选择器','varName':'value','browserWindow':page})
                assert result['variables']['value']==expected,result
                assert run('acPreviewLocator',{'selector':'#field','by':'锚点定位','anchor':'text=名称','anchorRel':'右侧','browserWindow':page})['result']['found']
            old_address=dict(one,url='http://old-address.invalid')
            assert run('getText',{'selector':'#field','by':'CSS选择器','varName':'value','browserWindow':old_address})['variables']['value']=='first'
            print('PASS live window identity survives page address changes',flush=True)
            print('PASS two real browser windows: selected CSS/anchor input, independent values and previews',flush=True)
            missing=dict(one,id='closed',url='http://127.0.0.1/missing')
            try:run('input',{'selector':'#field','text':'wrong','browserWindow':missing})
            except RuntimeError as error:assert '关闭' in str(error),error
            else:raise AssertionError('missing window silently used the active window')
            print('PASS unavailable window refuses operation',flush=True)
    finally:
        bridge.close();server.shutdown();server.server_close()
        if previous is None:os.environ.pop('ANCLICKER_DATA_DIR',None)
        else:os.environ['ANCLICKER_DATA_DIR']=previous
    return 0


if __name__=='__main__':raise SystemExit(main())
