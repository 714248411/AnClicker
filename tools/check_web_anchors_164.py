"""Exercise anchor lookup through AnClicker's real isolated browser engine."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.rpa_bridge import RpaBridge
from anclicker.domain.web_locators import parse_anchor_config, encode_anchor_config

HTML = '''<!doctype html><meta charset="utf-8"><title>锚点定位回归</title>
<style>body{margin:0;font:16px sans-serif}label,input,button{position:absolute;box-sizing:border-box;height:28px}label{width:90px}input{width:95px}#audit{position:absolute;top:670px;left:20px}iframe{position:absolute;top:740px;left:20px;width:420px;height:100px}</style>
<label style="left:20px;top:100px" id="row-a">产品甲</label><label style="left:20px;top:180px" id="row-b">产品乙</label>
<label style="left:200px;top:40px" id="price">价格</label><label style="left:400px;top:40px" id="quantity">数量</label>
<input id="ap" style="left:200px;top:100px"><input id="aq" style="left:400px;top:100px">
<input id="bp" style="left:200px;top:180px"><input id="bq" style="left:400px;top:180px">
<input class="hidden" style="display:none;left:400px;top:180px">
<label id="middle" style="left:300px;top:350px;width:20px">中心</label>
<input id="same-left" class="same" style="left:200px;top:350px;width:40px"><input id="same-right" class="same" style="left:380px;top:350px;width:40px">
<label data-key="a;b" style="left:580px;top:100px">分号</label><input class="semi" style="left:700px;top:100px">
<label style="left:580px;top:180px">O'Reilly\\路径</label><input class="quoted" style="left:700px;top:180px">
<div id="shadow-host" style="position:absolute;left:20px;top:500px"></div>
<button id="mutate" style="top:620px;left:20px" onclick="document.body.prepend(document.querySelector('#bq'));document.querySelector('#row-b').style.top='260px';document.querySelector('#bp').style.top='260px';document.querySelector('#bq').style.top='260px'">改变布局</button>
<div id="audit">0</div><iframe src="/frame"></iframe>
<script>document.addEventListener('input',()=>{document.querySelector('#audit').textContent=String(Number(document.querySelector('#audit').textContent)+1)});
const sr=document.querySelector('#shadow-host').attachShadow({mode:'open'});sr.innerHTML='<style>label{display:inline-block;width:90px;height:28px}input{width:100px;height:28px}</style><label>影子名称</label><input class="shadow">';</script>'''
FRAME='''<!doctype html><meta charset="utf-8"><style>label{position:absolute;left:10px;top:15px;width:90px;height:25px}input{position:absolute;left:120px;top:15px;width:100px;height:25px}</style><label>框架名称</label><input id="frame-input">'''


def config(rules,**extras):
    return json.dumps({'anchors':rules,**extras},ensure_ascii=False)


def rule(selector,relation='右侧',by='文本内容'):
    return {'selector':selector,'relation':relation,'by':by}


def main():
    legacy=parse_anchor_config('[data-key="a;b"]; #second')
    assert len(legacy['anchors'])==2
    assert parse_anchor_config(encode_anchor_config(legacy))==legacy
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=(FRAME if self.path.startswith('/frame') else HTML).encode('utf-8')
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
        def log_message(self,*_):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    bridge=RpaBridge('web-anchor-check-164')
    previous=os.environ.get('ANCLICKER_DATA_DIR')
    try:
        with tempfile.TemporaryDirectory(prefix='anclicker-anchors-',ignore_cleanup_errors=True) as folder:
            os.environ['ANCLICKER_DATA_DIR']=folder
            def run(kind,params=None):return bridge.execute({'id':kind,'params':params or {}},timeout=60)
            def preview(selector,anchor,relation='右侧'):
                return run('acPreviewLocator',{'selector':selector,'by':'锚点定位','anchor':anchor,'anchorRel':relation})['result']
            def read(selector):return run('getText',{'selector':selector,'by':'CSS选择器','varName':'read'})['variables']['read']
            run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}','target':'新窗口','loginMode':'独立登录(每次全新)','waitType':'加载完成'})
            both=config([rule('产品乙'),rule('数量','下方')])
            result=preview('input',both)
            assert result['found'] and result['count']==1,result
            assert result['target']['rect']['x']==400,result
            assert read('#audit')=='0','preview performed an input action'
            run('input',{'selector':'input','by':'锚点定位','anchor':both,'text':'42'})
            assert read('#bq')=='42'
            assert read('#audit')=='1'
            print('PASS multiple anchors jointly choose the correct repeated input; preview has no side effects',flush=True)
            missing=preview('input',config([rule('产品乙'),rule('不存在的锚点','下方')]))
            assert not missing['found'] and missing['anchors'][1]['count']==0,missing
            ambiguous=config([rule('#middle','最近','CSS选择器')])
            report=preview('.same',ambiguous)
            assert not report['found'] and report['count']==2,report
            try:run('input',{'selector':'.same','by':'锚点定位','anchor':ambiguous,'text':'must not write'})
            except RuntimeError as error:assert '多个目标' in str(error),error
            else:raise AssertionError('ambiguous lookup silently selected a target')
            explicit=config([rule('#middle','最近','CSS选择器')],matchIndex=2)
            run('input',{'selector':'.same','by':'锚点定位','anchor':explicit,'text':'second'})
            assert read('#same-right')=='second'
            print('PASS missing second anchor, equal candidates refused, explicit visual index',flush=True)
            assert preview('.semi','[data-key="a;b"]')['found']
            quoted=config([rule("O'Reilly\\路径")])
            assert preview('.quoted',quoted)['found']
            assert preview('input.shadow',config([rule('影子名称')]))['found']
            assert preview('#frame-input',config([rule('框架名称')]))['found']
            assert not preview('#frame-input',config([rule('产品乙')]))['found']
            assert preview('#bp','#row-b')['found']
            xpath=config([rule('//*[@id="row-b"]','右侧','XPath'),rule('//*[@id="price"]','下方','XPath')])
            assert preview('#bp',xpath)['found']
            print('PASS legacy CSS and XPath, quoted selectors, shadow DOM, iframe, same-frame constraints',flush=True)
            run('click',{'selector':'#mutate','by':'CSS选择器'})
            changed=preview('input',both)
            assert changed['found'] and changed['target']['rect']['x']==400,changed
            run('input',{'selector':'input','by':'锚点定位','anchor':both,'text':'after layout change'})
            assert read('#bq')=='after layout change'
            print('PASS DOM reorder and layout changes recompute anchors before execution',flush=True)
            assert not preview('input',config([rule('产品乙'),rule('数量','下方')],maxDistance=10))['found']
            proof=Path(__file__).resolve().parents[1]/'artifacts/validation/web-anchors-164.png'
            preview('input',both)
            run('screenshot',{'selector':'','path':str(proof)})
            print('PASS distance limit and preview screenshot',flush=True)
            bridge.close()
    finally:
        bridge.close();server.shutdown();server.server_close()
        if previous is None:os.environ.pop('ANCLICKER_DATA_DIR',None)
        else:os.environ['ANCLICKER_DATA_DIR']=previous
    print('PASS AnClicker real-browser anchor regression',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
