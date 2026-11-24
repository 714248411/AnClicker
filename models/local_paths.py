"""Resolve explicit Chinese known-folder requests without an LLM guessing paths."""
import os
import re
import winreg
from pathlib import Path

def known_folder(label):
    names={'桌面':('Desktop','Desktop'),'下载':('{374DE290-123F-4565-9164-39C4925E467B}','Downloads'),'文档':('Personal','Documents')}
    value,fallback=names[label]
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            path=winreg.QueryValueEx(key,value)[0]
        return Path(os.path.expandvars(path))
    except OSError:return Path.home()/fallback

def parse_known_folder(text):
    from models.sentence_contracts import clean_action
    text=clean_action(text)
    inverted=re.fullmatch(r'(?:把|将)((?:桌面|下载|文档).+?)打开(?:看看)?[。！]?',text)
    if inverted:text='打开'+inverted[1]
    match=re.fullmatch(r'\s*(?:请帮我|帮我|请)?打开\s*(桌面|下载|文档)(?:上|里|中)?(?:的)?\s*(.*?)[。！]?\s*',text)
    if not match:return None
    label,tail=match.groups();tail=tail.strip()
    if not tail or tail=='文件夹':target=known_folder(label)
    else:
        base=known_folder(label).resolve()
        # Try the complete name before interpreting 文件夹 as a noun around it.
        quoted=re.fullmatch(r'(?:文件夹\s*)?(?:“([^”]+)”|"([^"]+)")(?:这个|的)?(?:文件夹)?',tail)
        if quoted:
            candidates=[next(value for value in quoted.groups() if value is not None)]
        else:
            bare=re.sub(r'^文件夹\s*','',tail)
            candidates=list(dict.fromkeys([tail,bare,
                re.sub(r'(?:这个|的)?文件夹$','',tail).strip(),
                re.sub(r'(?:这个|的)?文件夹$','',bare).strip()]))
        valid=[]
        for name in candidates:
            if not name or name in ('.','..') or re.search(r'[\\/:*?"<>|\r\n]|然后|并且|并打开|再打开|并删除|后删除|，|；',name):continue
            candidate=base/name
            if candidate.resolve().parent!=base:continue
            valid.append(candidate)
        if not valid:return None
        target=next((candidate for candidate in valid if candidate.is_dir()),valid[0])
    if not target.is_dir():raise ValueError('没有找到文件夹：'+str(target)+'。请检查名称是否正确。')
    return {'action':'open','source':str(target.resolve())}
