"""Second-role contract: native AnClicker first, internal Python only for capability gaps."""
import ast,re
from functools import lru_cache
from models.conversational_contracts import intent_text,quoted_values
from models.draft_planner import candidate_types
from anclicker.instructions.registry import iter_instruction_specs

@lru_cache(maxsize=1)
def native_catalog():return '、'.join(s.type_id for s in iter_instruction_specs() if s.type_id not in ('运行Python','运行cmd'))

def native_preference(text):
    t=intent_text(text)
    if '文件' in t and '行数' in t:return False
    if re.search(r'SHA.?256|哈希|校验和|base64|JSON.*(?:排序|格式|缩进)|去重|CSV.*(?:合计|求和)',t,re.I):return False
    if re.search(r'CSS|XPath|选择器',t,re.I) and candidate_types(text)==['输入文本']:return True
    if re.search(r'cmd|命令行',t,re.I):return True
    from models.instruction_catalog import ALIASES,normalize
    if any(len(spec.type_id)>=3 and normalize(spec.type_id) in normalize(t) for spec in iter_instruction_specs() if spec.type_id not in ('运行Python','运行cmd')):return True
    if any(word in t and name not in ('运行Python','运行cmd') for word,name in ALIASES.items()):return True
    if re.search(r'输入|填入|打上|写上|键入',t) and not re.search(r'文件|CSV|JSON|SHA|哈希|编码',t,re.I):return True
    if re.search(r'^(?:请|帮我|麻烦|先|稍微|劳驾|再|稍等)*(?:等待|等|暂停|停留)',t) and re.search(r'秒|分钟',t):return True
    if re.search(r'回车|快捷键|按下|按一下',t):return True
    if re.search(r'复制|拷贝|拷一份|备份|重命名|截图|滚轮|点击|打开|访问',t) and not re.search(r'SHA|哈希|校验和|base64|JSON|CSV',t,re.I):return True
    return False

def compiler_candidates(text):
    from models.sentence_contracts import explicit_native_type
    t=intent_text(text)
    # An already-open workbook is context, not a request to open Excel.
    if "当前已打开表格" in t:
        if re.match(r"读取",t) and re.search(r"[A-Z]+[0-9]+:[A-Z]+[0-9]+",t):return ["读取区域"]
        if re.match(r"将变量",t) and "写入" in t and re.search(r"从[A-Z]+[0-9]+开始",t):return ["写入区域"]
    explicit=explicit_native_type(text)
    if explicit:return [explicit]
    from models.desktop_contracts import grounded_instruction
    ground=grounded_instruction(text)
    if ground:return [ground[0]]
    if python_reference(text):return ['运行Python']
    names=[n for n in candidate_types(text) if n!='运行Python']
    if not native_preference(text):names.append('运行Python')
    return list(dict.fromkeys(names))

COMPILER_SYSTEM='''你是AnClicker的第二个模型，只编译一个已拆好的动作，不拆句、不执行。优先选择匹配的AnClicker原生指令，输出type_id和parameters。原生能力能完成时禁止用Python替代。仅当没有合适原生指令时，输出type_id=运行Python，parameters包含代码、返回值=result、变量=Python返回值。代码是完整Python3标准库程序，计算结果赋值给result；输入路径、网址、文本和数值必须取自请求，禁止编造。引用的文本和文件路径由宿主按出现顺序绑定到inputs列表，代码必须使用inputs[0]等读取这些值，不要在代码中重复抄写原文。不得赋值或修改inputs。context是运行上下文，variables是共享变量字典。不要生成终端命令、pip安装、eval或exec。缺少对象、路径、数据或执行条件时返回type=message和content追问，不能拿Python绕过缺参。表格、名字、结果、这个不是网址；打开网页必须提供有效http或https网址。表格填写优先使用宿主已绑定的活动工作表和表头；未知行只追问哪一行，不能猜单元格或默认修改所有行。编号别动等约束不是额外动作，必须保留未指定字段。剩下的、放回去没有可靠上下文时只追问缺少的范围或位置。文本输入不附加回车；复制保留原件。只返回JSON。'''

