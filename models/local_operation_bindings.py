"""Shared source-grounded bindings for single and multi-step computer requests."""
import re
from models.sentence_contracts import clean_action

def local_instruction(text):
    from models.desktop_shell import recycle_bin_instruction
    from models.local_paths import parse_known_folder
    item=recycle_bin_instruction(text)
    if item:return item
    known=parse_known_folder(text)
    if known:return {'type_id':'快速文件操作','parameters':{'操作':'打开','源路径':known['source']}}
    t=clean_action(text)
    from models.system_actions import parse_file_task
    file_task=parse_file_task(t)
    if file_task:
        params={'操作':'打开' if file_task['action']=='open' else '复制','源路径':file_task['source']}
        if file_task.get('destination'):params['目标路径']=file_task['destination']
        return {'type_id':'快速文件操作','parameters':params}
    repeated=re.fullmatch(r'按([两二三四五六七八九十0-9]+)下(回车|空格|删除)(?:键)?',t)
    if repeated:
        from models.chinese_planner import chinese_number
        count=int(chinese_number(repeated[1]))
        if not 1<=count<=100:raise ValueError('请将重复按键次数限定在1至100次')
        return {'type_id':'按下键盘','parameters':{'按键':{'回车':'enter','空格':'space','删除':'delete'}[repeated[2]]},'repeat_count':count}
    return None
