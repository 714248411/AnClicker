"""Tool loop. Browser work runs only in the dedicated Agent bridge."""
import json
import re
from copy import deepcopy
from agent_protocol import (catalog,instruction_schema,make_draft,draft_data,envelope,validate_call)
from agent_provider import ModelClient
from instructions.common.rpa_bridge import RpaBridge
from web_urls import normalize_web_url

class AgentSession:
    def __init__(self, bridge=None):
        self.bridge=bridge or RpaBridge('conversation-agent')
        self.drafts=[]
        self.history=[]
        self.browser_active=False
    def close(self): self.bridge.close()
    def execute(self, name, args, context):
        if context.stop_requested: raise InterruptedError('已停止')
        validate_call(name,args)
        if name=='instructions_search': return catalog(args['query'])
        if name=='instruction_schema': return deepcopy(instruction_schema(args['type_id']))
        if name=='draft_read': return [dict(row=i+1,**draft_data(d)) for i,d in enumerate(self.drafts)]
        if name=='draft_append':
            if len(self.drafts)>=100: raise ValueError('草稿最多 100 行，请先写入或清空')
            draft=make_draft(**args)
            self.drafts.append(draft)
            return {'row':len(self.drafts),'draft':draft_data(draft),'state':'待检查并写入，未执行'}
        if name=='draft_update':
            row=args['row']-1
            if row<0 or row>=len(self.drafts): raise ValueError('草稿行号不存在')
            old=self.drafts[row];parameters=deepcopy(old.parameters);parameters.update(args['parameters'])
            draft=make_draft(old.type_id,parameters,args.get('repeat_count',old.repeat_count),old.note)
            self.drafts[row]=draft
            return {'row':row+1,'draft':draft_data(draft),'state':'已更新草稿，未执行'}
        if name=='browser':
            action=args['action']
            if action=='open':
                url=normalize_web_url(args['url'])
                self.bridge.execute({'id':'openUrl','params':{'url':url,'engine':'Chrome','target':'当前标签页','loginMode':'独立登录(每次全新)','waitType':'加载完成'}},context=context,timeout=45)
                return self.execute('browser',{'action':'view'},context)
            params=dict(args)
            if action=='view':params['action']='observe'
            result=self.bridge.execute({'id':'acAgent','params':params},context=context,timeout=20)['result']
            if not isinstance(result,dict): raise ValueError('浏览器没有返回有效结果')
            self.browser_active=True
            if action=='view':
                result['text']=str(result.get('text',''))[:2500]
                items=result.get('elements',[])
                result['elements']=[{k:e[k] for k in ('ref','tag','type','label') if k in e} for e in items[:35]]
                result['truncated']=len(items)>35
            return result
        raise ValueError('未知工具')

    def run(self, text, settings, context, emit):
        client=ModelClient(settings)
        if re.search('草稿|指令|流程|参数|变量|脚本',text):client.tool_scope='instructions'
        elif self.browser_active or re.search(r'https?://|网页|浏览器|输入框|按钮|搜索框|滚动|页面|链接',text):client.tool_scope='browser'
        else:client.tool_scope='auto'
        # Completed turns only: never retain orphaned native tool messages.
        history=deepcopy(self.history[-4:])+[{'role':'user','content':text}]
        from agent_small_model import simple_browser_task
        local=settings.backend=='compatible' and settings.endpoint.rstrip('/')=='http://127.0.0.1:8766/v1' and settings.model=='anclicker-small' and settings.mode=='json'
        client.local_task=simple_browser_task(text) if local else None
        errors=0
        try:
            for step in range(settings.max_steps):
                if context.stop_requested: raise InterruptedError('已停止')
                emit('status',f'正在思考 · 第 {step+1} 步')
                client.browser_active=self.browser_active;client.draft_count=len(self.drafts)
                response=client.chat(history,context)
                if context.stop_requested: raise InterruptedError('已停止')
                call=response['call']
                if call is not None and client.local_task:
                    from agent_small_model import validate_task_call
                    validate_task_call(client.local_task,call,history,self.browser_active)
                history.append(response['message'])
                if call is None:
                    answer=response['text']
                    self.history=(self.history+[{'role':'user','content':text},{'role':'assistant','content':answer}])[-4:]
                    emit('assistant',answer)
                    return
                emit('tool_start',{'name':call['name'],'arguments':call['arguments']})
                try:
                    result=self.execute(call['name'],call['arguments'],context)
                    value=envelope(call['name'],result)
                    errors=0
                except InterruptedError: raise
                except Exception as error:
                    errors+=1;value=envelope(call['name'],error=error)
                emit('tool_result',value)
                if call['name'].startswith('draft_'):emit('drafts',[draft_data(d) for d in self.drafts])
                history.append(client.tool_message(call,value))
                if value['ok'] and client.local_task and call['name']=='browser' and call['arguments']['action']==client.local_task['action']:
                    action=call['arguments']['action']
                    answer=({'open':'已打开页面：'+str(result.get('title') or result.get('url','')),'view':str(result.get('text',''))[:1000],'type':'已填写：'+str(call['arguments'].get('text','')),'click':'已点击：'+client.local_task.get('label',''),'scroll':'已滚动页面。'}).get(action,'已完成。')
                    self.history=(self.history+[{'role':'user','content':text},{'role':'assistant','content':answer}])[-4:]
                    emit('assistant',answer);return
                if errors>=3: raise ValueError('连续 3 次工具失败，请调整描述后重试')
                # Retain the current user goal and the two latest complete tool exchanges.
                if len(history)>5: history=[{'role':'user','content':text}]+history[-4:]
            emit('assistant','已达到本轮步骤上限。已完成的操作和草稿保留，可继续描述下一步。')
        finally:
            if context.stop_requested:self.close()
