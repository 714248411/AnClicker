"""Controlled 32/64-bit integration checks; never targets existing user windows."""
import json,os,sys,time,subprocess,tempfile,traceback
from pathlib import Path
from unittest.mock import patch

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'ExecutionContext_InstructionDraft': ('from', 'anclicker.domain.instructions', ('ExecutionContext', 'InstructionDraft'), 0),
    'get_instruction_spec': ('from', 'anclicker.instructions.registry', ('get_instruction_spec',), 0),
    'background_runtime_DmTransport_etc': ('from', 'anclicker.platform.background_runtime', ('DmTransport', 'Windows', 'bind_background', 'current_backend', 'close_background', 'execute_background_method'), 0),
    'METHODS_label': ('from', 'anclicker.platform.background_catalog', ('METHODS', 'label'), 0),
    'DatabaseOperation': ('from', 'anclicker.storage.database', ('DatabaseOperation',), 0),
    'GraphRepository': ('from', 'anclicker.storage.graph_repository', ('GraphRepository',), 0),
    'CommandThread': ('from', 'anclicker.app.main_work', ('CommandThread',), 0),
    'win32gui': ('import', 'win32gui', (), False),
    'win32con': ('import', 'win32con', (), False),
    'win32process': ('import', 'win32process', (), False),
    'BackgroundWindowPicker': ('from', 'anclicker.ui.background_window_picker', ('BackgroundWindowPicker',), 0),
    'QTest': ('from', 'anclicker.platform.qt_compat.QtTest', ('QTest',), 0),
    'Qt_QPoint': ('from', 'anclicker.platform.qt_compat.QtCore', ('Qt', 'QPoint'), 0),
    'QDialog': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog',), 0),
    'base64': ('import', 'base64', (), False),
})

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
os.environ['QT_QPA_PLATFORM']='windows';os.environ['ANCLICKER_DATA_DIR']=str(root/'artifacts/validation/background-native-data')
QApplication = _module_imports.load('QApplication')
app=QApplication.instance() or QApplication([])
ExecutionContext, InstructionDraft = _module_imports.load('ExecutionContext_InstructionDraft')
get_instruction_spec = _module_imports.load('get_instruction_spec')
DmTransport, Windows, bind_background, current_backend, close_background, execute_background_method = _module_imports.load('background_runtime_DmTransport_etc')
METHODS, label = _module_imports.load('METHODS_label')
DatabaseOperation = _module_imports.load('DatabaseOperation')
GraphRepository = _module_imports.load('GraphRepository')
CommandThread = _module_imports.load('CommandThread')
win32gui = _module_imports.load('win32gui'); win32con = _module_imports.load('win32con'); win32process = _module_imports.load('win32process')
class TracedTransport(DmTransport):
    def call(self, name, *args, **kwargs):
        before=win32gui.GetCursorPos()
        result=super().call(name,*args,**kwargs)
        after=win32gui.GetCursorPos()
        if name in ('MoveTo','LeftClick','KeyDown','KeyUp','SendString'):
            report[str(bits)].setdefault('input_observations',[]).append({'method':name,'before':before,'after':after})
        return result

report={};destination=root/'artifacts/validation/background-native-results.json'

def check(result,message):
    if not result:raise AssertionError(message)

def method(context,name,values=None):
    result=execute_background_method(context,METHODS[name]['group'],{'接口':label(name),'参数':json.dumps(values or {}),'变量':'result'})
    report[str(bits)]['methods'][name]=result
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return result

