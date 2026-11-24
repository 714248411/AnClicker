"""Retrieve registered capabilities, never executable parameters or external examples."""
import json, math, re, subprocess, time, sys, tempfile
from collections import Counter
from pathlib import Path
from functools import lru_cache
from anclicker.domain.agent_protocol import catalog
from models.instruction_catalog import ALIASES, normalize
from models.conversational_contracts import intent_text

DESCRIPTIONS={
 '表格填入网页':'把表里的内容搬到页面 按名字对上 对着表头填 依次填表单',
 '提取文本到表格':'把网页结果写回表里 页面文字放到单元格',
 '滚轮滑动':'往下翻一点 往上翻一屏 滚动页面 鼠标滚轮',
 '鼠标拖拽':'按住鼠标拖过去 拖到另一边',
 '按下键盘':'敲一下回车 按组合键 全选快捷键',
 '文本输入':'在当前输入框打几个字 把这段话敲进去',
 'OCR精准找字点击':'找到屏幕上的文字并点击 按文字找按钮',
 '图像点击':'照着图片找图标 点击相同图案',
 '屏幕截图':'把现在的屏幕截下来 留张屏幕图片',
 'OCR文字提取':'提取图片上的字 识别照片里的文字 把图上的文字读出来',
 '获取剪切板':'读出刚复制的内容 读取剪贴板文字',
 '保存Excel':'把刚才改的表存一下 保存工作簿',
 '读取区域':'读表格里这一块的内容 获取单元格范围',
 'Excel写入单元格':'改表中指定格子的值 修改姓名单元格',
 '打开网页':'进入网址 访问网站 打开浏览器网页',
 '点击元素':'点击网页按钮 页面元素点击',
 '输入文本':'在网页输入框填写文字 搜索框输入关键词',
 '获取文本':'读取页面元素的文字 获取网页指定位置内容',
 '快速文件操作':'打开桌面文件夹 复制文件 保留原件 创建目录',
 '时间等待':'停一会儿 稍等几秒 等待一段时间',
}

def records(memory_enabled=True):
    from models.correction_memory import cases
    memories=cases() if memory_enabled else []
    result=[]
    for item in catalog():
        name=item['type_id']
        aliases=' '.join(k for k,v in ALIASES.items() if v==name)
        result.append({'type_id':name,'text':' '.join((name,item['name'],item['category'],aliases,DESCRIPTIONS.get(name,''),' '.join(x['query']+' '+x['guidance'] for x in memories if name in x['expected'])))})
    return result

def tokens(text):
    text=normalize(text)
    return re.findall(r'[a-z0-9_]+',text)+[text[i:i+2] for i in range(len(text)-1) if re.search(r'[\u4e00-\u9fff]',text[i:i+2])]

def lexical(query,docs):
    terms=set(tokens(query)); bags=[Counter(tokens(d['text'])) for d in docs]
    df=Counter(t for b in bags for t in b)
    ranked=[]
    for d,b in zip(docs,bags):
        score=sum(math.log(1+(len(docs)-df[t]+.5)/(df[t]+.5))*b[t]/(b[t]+1.2) for t in terms if t in b)
        if score:ranked.append((score,d['type_id']))
    return [n for _,n in sorted(ranked,reverse=True)]

