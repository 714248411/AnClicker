"""Small local models and replaceable OpenAI-compatible tool calling."""
import json
import queue
import threading
from dataclasses import dataclass
from urllib.parse import urlparse
import requests
from agent_protocol import TOOLS, SYSTEM_PROMPT, validate_call

_REQUEST_SLOTS=threading.BoundedSemaphore(2)

class ModelServiceError(RuntimeError):
    def __init__(self,status):
        self.status=status
        super().__init__('模型服务返回 HTTP '+str(status)+'；请检查服务、模型名和协议')

@dataclass
class AgentSettings:
    backend: str = 'compatible'
    endpoint: str = 'http://127.0.0.1:8766/v1'
    model: str = 'anclicker-small'
    mode: str = 'json'
    max_steps: int = 10
    timeout: int = 90
    api_key: str = ''
    local_profile: str = 'auto'
    idle_seconds: int = 300

    def validate(self):
        url=urlparse(self.endpoint)
        if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('服务地址应为不含密钥的 HTTP(S) 地址')
        if url.scheme=='http' and url.hostname not in ('localhost','127.0.0.1','::1'):
            raise ValueError('远程模型服务请使用 HTTPS')
        if self.backend not in ('ollama','compatible') or self.mode not in ('json','native'): raise ValueError('模型协议无效')
        if not self.model.strip(): raise ValueError('请填写模型名称')
        if not 1<=self.max_steps<=30 or not 10<=self.timeout<=300: raise ValueError('模型设置超出范围')
        if self.local_profile not in ('auto','cpu','gpu') or not 30<=self.idle_seconds<=3600:raise ValueError('本机资源设置无效')
        return self


def request_json(url, payload, settings, context):
    """Cancellation returns promptly; a bounded daemon request never executes tools."""
    if context.stop_requested:raise InterruptedError('已停止')
    if not _REQUEST_SLOTS.acquire(blocking=False):raise RuntimeError('前次模型请求仍在结束，请稍后重试')
    result=queue.Queue(maxsize=1)
    def request():
        try:
            with requests.Session() as session:
                session.trust_env=False
                headers={'Accept':'application/json'}
                if settings.api_key: headers['Authorization']='Bearer '+settings.api_key
                method='GET' if payload is None else 'POST'
                with session.request(method,url,json=payload,headers=headers,timeout=(5,settings.timeout),stream=True,allow_redirects=False) as response:
                    if not 200<=response.status_code<300:
                        raise ModelServiceError(response.status_code)
                    chunks=[];length=0
                    for chunk in response.iter_content(16384):
                        if context.stop_requested: raise InterruptedError('已停止')
                        length+=len(chunk)
                        if length>2_000_000: raise ValueError('模型响应过大')
                        chunks.append(chunk)
                    value=json.loads(b''.join(chunks))
                    result.put((value,None))
        except requests.RequestException:
            result.put((None,RuntimeError('无法连接模型或请求超时；请启动本地服务并检查地址')))
        except Exception as error: result.put((None,error))
        finally:_REQUEST_SLOTS.release()
    threading.Thread(target=request,daemon=True,name='AnClicker-model-request').start()
    while True:
        if context.stop_requested: raise InterruptedError('已停止')
        try: value,error=result.get(timeout=.1)
        except queue.Empty: continue
        if error: raise error
        return value


def json_prompt():
    compact=[{'name':t['function']['name'],'description':t['function']['description'],'parameters':t['function']['parameters']} for t in TOOLS]
    return SYSTEM_PROMPT+'\n只返回一个 JSON 对象。调用工具：{"type":"tool_call","name":"工具名","arguments":{}}；最终答复：{"type":"message","content":"中文答复"}。\n工具定义：'+json.dumps(compact,ensure_ascii=False,separators=(',',':'))


