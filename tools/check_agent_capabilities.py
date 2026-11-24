"""Catalogue coverage, real file copies, OCR decision paths and native editors."""
import sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.agent_protocol import catalog,instruction_schema,make_draft
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext
from models.draft_planner import candidate_types,parameter_schema,plan_drafts
from models.agent_provider import AgentSettings
from models.system_actions import file_action,parse_file_task
from models.screen_verifier import verify_screen
from models.tool_api import ToolAPIServer
from anclicker.platform.qt_compat.QtWidgets import QApplication
from PIL import Image

def main():
    app=QApplication([]);ctx=ExecutionContext();count=0
    for item in catalog():
        name=item['type_id'];schema=instruction_schema(name)
        assert name in candidate_types('使用'+name),'unreachable '+name
        assert set(parameter_schema(name)['properties'])==set(schema['parameters']['properties']),name
        spec=get_instruction_spec(name);assert spec.create_executor() is not None
        params={k:v['default'] for k,v in schema['parameters']['properties'].items()}
        for key in schema['required_fields']:
            if params[key] in ('',None):params[key]='测试参数'
        result=plan_drafts('使用'+name+' 参数 '+json.dumps(params,ensure_ascii=False),AgentSettings(),ctx)
        assert result.get('arguments',{}).get('instructions',[{}])[0].get('type_id')==name, (name,result)
        count+=1
    for name in ('快速文件操作','截图OCR核验'):
        editor=get_instruction_spec(name).create_editor();editor.close();editor.deleteLater()
    assert parse_file_task('不要打开 "C:/a.txt"') is None
    assert parse_file_task('如果存在就复制 "C:/a" 到 "C:/b"') is None
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);source=folder/'源文件 & %test%!.txt';target=folder/'目标文件.txt'
        source.write_text('AnClicker copy verification 中文',encoding='utf-8')
        result=file_action(ctx,'copy',str(source),str(target));assert result['verified'] and target.read_bytes()==source.read_bytes()
        try:file_action(ctx,'copy',str(source),str(target))
        except FileExistsError:pass
        else:raise AssertionError('Existing target overwritten')
        ctx.stop_requested=True
        try:file_action(ctx,'copy',str(source),str(folder/'cancel.txt'))
        except InterruptedError:pass
        else:raise AssertionError('Cancelled action ran')
        ctx.stop_requested=False
    services={'agent_screenshot':lambda bounds:Image.new('RGB',(400,150),'white'),
        'agent_ocr':lambda path:[{'text':'Copy complete','score':.99,'box':[[1,1],[200,1],[200,40],[1,40]]}]}
    check=ExecutionContext(services=services)
    assert verify_screen(check,['Copy complete'],region='0,0,400,150')['verified']
    assert not verify_screen(check,['Missing text'],region='0,0,400,150',attempts=1)['verified']
    assert not verify_screen(check,['Copy complete'],region='0,0,400,150',minimum_score=1,attempts=1)['verified']
    assert not verify_screen(check,['Copy complete'],attempts=1)['verified']
    server=ToolAPIServer(('127.0.0.1',0),'test',allow_browser=True)
    try:assert not server.allowed('system_file') and not server.allowed('verify_screen')
    finally:server.server_close()
    print('PASS:',count,'registered instruction schemas reachable with complete parameters; real robocopy+SHA256; overwrite/cancel; OCR decision paths; native editors; API separation')
if __name__=='__main__':main()