@lru_cache(maxsize=128)
def _embedding(query,serialized,python,model,worker,identity):
    payload=json.dumps({'query':query,'documents':json.loads(serialized)},ensure_ascii=False)
    proc=subprocess.run([python,'-X','utf8',worker,model],input=payload,text=True,encoding='utf8',capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if proc.returncode:raise ValueError('embedding worker failed')
    result=json.loads(proc.stdout)
    if not isinstance(result,list) or any(not isinstance(n,str) for n in result):raise ValueError('invalid embedding ranking')
    return result

@lru_cache(maxsize=128)
def _onnx_embedding(query,serialized,model,identity):
    with tempfile.TemporaryDirectory(prefix='anclicker-embedding-') as folder:
        request=Path(folder)/'request.json';result=Path(folder)/'result.json'
        request.write_text(json.dumps({'query':query,'documents':json.loads(serialized)},ensure_ascii=False),encoding='utf8')
        command=[sys.executable,'--capability-embedding-worker'] if getattr(sys,'frozen',False) else [sys.executable,'-X','utf8',str(Path(__file__).with_name('capability_onnx_worker.py'))]
        subprocess.run(command+[model,str(request),str(result)],capture_output=True,timeout=30,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        ranking=json.loads(result.read_text(encoding='utf8'))
        if not isinstance(ranking,list) or any(not isinstance(n,str) for n in ranking):raise ValueError('invalid embedding ranking')
        return ranking

def retrieve(text,baseline,context=None,config=None):
    from models.sentence_contracts import explicit_native_type
    from models.instruction_compiler import python_reference,native_preference
    config=config or {}; query=intent_text(text); memory_enabled=config.get('correction_memory_enabled',True); docs=records(memory_enabled); known={d['type_id'] for d in docs}
    explicit=explicit_native_type(text)
    from models.correction_memory import cases,family
    matched=family(text) if memory_enabled else None
    memories=[x for x in cases() if x['family']==matched] if matched else []
    method='lexical';reason='';ranked=[]
    if explicit or python_reference(text):
        names=[explicit] if explicit else ['运行Python'];method='exact'
    else:
        ranked=lexical(query,docs)
        # Exact aliases and existing single native bindings stay authoritative.
        anchored=[n for n in baseline if n!='运行Python']
        exact=any(word in query for word in ALIASES) or any(normalize(n) in normalize(query) for n in anchored)
        if (not exact or memories) and config.get('embedding_enabled'):
            from models.agent_local import runtime_root
            root=runtime_root().parent
            python=root/config.get('embedding_python','.local/runtimes/training-gpu/venv/Scripts/python.exe')
            model=root/config.get('embedding_model','models/embeddings/bge-small-zh-v1.5')
            worker=Path(__file__).resolve().parents[1]/'tools/capability_embedding_worker.py'
            if context is not None and context.stop_requested:raise InterruptedError('已停止')
            try:
                identity=tuple((f.name,f.stat().st_size,f.stat().st_mtime_ns) for f in sorted(model.glob('*')) if f.is_file() and f.suffix in ('.json','.txt','.safetensors','.onnx'))
                if not identity:raise ValueError('embedding model unavailable')
                serialized=json.dumps(docs,ensure_ascii=False)
                if (model/'model.onnx').is_file():
                    semantic=_onnx_embedding(query,serialized,str(model),identity)
                else:
                    if not python.is_file():raise ValueError('embedding runtime unavailable')
                    semantic=_embedding(query,serialized,str(python),str(model),str(worker),identity)
                # Reciprocal rank fusion. Scores are rankings, never execution confidence.
                scores={}
                for order in (ranked,semantic):
                    for i,name in enumerate(order):
                        if name in known:scores[name]=scores.get(name,0)+1/(60+i+1)
                ranked=sorted(scores,key=lambda n:(-scores[n],n));method='hybrid'
            except (OSError,ValueError,subprocess.SubprocessError):reason='embedding unavailable; lexical fallback'
        if exact:names=list(baseline);method='anchored'
        else:
            # Never enable shell/Python/control-flow merely through a retrieval hit.
            excluded={'运行Python','运行cmd','运行外部文件'}
            flow={i['type_id'] for i in catalog() if i['category']=='流程'}
            extra=[n for n in ranked if n not in excluded|flow][:3]
            names=list(dict.fromkeys(list(baseline)+extra))
        supported=[n for n,description in DESCRIPTIONS.items() if any(len(phrase)>=4 and phrase in query for phrase in description.split())]
        if supported:names=supported
        if native_preference(text) or supported:names=[n for n in names if n!='运行Python']
        from models.conversational_contracts import no_enter
        if no_enter(text):names=[n for n in names if n not in ('按下键盘','按键')]
    if memories and not explicit and not python_reference(text):
        names=list(dict.fromkeys(n for x in memories for n in x['expected']))
    names=[n for n in names if n in known]
    if context is not None:context.metadata.setdefault('capability_retrieval',[]).append({'query':query,'method':method,'baseline':list(baseline),'selected':names,'ranking':ranked[:6],'fallback':reason,'correction_ids':[x['id'] for x in memories],'memory_enabled':memory_enabled})
    return names
