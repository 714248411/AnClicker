"""Shared Chinese action suggestions; choosing a suggestion never runs it."""
from dataclasses import dataclass, field
import json
from instructions.registry import INSTRUCTION_SPECS, get_instruction_spec

@dataclass(frozen=True)
class Suggestion:
    label: str
    kind: str
    parameters: dict = field(default_factory=dict)
    aliases: str = ''

PASTE = (
    Suggestion('先点击位置，再粘贴文字', '坐标点击', aliases='点击位置 点选坐标 点击后粘贴'),
    Suggestion('粘贴到当前输入位置', 'OCR粘贴', {'内容来源':'剪贴板'}, '粘贴文字 剪贴板 直接粘贴'),
    Suggestion('把文字粘贴到表格单元格', '粘贴到单元格', aliases='粘贴到Excel 粘贴到表格 写入表格'),
    Suggestion('把文字粘贴到网页输入框', '粘贴到网页元素', aliases='粘贴到网页 网页粘贴 网页输入框'),
    Suggestion('按 Ctrl+V 粘贴', '按下键盘', {'按键':'ctrl+v'}, '快捷键粘贴'),
    Suggestion('点击网页位置并粘贴', '点击并粘贴', aliases='点击网页后粘贴'),
)
WEB_WAIT = (
    Suggestion('先等一会儿（按秒设置）', '等待（秒）', aliases='等待时间 延时 暂停 等一会'),
    Suggestion('等按钮或输入框出现', '等待元素出现', aliases='等按钮出现 等输入框出现'),
    Suggestion('等网页加载完毕再继续', '等待页面加载完成', aliases='等待网页加载完成 等页面打开完'),
)
WEB_ACTIONS = (
    Suggestion('先选中要操作的按钮或输入框', '拾取元素', aliases='选择网页按钮 选择输入框'),
    Suggestion('点击网页中的按钮或链接', '点击元素', aliases='网页点击 点击按钮'),
    Suggestion('在网页输入框里填写文字', '输入文本', aliases='网页输入'),
    PASTE[3],
    Suggestion('读取网页上的文字', '获取文本', aliases='读取网页文字'),
)
COMMON = (
    Suggestion('先打开网页', '打开网页', aliases='打开网站 访问网址'),
    Suggestion('先打开Excel表格', '打开Excel', aliases='打开表格'),
    Suggestion('识别并复制文字', 'OCR复制', aliases='复制识别文字 复制文字 截图识字'),
    *PASTE,
    Suggestion('等待一会儿再继续', '时间等待', aliases='等待 暂停 延时'),
    Suggestion('保存表格', '保存Excel', aliases='保存Excel'),
    Suggestion('点击网页中的按钮', '点击元素', aliases='网页点击 点击按钮'),
    Suggestion('在网页中输入文字', '输入文本', aliases='网页输入'),
)

def suggestions():
    candidates = COMMON + WEB_WAIT + WEB_ACTIONS
    primary = tuple(s for index,s in enumerate(candidates) if s.kind not in {prior.kind for prior in candidates[:index]})
    known={s.kind for s in primary}
    return primary + tuple(Suggestion(s.display_name,s.type_id,aliases=s.category) for s in INSTRUCTION_SPECS if s.type_id not in known)

def matching(text):
    text=text.strip().casefold()
    for prefix in ('然后','接着','下一步','我想','我要','请'):
        if text.startswith(prefix):text=text[len(prefix):].strip()
    tokens=[c for c in text if c not in '把将的到先再一个，。 ']
    def score(item):
        hay=(item.label+' '+item.kind+' '+item.aliases).casefold()
        if text in hay:return 100+len(text)
        if tokens and all(c in hay for c in tokens):return len(tokens)
        return 0
    return sorted((s for s in suggestions() if score(s)>0),key=score,reverse=True)

def next_steps(kind, clipboard_ready=False, parameters=None):
    if kind in ('OCR复制','复制到剪贴板','点击并全选复制'):
        primary={s.kind for s in PASTE}
        labels={'复制粘贴（选择性粘贴）':'表格区域选择性复制粘贴','表格复制粘贴':'工作表之间复制粘贴','表格复制粘贴（白话）':'表格文件之间复制粘贴'}
        extra=tuple(Suggestion(labels.get(s.type_id,s.display_name),s.type_id) for s in INSTRUCTION_SPECS if '粘贴' in s.type_id and s.type_id not in primary)
        return PASTE + extra
    if clipboard_ready and kind in ('坐标点击','图像点击','点击元素','OCR点击识别区域'):
        return PASTE[1:]
    if kind=='打开网页':return WEB_WAIT + WEB_ACTIONS
    if kind in {item.kind for item in WEB_WAIT}:
        return WEB_ACTIONS + tuple(item for item in WEB_WAIT if item.kind != kind)
    if kind == '拾取元素':return WEB_ACTIONS[1:]
    if kind == '点击元素':return (WEB_WAIT[1], WEB_WAIT[2], WEB_ACTIONS[2], PASTE[3], WEB_ACTIONS[-1])
    if kind in ('输入文本','粘贴到网页元素'):
        return (Suggestion('填好后按回车确认','按键',{'key':'回车(Enter)','times':1}), WEB_ACTIONS[1], WEB_WAIT[1], WEB_ACTIONS[-1])
    if kind == '按键':return (WEB_WAIT[1], WEB_WAIT[2], WEB_ACTIONS[-1], WEB_ACTIONS[1])
    if kind == '获取文本':
        name = str((parameters or {}).get('varName') or '变量1')
        return (Suggestion('把读取到的文字写入表格','Excel写入单元格',{'value':'${'+name+'}'},aliases='文字写入Excel'), Suggestion('把网页内容提取到表格','提取文本到表格'), WEB_ACTIONS[1])
    if kind in ('打开Excel','新建Excel'):return (PASTE[2],Suggestion('读取表格单元格','读取单元格'),COMMON[-3])
    if kind in ('粘贴到单元格','Excel写入单元格','写入区域'):return (COMMON[-3], PASTE[2])
    if kind == 'OCR粘贴':
        return (Suggestion('按回车确认','按下键盘',{'按键':'enter'}),next(s for s in COMMON if s.kind == '时间等待'))
    return ()

def command_template(suggestion):
    editor=get_instruction_spec(suggestion.kind).load_editor_class()
    params={f.key:f.default for f in editor.FIELDS}
    params.update(suggestion.parameters)
    return suggestion.kind+'('+json.dumps(params,ensure_ascii=False)+', 重复次数=1, 异常处理="提示异常并暂停")'