for bits in (32,64):
    entry=report[str(bits)]={'methods':{},'passed':False}
    context=None;process=None;state=None
    try:
        folder=root/'artifacts/validation'/('background-fixture-'+str(bits));folder.mkdir(exist_ok=True)
        state_path=folder/'state.json';state_path.unlink(missing_ok=True)
        shell=Path(os.environ['WINDIR'])/('SysWOW64' if bits==32 else 'System32')/'WindowsPowerShell/v1.0/powershell.exe'
        process=subprocess.Popen([str(shell),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'artifacts/validation/dm-fixture.ps1'),str(state_path)],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        deadline=time.monotonic()+12
        while not state_path.exists() and time.monotonic()<deadline and process.poll() is None:time.sleep(.05)
        if not state_path.exists():raise RuntimeError('test target did not start: '+process.stderr.read().decode(errors='replace'))
        state=json.loads(state_path.read_text(encoding='utf8'));check(state['bits']==bits,'fixture bitness')
        BackgroundWindowPicker = _module_imports.load('BackgroundWindowPicker')
        QTest = _module_imports.load('QTest')
        Qt, QPoint = _module_imports.load('Qt_QPoint')
        QDialog = _module_imports.load('QDialog')
        win32gui.SetWindowPos(state['hwnd'],win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE)
        native_windows=Windows()
        native_windows.cursor_position=lambda:win32gui.ClientToScreen(state['hwnd'],(30,30))
        picker=BackgroundWindowPicker(native_windows);picker.show();QTest.qWait(40)
        QTest.mouseClick(picker,Qt.LeftButton,Qt.NoModifier,QPoint(100,100))
        params=picker.selection
        check(picker.result()==QDialog.Accepted and params['窗口句柄']==str(state['hwnd']),'actual window point selection')
        entry['window_picker']={'handle_matches':True,'pid_matches':params['进程ID']==state['pid']}
        picker.deleteLater();app.processEvents()
        win32gui.SetWindowPos(state['hwnd'],win32con.HWND_NOTOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE)
        params['绑定等待']=.3
        params['绑定方案']='GDI 兼容'
        context=ExecutionContext(services={"background_transport":TracedTransport})
        bind_background(context,params);backend=current_backend(context)
        entry['version']=backend.transport.version
        image=backend.screenshot();image.save(folder/'capture.png')
        check(image.size==(400,240),'screenshot dimensions')
        check(image.getpixel((30,30))==(255,0,0),'red pixel')
        check(image.getpixel((110,20))==(17,34,51),'background pixel')
        check(method(context,'GetColor',{'x':30,'y':30})=='ff0000','GetColor')
        method(context,'GetColorHSV',{'x':30,'y':30})
        converted=method(context,'ClientToScreen',{'x':5,'y':8})['output']
        check((converted['x'],converted['y'])==win32gui.ClientToScreen(state['hwnd'],(5,8)),'ClientToScreen preserves input')
        array=execute_background_method(context,'后台图色操作',{'接口':'CaptureArray','参数':'{"x1":20,"y1":20,"x2":22,"y2":22}'})
        base64 = _module_imports.load('base64')
        check(base64.b64decode(array['data_base64'])==bytes((255,0,0))*4,'CaptureArray RGB bytes')
        check(method(context,'CmpColor',{'x':30,'y':30,'color':'ff0000-000000','sim':1})==0,'CmpColor')
        found=method(context,'FindColor',{'x1':0,'y1':0,'x2':100,'y2':100,'color':'ff0000-000000','sim':1,'dir':0})
        check(found['value']==1 and found['output']['x']==20 and found['output']['y']==20,'FindColor coordinates')
        template=folder/'template.bmp';image.crop((58,18,87,48)).save(template)
        found=method(context,'FindPic',{'x1':0,'y1':0,'x2':200,'y2':120,'pic_name':str(template),'delta_color':'000000','sim':1,'dir':0})
        check(found['value']==0 and found['output']['x']>=0,'FindPic template')
        dict_info=method(context,'FetchWord',{'x1':59,'y1':19,'x2':86,'y2':46,'color':'ffffff-000000','word':'A'})
        check(bool(dict_info),'FetchWord')
        check(method(context,'AddDict',{'index':0,'dict_info':dict_info})==1,'AddDict')
        method(context,'UseDict',{'index':0})
        text=method(context,'Ocr',{'x1':50,'y1':10,'x2':95,'y2':55,'color':'ffffff-000000','sim':1})
        check('A' in text,'OCR dictionary actual recognition')
        method(context,'GetWordsNoDict',{'x1':50,'y1':10,'x2':95,'y2':55,'color':'ffffff-000000'})
        check(method(context,'ReadInt',{'addr':state['address'],'type':0})==123456,'ReadInt fixture')
        check(method(context,'WriteInt',{'addr':state['address'],'type':0,'v':654321})==1,'WriteInt fixture')
        check(method(context,'ReadInt',{'addr':state['address'],'type':0})==654321,'ReadInt after write')
        method(context,'WriteInt',{'addr':state['address'],'type':0,'v':123456})
        method(context,'AsmClear')
        method(context,'AsmAdd',{'asm_ins':'mov eax, 42'})
        method(context,'AsmAdd',{'asm_ins':'ret'})
        machine=method(context,'Assemble',{'base_addr':0,'is_64bit':0});check(bool(machine),'Assemble')
        disasm=method(context,'DisAssemble',{'asm_code':machine,'base_addr':0,'is_64bit':0});check('MOV' in disasm.upper(),'DisAssemble')
        check(method(context,'AsmCall',{'hwnd':0,'mode':0})==0x42,'local assembly execution')
        # Run real existing and new commands through the connected graph engine.
        close_background(context)
        db=DatabaseOperation(str(folder/'flow.db'));repo=GraphRepository(db.db_path);repo.clear()
        drafts=[InstructionDraft('绑定选择窗口',params),InstructionDraft('坐标点击',{'坐标':'30,30','动作':'左键单击'}),InstructionDraft('按下键盘',{'按键':'a','按压时长':.01}),InstructionDraft('文本输入',{'内容':'后台中文验证','手动输入':False}),InstructionDraft('后台图色操作',{'接口':label('GetColor'),'参数':'{"x":30,"y":30}','变量':'pixel'}),InstructionDraft('颜色判断',{'坐标':'30,30','颜色':'#FF0000','变量':'matched'}),InstructionDraft('解除后台绑定',{})]
        commands=[repo.add_command(d,unconnected=True) for d in drafts]
        nodes={n.command_id:n.node_id for n in repo.snapshot().nodes if n.command_id is not None}
        repo.connect_nodes('start',nodes[commands[0].id])
        for left,right in zip(commands,commands[1:]):repo.connect_nodes(nodes[left.id],nodes[right.id])
        repo.connect_nodes(nodes[commands[-2].id],'end')
        repo.connect_nodes(nodes[commands[-1].id],'end')
        repo.validate_graph()
        with patch('main_work.DatabaseOperation',return_value=db):
            worker=CommandThread(type('Window',(),{'execution_services':{}})())
        worker.repository=repo;worker.run_mode=('全部指令',None);worker.start_state=True
        context=ExecutionContext(services={"background_transport":TracedTransport});cursor=win32gui.GetCursorPos()
        worker._execute_commands(worker._commands_for_mode(),context)
        check(context.variables['pixel']=='ff0000' and context.variables['matched'] is True,'graph variable result')
        check(current_backend(context) is None,'graph unbind')
        time.sleep(.6);state=json.loads(state_path.read_text(encoding='utf8'))
        check(state['clicks']>=1 and state['keys']>=1,'target received click and key')
        check('后台中文验证' in state['text'],'target received unicode input')
        check(all(item['before']==item['after'] for item in entry['input_observations']),
              'a background input call changed the physical cursor')
        entry['graph']={'commands':len(commands),'variables':dict(context.variables),'target':state}
        entry['passed']=True
    except Exception:
        entry['error']=traceback.format_exc()
    finally:
        if context:close_background(context)
        if state and win32gui.IsWindow(state['hwnd']) and win32process.GetWindowThreadProcessId(state['hwnd'])[1]==state['pid']:
            win32gui.PostMessage(state['hwnd'],win32con.WM_CLOSE,0,0)
        if process:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=3)
            if process.stderr:process.stderr.close()
        destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(bits,entry['passed'],entry.get('error',''),flush=True)
if not all(e['passed'] for e in report.values()):raise SystemExit(1)
