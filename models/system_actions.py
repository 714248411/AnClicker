"""Fast local file operations using structured OS calls, with SHA-256 verification."""
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from anclicker.execution import actions
from anclicker.platform.services import open_path
from models.screen_verifier import verify_screen
from models.local_paths import parse_known_folder
from models.folder_verifier import verify_open_folder

def digest(path,context):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            if context.stop_requested:raise InterruptedError('已停止')
            chunk=stream.read(1024*1024)
            if not chunk:break
            value.update(chunk)
    return value.hexdigest()

def file_action(context,action,source,destination='',overwrite=False,expected_text=None,window_title='',region=''):
    source=Path(actions.substitute_variables(context,source)).expanduser()
    if not source.is_absolute() or not source.exists():raise ValueError('源路径必须是存在的绝对路径')
    source=source.resolve()
    if context.stop_requested:raise InterruptedError('已停止')
    result={'action':action,'source':str(source),'verified':False}
    if action=='open':
        open_path(str(source));result.update(backend='Windows ShellExecute',status='open_requested')
    elif action=='copy':
        if not source.is_file():raise ValueError('快速复制当前仅支持单个文件；文件夹请使用处理文件指令')
        target=Path(actions.substitute_variables(context,destination)).expanduser()
        if not target.is_absolute():raise ValueError('目标必须是绝对路径')
        if target.is_dir():target=target/source.name
        target=target.resolve()
        if source==target:raise ValueError('源文件和目标文件相同')
        if target.exists() and not overwrite:raise FileExistsError('目标已存在；如需覆盖请明确设置 overwrite=true')
        if not target.parent.is_dir():raise ValueError('目标父目录不存在')
        before=digest(source,context)
        # Copy to an isolated staging directory, so failed commands cannot clobber the target.
        with tempfile.TemporaryDirectory(prefix='.anclicker-copy-',dir=target.parent) as staging:
            runner=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/robocopy.exe'
            command=[str(runner),str(source.parent),staging,source.name,'/R:0','/W:0','/COPY:DAT','/NP','/NFL','/NDL','/NJH','/NJS']
            process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                while process.poll() is None:
                    if not actions.wait_interruptibly(context,.05):raise InterruptedError('已停止')
                if process.returncode>=8:raise RuntimeError('robocopy 失败，退出码 '+str(process.returncode))
            finally:
                if process.poll() is None:process.kill();process.wait()
            copied=Path(staging)/source.name
            if not copied.is_file() or digest(copied,context)!=before or digest(source,context)!=before:raise RuntimeError('复制校验不一致，未提交目标文件')
            if context.stop_requested:raise InterruptedError('已停止')
            if overwrite:os.replace(copied,target)
            else:os.rename(copied,target)  # Windows fails if target appeared concurrently.
        result.update(destination=str(target),backend='robocopy',status='copied',verified=True,sha256=before)
    else:raise ValueError('仅支持 open/copy')
    if expected_text:
        verification=verify_screen(context,expected_text,window_title,region)
        result['visual_verification']=verification
        result['verified']=result['verified'] and verification['verified'] if action=='copy' else verification['verified']
        result['status']='verified' if result['verified'] else 'unconfirmed'
    elif action=='open' and source.is_dir():
        verification=verify_open_folder(context,source)
        result.update(visual_verification=verification,verified=verification['verified'],status='verified' if verification['verified'] else 'unconfirmed')
    elif action=='open':result['note']='已请求打开；尚未截图核验窗口内容'
    return result

def parse_file_task(text):
    known=parse_known_folder(text)
    if known:return known
    # Deliberately exact: never execute a negated, conditional or mixed free-form command.
    path=r'["“]([^"”]+)["”]'
    match=re.fullmatch(r'\s*(?:请)?(?:打开|打开文件|打开文件夹)\s*'+path+r'[。！]?\s*',text)
    if match:return {'action':'open','source':match[1]}
    match=re.fullmatch(r'\s*(?:请)?(?:复制|复制文件|拷贝)\s*'+path+r'\s*(?:到|至)\s*'+path+r'[。！]?\s*',text)
    if match:return {'action':'copy','source':match[1],'destination':match[2]}
    return None

def parse_verify_task(text):
    match=re.fullmatch(r'\s*(?:截图\s*OCR\s*核验(?:窗口)?|检查窗口|核验窗口)\s*["“]([^"”]+)["”]\s*(?:是否显示|显示|包含)\s*["“]([^"”]+)["”][。！]?\s*',text,re.I)
    if match:return {'window_title':match[1],'expected_text':[x.strip() for x in match[2].split('|') if x.strip()]}
    return None
