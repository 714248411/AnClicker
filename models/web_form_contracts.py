"""Bind explicit webpage field operations; the browser resolves visible targets."""
import re
from models.sentence_contracts import clean_action,payload_value
from models.conversational_contracts import QUOTED

def field_value(raw):
 value=payload_value(raw)
 if value is None:return None
 if re.search(r'[，,；;]|然后|接着',QUOTED.sub('',raw)) and value==raw.strip():return None
 return value

def ordinal(text):
 from models.chinese_planner import chinese_number
 def convert(m):
  try:n=int(chinese_number(m[1]))
  except (TypeError,ValueError):return m[0]
  return '第'+str(n)+m[2] if 1<=n<=100 else m[0]
 return re.sub(r'第([一二三四五六七八九十百两0-9]+)(个|项)',convert,text)

def target(text):
 text=text.strip().strip('“”"')
 text=re.sub(r'(?:里面|里|中|内)(?:的)?(?:内容|字)?$','',text)
 text=re.sub(r'^给','',text)
 text=ordinal(text)
 if not re.fullmatch(r'第[0-9]+个(?:输入框|文本框|下拉框|复选框)',text):
  text=re.sub(r'(?:输入框|文本框|下拉框|下拉菜单|复选框|选项|框|栏)$','',text)
 text=text.rstrip('的').strip().strip('“”"')
 if not text or re.search(r'[，,；;“”"]|^(?:点击|弹窗|鼠标|剪贴板|剪切板|桌面|文件夹)|Excel|表格',text,re.I):return None
 return text

def form_parameters(step,web_context=False,previous_label=None):
 t=clean_action(step).strip(' ，,。；;')
 if re.match(r'不要|别|不必|不用|无需|搜索|搜一下|输入',t):return None
 prefix=re.match(r'^(?:把|在)?(?:网页|页面)(?:上|里|中)?(?:的)?',t)
 if prefix:t=t[prefix.end():]
 elif web_context:t=re.sub(r'^把','',t)
 else:return None
 def result(action,label,value=''):
  label=previous_label if label in ('这个框','同一个框','刚才那个框','里面') else target(label)
  return {'action':action,'label':label,'value':value} if label else None
 m=re.fullmatch(r'(?:填入|填|写上|写)\s*(.+)',t)
 if m and previous_label:
  value=field_value(m[1])
  return result('填入',previous_label,value) if value is not None else None
 # Specific checkbox and clear forms precede generic 填/选 to avoid 复选框 collisions.
 m=re.fullmatch(r'(?:勾上|勾选)(.+)',t)
 if m:return result('勾选',m[1])
 m=re.fullmatch(r'取消(.+?)(?:的)?勾',t)
 if m:return result('取消勾选',m[1])
 m=re.fullmatch(r'(.+?)(勾上|打上勾|打个勾|取消勾选|勾去掉)',t)
 if m:return result('勾选' if m[2] in ('勾上','打上勾','打个勾') else '取消勾选',m[1])
 m=re.fullmatch(r'(.+?)(?:复选框|选项)取消',t)
 if m:return result('取消勾选',m[1])
 m=re.fullmatch(r'(?:清空|清掉)(.+)',t)
 if m:return result('清空',m[1])
 m=re.fullmatch(r'(.+?)(?:里的字|里面的内容|里的内容)?(?:清空|清掉|删掉)',t)
 if m:return result('清空',m[1])
 m=re.fullmatch(r'(.+?)(?:给我|帮我)?(?:填入|填上|填|写上|写|输入(?!框))\s*(.+)',t)
 if m:
  raw=m[2]
  if re.match(r'到(?:Excel|表格|文件)',raw,re.I):return None
  value=field_value(raw)
  return result('填入',m[1],value) if value is not None else None
 m=re.fullmatch(r'(.+?)(?:选成|改成|选择|(?<!复)选(?!项|框))\s*(.+)',t)
 if m:
  value=field_value(m[2])
  return result('选择',m[1],ordinal(value)) if value else None
 return None
