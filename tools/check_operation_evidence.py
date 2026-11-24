import sys,tempfile
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.domain.agent_protocol import make_draft
from anclicker.domain.instructions import ExecutionContext
from models.operation_evidence import automatic_check,before_operation,operation_evidence
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);source=root/'原件.txt';target=root/'副本.txt';source.write_text('原始内容',encoding='utf8')
 draft=make_draft('快速文件操作',{'操作':'复制','源路径':str(source),'目标路径':str(target)})
 check=automatic_check(draft);ctx=ExecutionContext()
 with patch('models.operation_evidence.open_path'),patch('models.operation_evidence.verify_open_folder',return_value={'verified':True}) as verify:
  assert not operation_evidence(check,None,ctx)['verified'];verify.assert_not_called()
  target.write_text('错误内容',encoding='utf8');assert not operation_evidence(check,None,ctx)['verified']
  target.write_bytes(source.read_bytes());assert operation_evidence(check,None,ctx)['verified'];assert verify.call_args.kwargs['expected_text']==['副本']
 rename=automatic_check(make_draft('运行cmd',{'命令':f'ren "{source}" "改名.txt"'}));before_operation(rename,ctx);source.rename(root/'改名.txt')
 with patch('models.operation_evidence.open_path'),patch('models.operation_evidence.verify_open_folder',return_value={'verified':True}):assert operation_evidence(rename,0,ctx)['verified']
 assert automatic_check(make_draft('运行cmd',{'命令':f'mkdir "{root}/a" & echo unrelated'})) is None
 assert automatic_check(make_draft('运行cmd',{'命令':f'ren "{target}" "../escape"'})) is None
print('PASS automatic file evidence, hash mismatch veto, rename state and unsupported command rejection')
