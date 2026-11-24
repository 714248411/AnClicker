"""Remote role inference using the same semantic contracts as local models."""
import json,re
from models.agent_provider import request_json
from models.conversational_contracts import validate_model_output

def is_local(s):
 return s.backend=='compatible' and s.endpoint.rstrip('/')=='http://127.0.0.1:8766/v1' and s.model=='anclicker-small'

def parse_json(content):
 if not isinstance(content,str):raise ValueError('API 的 JSON 正文为空或类型无效')
 content=content.strip();fence=chr(96)*3
 fenced=re.fullmatch(re.escape(fence)+r'(?:json)?\s*\n?(.*?)\n?'+re.escape(fence),content,re.S|re.I)
 if fenced:content=fenced[1].strip()
 try:return json.loads(content)
 except (TypeError,ValueError):raise ValueError('API 未返回有效 JSON；本次没有生成可执行步骤') from None

def infer_remote(role,messages,schema,settings,context):
 settings.validate();name='anclicker_'+role;prompt=[dict(m) for m in messages]
 contract='\n本次仅返回一个符合此结构的结果：'+json.dumps(schema,ensure_ascii=False,separators=(',',':'))
 contract+=('\n必须调用 '+name+'，将结果放入 result 字段；不要调用其他工具。') if settings.mode=='native' else '\n只返回 JSON，不要添加说明或 Markdown。'
 prompt[0]={**prompt[0],'content':prompt[0]['content']+contract}
 payload={'model':settings.model,'messages':prompt,'stream':False}
 if settings.backend=='ollama':
  path='/api/chat';payload.update(options={'temperature':0,'num_ctx':8192,'num_predict':2000},keep_alive='3m')
 else:path='/chat/completions';payload.update(temperature=0,max_tokens=2000)
 if settings.mode=='native':
  params={'type':'object','properties':{'result':schema},'required':['result'],'additionalProperties':False}
  payload['tools']=[{'type':'function','function':{'name':name,'description':'返回规划结果，不执行操作','parameters':params}}]
  if settings.backend=='compatible':payload.update(tool_choice={'type':'function','function':{'name':name}},parallel_tool_calls=False)
 elif settings.backend=='ollama':payload['format']='json'
 else:payload['response_format']={'type':'json_object'}
 data=request_json(settings.endpoint.rstrip('/')+path,payload,settings,context)
 if not isinstance(data,dict):raise ValueError('API 响应必须是对象')
 if settings.backend=='ollama':
  if data.get('done_reason')=='length':raise ValueError('API 输出被截断，本次未生成完整步骤')
  message=data.get('message',{})
 else:
  choices=data.get('choices') or []
  if not choices:raise ValueError('API 没有返回答复')
  if choices[0].get('finish_reason') in ('length','content_filter'):raise ValueError('API 没有返回完整计划，本次未生成步骤')
  message=choices[0].get('message',{})
 if not isinstance(message,dict):raise ValueError('API 消息格式无效')
 if settings.mode=='native':
  calls=message.get('tool_calls') or []
  if len(calls)!=1:raise ValueError('API 每次必须返回一个规划工具调用')
  function=calls[0].get('function',{})
  if function.get('name')!=name:raise ValueError('API 返回了未请求的工具')
  arguments=function.get('arguments')
  if isinstance(arguments,str):arguments=parse_json(arguments)
  if not isinstance(arguments,dict) or set(arguments)!={'result'}:raise ValueError('API 工具参数必须只包含 result')
  value=arguments['result']
 else:value=parse_json(message.get('content'))
 validate_model_output(value,schema)
 context.metadata.setdefault('dual_model_trace',[]).append({'role':role,'model':settings.model,'transport':settings.backend,'mode':settings.mode,'input':messages[-1]['content'],'output':value})
 return value
