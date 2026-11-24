"""Locate the actual Explorer directory before verifying its visible OCR text."""
import os
import time
from pathlib import Path
from urllib.parse import unquote,urlparse
from models.screen_verifier import verify_screen
from anclicker.execution.actions import wait_interruptibly
from anclicker._imports import DeferredImports
_imports=DeferredImports(globals(),{'client':('import','win32com.client',(),True),'pythoncom':('import','pythoncom',(),False)})

def verify_open_folder(context,source,expected_text=None):
    expected_text=expected_text or [Path(source).name]
    target=os.path.normcase(str(Path(source).resolve()))
    result={'verified':False,'status':'unconfirmed','expected_text':expected_text,'target_path':str(source)}
    com=_imports.load('pythoncom');com.CoInitialize()
    try:
        client=_imports.load('client');shell=client.Dispatch('Shell.Application');deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if context.stop_requested:raise InterruptedError('已停止')
            for window in shell.Windows():
                try:
                    url=urlparse(str(window.LocationURL));path=unquote(url.path).lstrip('/')
                    if url.netloc:path='//'+url.netloc+'/'+path
                    if url.scheme!='file' or os.path.normcase(str(Path(path).resolve()))!=target:continue
                    handle=int(window.HWND)
                except Exception:continue
                if not wait_interruptibly(context,.4):raise InterruptedError('已停止')
                result=verify_screen(context,expected_text,window_handle=handle)
                result['target_path']=str(source);result['directory_confirmed']=True
                if result.get('verified'):return result
                break  # Explorer may have updated its path before painting the new view.
            if not wait_interruptibly(context,.2):raise InterruptedError('已停止')
        if not result.get('error'):result['error']='目标窗口尚未显示预期文字' if result.get('directory_confirmed') else '未找到已打开目标路径的资源管理器窗口'
        return result
    except InterruptedError:raise
    except Exception as error:result['error']=str(error);return result
    finally:com.CoUninitialize()