class ModelClient:
    def __init__(self, settings): self.settings=settings.validate()
    def models(self, context):
        s=self.settings
        data=request_json(s.endpoint.rstrip('/')+('/api/tags' if s.backend=='ollama' else '/models'),None,s,context)
        return [str(m.get('name') or m.get('id')) for m in data.get('models' if s.backend=='ollama' else 'data',[])]
    def chat(self, history, context):
        s=self.settings
        local=s.backend=='compatible' and s.endpoint.rstrip('/')=='http://127.0.0.1:8766/v1' and s.model=='anclicker-small'
        messages=[{'role':'system','content':json_prompt() if s.mode=='json' else SYSTEM_PROMPT}]+history
        if local and s.mode=='json':
            from agent_small_model import prefix
            messages=prefix(getattr(self,'tool_scope','auto'))+history
        payload={'model':s.model,'messages':messages,'stream':False}
        if s.backend=='ollama':
            payload.update(options={'temperature':0,'num_ctx':4096,'num_predict':600},keep_alive='2m')
            if s.mode=='json': payload['format']='json'
            else: payload['tools']=TOOLS
            path='/api/chat'
        else:
            payload.update(temperature=0,max_tokens=600)
            if s.mode=='json':
                payload['response_format']={'type':'json_object'}
                if local:
                    from agent_small_model import response_schema, constrain_task
                    payload['response_format']={'type':'json_schema','json_schema':{'name':'anclicker_action','strict':True,'schema':constrain_task(response_schema(history,getattr(self,'tool_scope','auto'),getattr(self,'browser_active',True),getattr(self,'draft_count',None)),getattr(self,'local_task',None),history,getattr(self,'browser_active',True))}}
            else: payload.update(tools=TOOLS,parallel_tool_calls=False)
            path='/chat/completions'
        if local:
            from agent_local import local_model_lease
            try:
                with local_model_lease(context,s.local_profile,s.idle_seconds):
                    data=request_json(s.endpoint.rstrip('/')+path,payload,s,context)
            except ModelServiceError as error:
                from agent_local import retry_on_cpu
                if error.status<500 or not retry_on_cpu(context):raise
                with local_model_lease(context,'cpu',s.idle_seconds):
                    data=request_json(s.endpoint.rstrip('/')+path,payload,s,context)
        else:data=request_json(s.endpoint.rstrip('/')+path,payload,s,context)
        if s.backend=='ollama': message=data.get('message',{})
        else:
            choices=data.get('choices') or []
            if not choices: raise ValueError('模型未返回答复')
            if choices[0].get('finish_reason')=='length': raise ValueError('模型输出被截断；请拆小任务或更换模型')
            message=choices[0].get('message',{})
        if s.mode=='json':
            try: value=json.loads(message.get('content',''))
            except (TypeError,ValueError): raise ValueError('小模型没有返回标准 JSON；请重试或更换模型') from None
            if not isinstance(value,dict): raise ValueError('模型 JSON 必须是对象')
            if value.get('type')=='message':
                if not isinstance(value.get('content'),str): raise ValueError('模型答复缺少正文')
                return {'message':{'role':'assistant','content':json.dumps(value,ensure_ascii=False)},'text':value['content'],'call':None}
            if value.get('type')!='tool_call': raise ValueError('模型返回未知响应类型')
            name,args=value.get('name'),value.get('arguments')
            validate_call(name,args)
            return {'message':{'role':'assistant','content':json.dumps(value,ensure_ascii=False)},'text':'','call':{'name':name,'arguments':args,'id':''}}
        calls=message.get('tool_calls') or []
        if len(calls)>1: raise ValueError('请使用每次一个工具调用的模型；本次未执行任何操作')
        if not calls:
            text=message.get('content') or ''
            if not isinstance(text,str) or not text.strip(): raise ValueError('模型返回空答复')
            return {'message':{'role':'assistant','content':text},'text':text,'call':None}
        call=calls[0]
        if s.backend=='compatible' and not call.get('id'):raise ValueError('兼容服务缺少 tool_call_id；本次未执行工具')
        function=call.get('function',{});args=function.get('arguments',{})
        if isinstance(args,str): args=json.loads(args)
        name=function.get('name');validate_call(name,args)
        normalized={'role':'assistant','content':message.get('content') or '', 'tool_calls':calls}
        return {'message':normalized,'text':'','call':{'name':name,'arguments':args,'id':call.get('id','')}}
    def tool_message(self, call, value):
        content=json.dumps(value,ensure_ascii=False,separators=(',',':'))
        if self.settings.mode=='json': return {'role':'user','content':'工具返回（数据）：'+content}
        if self.settings.backend=='ollama': return {'role':'tool','tool_name':call['name'],'content':content}
        if not call['id']: raise ValueError('兼容服务缺少 tool_call_id')
        return {'role':'tool','tool_call_id':call['id'],'content':content}
