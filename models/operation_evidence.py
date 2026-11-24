"""Automatic evidence for structured local file tasks, without guessing screen targets."""
import re
from pathlib import Path
from models.system_actions import digest
from models.folder_verifier import verify_open_folder
from anclicker.platform.services import open_path

def automatic_check(draft):
    p=draft.parameters
    if draft.type_id in ('表格填入网页','提取文本到表格','Excel写入单元格','保存Excel'):
        return {'kind':'native_result','type_id':draft.type_id}
    if p.get('预期文字'):return None
    if draft.type_id=='快速文件操作' and p.get('操作')=='复制':
        source=Path(p.get('源路径',''));target=Path(p.get('目标路径',''))
        if source.is_absolute() and target.is_absolute():return {'kind':'copy','source':source,'target':target/source.name if target.is_dir() else target}
    if draft.type_id=='运行cmd':
        cmd=p.get('命令','').strip()
        match=re.fullmatch(r'(?:mkdir|md)\s+"([^"]+)"',cmd,re.I)
        if match and Path(match[1]).is_absolute():return {'kind':'mkdir','target':Path(match[1])}
        match=re.fullmatch(r'(?:ren|rename)\s+"([^"]+)"\s+"([^"]+)"',cmd,re.I)
        if match and Path(match[1]).is_absolute() and not re.search(r'[/\\:*?<>|]',match[2]) and match[2] not in ('.','..'):
            return {'kind':'rename','source':Path(match[1]),'target':Path(match[1]).with_name(match[2])}
    from models.web_evidence import web_check
    return web_check(draft)

def before_operation(check,context):
    if check and check['kind']=='rename':check['sha256']=digest(check['source'],context)

def operation_evidence(check,result,context):
    if check['kind']=='native_result':
        evidence=context.variables.get('保存核验') if check['type_id']=='保存Excel' else (result or {}).get('verification') if isinstance(result,dict) else None
        return evidence or {'verified':False,'error':'原生指令未返回结果核验证据'}
    if check['kind'].startswith('web_'):
        from models.web_evidence import web_evidence
        return web_evidence(check,context)
    target=check['target'];kind=check['kind']
    if kind=='mkdir':valid=target.is_dir()
    elif kind=='rename':valid=target.is_file() and not check['source'].exists() and digest(target,context)==check['sha256']
    else:valid=target.is_file() and check['source'].is_file() and digest(target,context)==digest(check['source'],context)
    if not valid:return {'verified':False,'status':'unconfirmed','error':'操作后文件状态或内容不符合预期','expected_text':[target.name]}
    # Show the actual parent directory and OCR its real file row, not a generated success label.
    open_path(str(target.parent))
    evidence=verify_open_folder(context,target.parent,expected_text=[target.name if target.is_dir() else target.stem])
    evidence['state_verified']=True;evidence['operation']=kind;evidence['result_path']=str(target)
    return evidence