def validate_python_instruction(request,item):
    if item.get('type_id')!='运行Python':return
    if native_preference(request):raise ValueError('该动作有合适原生指令，不能使用Python替代')
    code=item['parameters'].get('代码','');tree=ast.parse(code,mode='exec');compile(tree,'<generated-anclicker-python>','exec')
    if len(code)>12000:raise ValueError('Python代码过长，请拆分任务')
    result_name=item['parameters'].get('返回值','result')
    if result_name and not result_name.isidentifier():raise ValueError('Python返回值必须是有效变量名')
    if result_name and not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store) and n.id==result_name for n in ast.walk(tree)):raise ValueError('Python代码没有设置返回变量')
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            modules=[a.name.split('.')[0] for a in n.names] if isinstance(n,ast.Import) else [(n.module or '').split('.')[0]]
            if any(m in {'subprocess','socket','ctypes','requests','urllib','winreg'} for m in modules):raise ValueError('生成的Python不应启动命令或访问未声明的系统/网络接口')
        if isinstance(n,ast.Call):
            name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else ''
            if name in {'eval','exec','compile','system','popen','__import__','rmtree','unlink','remove','rmdir'}:raise ValueError('该Python调用不能在自动生成的补充指令中使用')
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            value=n.value
            if re.match(r'^[A-Za-z]:[/\\]|^https?://',value) and value.replace('\\','/').casefold() not in request.replace('\\','/').casefold():raise ValueError('Python代码包含请求以外的路径或网址')


def bind_python_inputs(request,item):
    if item.get("type_id") != "运行Python":return
    code=item["parameters"]["代码"]
    values=quoted_values(request)
    tree=ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node,ast.Name) and node.id=="inputs" and isinstance(node.ctx,(ast.Store,ast.Del)):
            raise ValueError("模型不能修改宿主输入绑定")
        if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=="inputs":
            if not isinstance(node.ctx,ast.Load) or not isinstance(node.slice,ast.Constant) or type(node.slice.value) is not int or not 0<=node.slice.value<len(values):
                raise ValueError("Python输入索引无效")
    item["parameters"]=dict(item["parameters"])
    item["parameters"]["代码"]="inputs = "+repr(values)+"\n"+code
    compile(item["parameters"]["代码"],"<bound-python>","exec")

# Small-model coding references. These are examples, never substituted for model output.
def python_reference(text):
    t=intent_text(text)
    if re.search(r'SHA.?256',t,re.I):
        if '文件' in t:return ('计算文件的SHA256','import hashlib\nfrom pathlib import Path\nresult = hashlib.sha256(Path(inputs[0]).read_bytes()).hexdigest()')
        return ('计算文本的SHA256','import hashlib\nresult = hashlib.sha256(inputs[0].encode("utf-8")).hexdigest()')
    if re.search(r'base64',t,re.I) and not re.search(r'解码|还原|文件',t):return ('文本转为Base64编码','import base64\nresult = base64.b64encode(inputs[0].encode("utf-8")).decode("ascii")')
    if re.search(r'JSON',t,re.I) and '排序' in t and re.search(r'两格|2格',t):return ('JSON按键名排序并缩进两格','import json\nresult = json.dumps(json.loads(inputs[0]), ensure_ascii=False, sort_keys=True, indent=2)')
    if '去重' in t and '逗号' in t and '原顺序' in t:return ('逗号分隔去重并保留顺序','result = list(dict.fromkeys(inputs[0].split(",")))')
    if '文件' in t and '行数' in t and 'UTF-8' in t.upper():return ('计算UTF-8文件行数','from pathlib import Path\nresult = len(Path(inputs[0]).read_text(encoding="utf-8").splitlines())')
    if 'CSV' in t.upper() and '金额' in t and re.search(r'合计|求和',t):return ('计算CSV金额列合计','import csv\nfrom pathlib import Path\nwith Path(inputs[0]).open(encoding="utf-8", newline="") as stream:\n    result = sum(float(row["金额"]) for row in csv.DictReader(stream))')
    return None

def compiler_user_text(text):
    from models.conversational_contracts import QUOTED
    index=iter(range(100));return QUOTED.sub(lambda m:'“inputs['+str(next(index))+']”',text)

def normalize_python_syntax(item):
    """Repair only a missing separator after a single import; never change an algorithm."""
    if item.get('type_id')!='运行Python':return False
    code=item['parameters'].get('代码','')
    try:ast.parse(code);return False
    except SyntaxError:pass
    fixed=re.sub(r'(?m)^import ([A-Za-z_][\w.]*)[ \t]+(?=[A-Za-z_]\w*\s*=)',r'import \1; ',code)
    if fixed==code:return False
    ast.parse(fixed)
    item['parameters']=dict(item['parameters'],代码=fixed)
    return True
