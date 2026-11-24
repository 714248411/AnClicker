import sys,tempfile
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.cmd_commands import normalize_cmd_paths
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import ExecutionContext,CommandRecord
with tempfile.TemporaryDirectory(prefix='anclicker-cmd-') as temp:
 root=Path(temp);source=root/'待改名.txt';source.write_text('实际重命名验证',encoding='utf8')
 executor=get_instruction_spec('运行cmd').create_executor()
 executor.execute(ExecutionContext(),CommandRecord(None,'运行cmd',{'命令':f'ren "{source.as_posix()}" "已改名.txt"','等待完成':True}))
 assert not source.exists() and (root/'已改名.txt').read_text(encoding='utf8')=='实际重命名验证'
 target=root/'新目录'
 executor.execute(ExecutionContext(),CommandRecord(None,'运行cmd',{'命令':f'mkdir "{target.as_posix()}"','等待完成':True}))
 assert target.is_dir()
assert normalize_cmd_paths('echo "C:/unchanged"')=='echo "C:/unchanged"'
assert normalize_cmd_paths('python -c "print(1/2)"')=='python -c "print(1/2)"'
print('PASS real Chinese filename rename/mkdir and non-filesystem command preservation')
