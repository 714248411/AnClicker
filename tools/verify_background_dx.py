"""Probe DX presets only against temporary test windows owned by this script."""
import json,os,sys,time,subprocess,traceback,threading
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
os.environ['ANCLICKER_DATA_DIR']=str(root/'validation/background-dx-data')
from instructions.models import ExecutionContext
from background_runtime import Windows,bind_background,current_backend,close_background
from background_binding import AUTO
import win32gui,win32con,win32process
result=[];destination=root/'validation/background-dx-results.json'
for bits in (32,64):
    for preset in ((AUTO,) if '--auto-only' in sys.argv else ('DX1','DX2',AUTO)):
        entry={'bits':bits,'preset':preset};result.append(entry)
        process=None;state=None;context=ExecutionContext();timer=None
        try:
            folder=root/'validation'/('dx-fixture-'+str(bits));folder.mkdir(exist_ok=True)
            state_path=folder/'state.json';state_path.unlink(missing_ok=True)
            shell=Path(os.environ['WINDIR'])/('SysWOW64' if bits==32 else 'System32')/'WindowsPowerShell/v1.0/powershell.exe'
            process=subprocess.Popen([str(shell),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'validation/dm-fixture.ps1'),str(state_path)],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            deadline=time.monotonic()+12
            while not state_path.exists() and time.monotonic()<deadline and process.poll() is None:time.sleep(.05)
            state=json.loads(state_path.read_text(encoding='utf8'))
            params=Windows().describe(state['hwnd']);params.update({'绑定方案':preset,'绑定等待':.5})
            timer=threading.Timer(30,lambda:setattr(context,'stop_requested',True));timer.start()
            start=time.monotonic();bind_background(context,params)
            backend=current_backend(context)
            entry.update(bound=True,selected=backend.binding_profile,seconds=round(time.monotonic()-start,2))
            try:
                image=backend.screenshot()
                entry['capture_matches_fixture']=image.size==(400,240) and image.getpixel((30,30))==(255,0,0) and image.getpixel((110,20))==(17,34,51)
                image.save(folder/(('auto' if preset==AUTO else preset)+'.png'))
            except Exception as error:entry['capture_error']=str(error)
            cursor=win32gui.GetCursorPos()
            backend.click(30,30);backend.keyDown('a');time.sleep(.1);backend.keyUp('a');backend.write('DX验证')
            entry['input_calls_passed']=True
            entry['cursor_unchanged_during_calls']=win32gui.GetCursorPos()==cursor
            time.sleep(.4)
            actual=json.loads(state_path.read_text(encoding='utf8'))
            entry['target']={key:actual[key] for key in ('clicks','keys','text')}
        except Exception:
            entry['error']=traceback.format_exc()
        finally:
            if timer:timer.cancel()
            try:close_background(context)
            except Exception as error:entry['cleanup_error']=str(error)
            if state and win32gui.IsWindow(state['hwnd']) and win32process.GetWindowThreadProcessId(state['hwnd'])[1]==state['pid']:
                win32gui.PostMessage(state['hwnd'],win32con.WM_CLOSE,0,0)
            if process:
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=3)
            destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
            print(bits,preset,entry,flush=True)
auto=[entry for entry in result if entry['preset']==AUTO]
if len(auto)!=2 or not all(e.get('bound') and e.get('capture_matches_fixture') and e.get('input_calls_passed') and not e.get('cleanup_error') for e in auto):raise SystemExit(1)
