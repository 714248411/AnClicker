import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.local_operation_bindings import local_instruction
from models.chinese_planner import resolve_previous_file
from anclicker.domain.agent_protocol import make_draft
source='C:/Work/report.txt';target='C:/Backup/report.txt'
opened=local_instruction('打开文件“'+source+'”');assert opened['parameters']=={'操作':'打开','源路径':source}
resolved=resolve_previous_file('复制刚才打开的文件到“'+target+'”',[make_draft(**opened)])
assert local_instruction(resolved)['parameters']=={'操作':'复制','源路径':source,'目标路径':target}
for text in ['不要打开文件“C:/Work/report.txt”','输入“打开文件C:/Work/report.txt”','如果存在就打开文件“C:/Work/report.txt”','打开文件“C:/Work/report.txt”，然后删除它']:
 assert local_instruction(text) is None,text
print('PASS explicit open/copy binding, previous-file resolution and four negative boundaries')
