"""Tool loop. Browser work runs only in the dedicated Agent bridge."""
import json
import re
from copy import deepcopy
from anclicker.domain.agent_protocol import catalog, instruction_schema, make_draft, draft_data, envelope, validate_call
from models.agent_provider import ModelClient
from models.system_actions import file_action, parse_file_task, parse_verify_task
from models.screen_verifier import verify_screen
from models.command_reference import search_commands
from models.draft_verification import verify_plan
from uuid import uuid4
from models.workflow_ast import from_drafts,to_drafts,apply_patch
from models.chinese_planner import split_numbered_steps
from anclicker.platform.rpa_bridge import RpaBridge
from anclicker.platform.crawl4ai_bridge import crawl_page
from anclicker.domain.web_urls import normalize_web_url

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'plan_drafts': ('from', 'models.draft_planner', ('plan_drafts',), 0),
    'simple_browser_task': ('from', 'models.agent_small_model', ('simple_browser_task',), 0),
    'validate_task_call': ('from', 'models.agent_small_model', ('validate_task_call',), 0),
})


class AgentSession:
    def __init__(self, bridge=None):
        self.bridge=bridge or RpaBridge('conversation-agent')
        self.drafts=[]
        self.history=[]
        self.pending_plan_text=""
        self.pending_sheet_target=None
        self.browser_active=False
        self.pending_verification=None
        self._workflow_ast=None
    def workflow_snapshot(self):
        current=[draft_data(d) for d in self.drafts]
        if self._workflow_ast is None or [draft_data(d) for d in to_drafts(self._workflow_ast)]!=current:
            revision=0 if self._workflow_ast is None else self._workflow_ast["revision"]+1
            self._workflow_ast=from_drafts(self.drafts,revision)
        return deepcopy(self._workflow_ast)
    def import_workflow_ast(self,ast):
        prepared=to_drafts(ast);revision=self.workflow_snapshot()['revision']+1
        imported=deepcopy(ast);imported['revision']=revision
        self.drafts=prepared;self._workflow_ast=imported
    def apply_workflow_patch(self,patch):
        merged=apply_patch(self.workflow_snapshot(),patch)
        prepared=to_drafts(merged)
        self.drafts=prepared;self._workflow_ast=merged
        return deepcopy(merged)
    def close(self): self.bridge.close()
    def execute(self, name, args, context):
        if context.stop_requested: raise InterruptedError('已停止')
        validate_call(name,args)
        if name=='cmd_reference':return search_commands(args['query'])
        if name=='system_file':return file_action(context,**args)
        if name=='verify_screen':return verify_screen(context,**args)
        if name=='instructions_search': return catalog(args['query'])
        if name=='instruction_schema': return deepcopy(instruction_schema(args['type_id']))
        if name=='workflow_read':return self.workflow_snapshot()
        if name=='workflow_patch':
            if self.pending_verification:raise ValueError('请先处理待确认的核验流程')
            return self.apply_workflow_patch(args)
        if name=='draft_read': return [dict(row=i+1,**draft_data(d)) for i,d in enumerate(self.drafts)]
        if name=='draft_append_batch':
            if len(self.drafts)+len(args['instructions'])>100:raise ValueError('草稿最多 100 行，请先写入或清空')
            prepared=[make_draft(**item) for item in args['instructions']]
            first=len(self.drafts)+1
            self.drafts.extend(prepared)
            return {'rows':list(range(first,first+len(prepared))), 'count':len(prepared), 'state':'已生成可编辑草稿，未执行'}
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
        if name=='crawl_page':
            return crawl_page(context=context, **dict({'max_chars':8000}, **args))
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

    def resolve_verification(self, token, accept, context):
        pending=self.pending_verification
        if not pending or pending['id']!=token:raise ValueError('核验确认已失效')
        self.pending_verification=None
        if not accept:return {'accepted':False}
        items=deepcopy(pending['instructions'])
        for item in items:item['note']='[核验失败] '+pending['reason']+'；'+item.get('note','')
        result=self.execute('draft_append_batch',{'instructions':items},context)
        return {'accepted':True,**result}

    def run_draft_plan(self,text,settings,context,emit):
        if self.pending_verification:raise ValueError('请先处理核验失败流程的保留提示')
        plan_drafts = _module_imports.load('plan_drafts')
        emit('status','正在拆分任务并生成单步骤草稿…')
        planning_text=(self.pending_plan_text+"\n用户补充："+text) if self.pending_plan_text else text
        context.metadata["workflow_ast"]=self.workflow_snapshot()
        context.metadata["pending_sheet_target"]=self.pending_sheet_target
        response=plan_drafts(planning_text,settings,context,self.drafts)
        if context.stop_requested:raise InterruptedError('已停止')
        if response['type']=='message':
            self.pending_sheet_target=context.metadata.get('pending_sheet_target')
            self.pending_plan_text=planning_text[-12000:]
            emit('assistant',response['content']);return
        self.pending_sheet_target=None
        name,args=response['name'],response['arguments']
        if name=='workflow_patch':
            self.apply_workflow_patch(args);self.pending_plan_text=''
            emit('drafts',[draft_data(d) for d in self.drafts])
            emit('assistant','已合并流程编辑补丁，草稿共 '+str(len(self.drafts))+' 步。修改后的流程尚未试运行。')
            return
        if name not in ('draft_append_batch','draft_update'):raise ValueError('草稿模式不允许直接执行操作')
        if settings.verify_before_draft:
            if name=='draft_update':
                emit('assistant','请先在草稿中直接编辑已有步骤；核验模式用于新建流程。');return
            if len(self.drafts)+len(args['instructions'])>100:raise ValueError('草稿最多 100 行，请先写入或清空')
            outcome=verify_plan(planning_text,args['instructions'],settings,context,emit)
            self.pending_plan_text=''
            if not outcome['passed']:
                self.pending_verification={'id':uuid4().hex,**outcome}
                emit('verification_failed',deepcopy(self.pending_verification));return
            result=self.execute(name,{'instructions':outcome['instructions']},context)
            emit('drafts',[draft_data(d) for d in self.drafts])
            emit('assistant','任务结果核验通过，已自动加入 '+str(result['count'])+' 条可编辑草稿。试运行已执行。依据：'+outcome['reason'])
            return
        emit('tool_start',{'name':name,'arguments':args})
        try:
            result=self.execute(name,args,context)
        except Exception as error:
            emit('tool_result',envelope(name,error=error));raise
        self.pending_plan_text=''
        emit('tool_result',envelope(name,result))
        emit('drafts',[draft_data(d) for d in self.drafts])
        emit('assistant',('已拆分为 '+str(result['count'])+' 个单步骤' if name=='draft_append_batch' else '已修改指定步骤')+'，已放入可编辑草稿，尚未执行。')

    def run(self, text, settings, context, emit):
        quick=parse_file_task(text)
        if settings.draft_only or split_numbered_steps(text) is not None:
            return self.run_draft_plan(text,settings,context,emit)
        verification=parse_verify_task(text)
        if verification:
            emit('tool_start',{'name':'verify_screen','arguments':verification})
            result=self.execute('verify_screen',verification,context)
            emit('tool_result',envelope('verify_screen',result))
            emit('assistant','截图 OCR 核验通过：预期文字全部出现。' if result['verified'] else '截图 OCR 未确认：'+str(result.get('missing',result.get('error','未知原因'))))
            return
        if quick:
            emit('tool_start',{'name':'system_file','arguments':quick})
            result=self.execute('system_file',quick,context)
            emit('tool_result',envelope('system_file',result))
            emit('assistant','复制完成，SHA-256 一致。' if quick['action']=='copy' else ('已打开目标文件夹，路径与截图 OCR 已核验。' if result.get('verified') else '已请求打开；'+str(result.get('visual_verification',{}).get('error') or '尚未确认窗口内容。')))
            return
        client=ModelClient(settings)
        if re.search('文件|复制|拷贝|截图|核验|检查.*文字',text):client.tool_scope='system'
        elif re.search('草稿|指令|流程|参数|变量|脚本',text):client.tool_scope='instructions'
        elif self.browser_active or re.search(r'https?://|抓取|提取|正文|Markdown|网页|浏览器|输入框|按钮|搜索框|滚动|页面|链接',text):client.tool_scope='browser'
        else:client.tool_scope='auto'
        # Completed turns only: never retain orphaned native tool messages.
        history=deepcopy(self.history[-4:])+[{'role':'user','content':text}]
        simple_browser_task = _module_imports.load('simple_browser_task')
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
                    validate_task_call = _module_imports.load('validate_task_call')
                    validate_task_call(client.local_task,call,history,self.browser_active)
                history.append(response['message'])
                if call is None:
                    answer=response['text']
                    verification=context.metadata.get('agent_verification')
                    if verification and not verification.get('verified'):answer='截图 OCR 核验未通过，任务尚未确认。缺失文字或错误：'+str(verification.get('missing',verification.get('error','未知原因')))
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
