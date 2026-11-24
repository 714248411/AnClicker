"""Resolve explicit Recycle Bin actions without inventing a disk path or web selector."""
import json
import os
import re
import subprocess
from pathlib import Path

def recycle_bin_instruction(text):
    from models.sentence_contracts import clean_action
    text=clean_action(text)
    inverted=re.fullmatch(r'(?:把|将)((?:桌面(?:上)?(?:的)?)?回收站)(打开|选中)[。！]?',text)
    if inverted:text=inverted[2]+inverted[1]
    location=re.fullmatch(r'在桌面(?:上)?(?:点击|点一下|单击)(回收站)[。！]?',text)
    if location:text='点击桌面'+location[1]
    match=re.fullmatch(r'\s*(?:请帮我|帮我|请|麻烦)?\s*(点击|单击|点一下|双击|打开|选中)\s*(?:桌面(?:上|里)?(?:的)?\s*)?[“"]?回收站[”"]?(?:图标)?\s*[。！]?\s*',text)
    if not match:return None
    action='open' if match[1] in ('打开','双击') else 'select'
    code='from models.desktop_shell import operate_recycle_bin\nresult = operate_recycle_bin('+repr(action)+')'
    return {'type_id':'运行Python','parameters':{'代码':code,'返回值':'result','变量':'桌面操作结果'}}

def operate_recycle_bin(action):
    if action not in ('select','open'):raise ValueError('不支持的回收站操作')
    if os.name!='nt':raise RuntimeError('桌面回收站操作仅支持 Windows')
    if action=='open':
        os.startfile('shell:RecycleBinFolder')
        return {'target':'回收站','action':'open','status':'requested'}
    script=Path(__file__).with_name('select_recycle_bin.ps1')
    powershell=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    completed=subprocess.run([str(powershell),'-NoProfile','-NonInteractive','-File',str(script)],
        capture_output=True,encoding='utf-8',errors='replace',timeout=20,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if completed.returncode:
        raise RuntimeError('未能选中桌面回收站：'+(completed.stderr.strip() or '请确认桌面显示了回收站图标。'))
    try:result=json.loads(completed.stdout.lstrip('\ufeff').strip())
    except ValueError as error:raise RuntimeError('桌面控件没有返回有效的选择结果') from error
    if result.get('selected') is not True:raise RuntimeError('桌面回收站尚未选中')
    return result
