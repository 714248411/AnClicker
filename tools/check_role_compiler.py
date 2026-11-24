from models.instruction_compiler import compiler_candidates,validate_python_instruction
from models.dual_model import split_messages
assert '运行Python' not in compiler_candidates('在当前文本框输入“算SHA256”')
assert '运行Python' not in compiler_candidates('等两秒')
assert '运行Python' in compiler_candidates('计算文本“甲乙丙”的SHA256')
valid={'type_id':'运行Python','parameters':{'代码':'import hashlib\nresult=hashlib.sha256("甲乙丙".encode("utf-8")).hexdigest()','返回值':'result'}}
validate_python_instruction('计算文本“甲乙丙”的SHA256',valid)
for request,code in [('等待三秒','result=3'),('计算文本“abc”的SHA256','import subprocess\nresult=subprocess.call("whoami")'),('读取“E:/允许.txt”','from pathlib import Path\nresult=Path("E:/其他.txt").read_text()'),('计算文本哈希','x=3')]:
 try:validate_python_instruction(request,{'type_id':'运行Python','parameters':{'代码':code,'返回值':'result'}})
 except ValueError:pass
 else:raise AssertionError((request,code))
print('PASS native preference, internal Python compilation, result binding and no invented paths or external command fallback')

from models.instruction_compiler import bind_python_inputs
from models.conversational_contracts import quoted_values,boundary_contract
import json
literal=json.dumps({"z":4,"a":"中文路径"},ensure_ascii=False)
request='将JSON“'+literal+'”按键名排序并缩进两格整理'
assert quoted_values(request)==[literal]
item={'type_id':'运行Python','parameters':{'代码':'import json\nresult=json.dumps(json.loads(inputs[0]),ensure_ascii=False,sort_keys=True,indent=2)','返回值':'result'}}
validate_python_instruction(request,item);bind_python_inputs(request,item)
ns={};exec(item['parameters']['代码'],ns)
assert ns['result']==json.dumps(json.loads(literal),ensure_ascii=False,sort_keys=True,indent=2)
assert boundary_contract(['等十二秒','刚说错了','改成六秒'],[True,True])==[False,False]
for code in ['inputs=[]\nresult=1','result=inputs[3]','inputs[0]="other"\nresult=1']:
 try:bind_python_inputs('处理“原文”',{'type_id':'运行Python','parameters':{'代码':code}})
 except ValueError:pass
 else:raise AssertionError(code)
print('PASS nested JSON literal binding, input index integrity and correction grouping')

from models.instruction_compiler import normalize_python_syntax
item={'type_id':'运行Python','parameters':{'代码':'import json result = json.loads(inputs[0])'}}
assert normalize_python_syntax(item)
assert item['parameters']['代码']=='import json; result = json.loads(inputs[0])'
assert not normalize_python_syntax(item)
print('PASS narrowly scoped import separator repair')
