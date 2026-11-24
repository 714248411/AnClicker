"""Verify browser outcomes from the same RPA browser that executed the commands."""
import time
from urllib.parse import urlsplit, parse_qs
from anclicker.execution import actions
from anclicker.platform.rpa_bridge import get_bridge
from models.web_contracts import SEARCH_FIELDS

def web_check(draft):
    p=draft.parameters
    if draft.type_id=='按名称操作网页表单':return {'kind':'web_form',**p}
    if draft.type_id=='滚动网页到指定位置':return {'kind':'web_scroll','position':p.get('position','中间')}
    if draft.type_id=='打开网页' and p.get('url'):return {'kind':'web_open','url':p['url']}
    if draft.type_id=='输入文本' and p.get('pressEnter')=='是' and p.get('selector') in set(SEARCH_FIELDS.values()) and p.get('clear')!='否' and not p.get('textVariable'):
        return {'kind':'web_search','query':p.get('text','')}
    return None

def matches(check,state):
    actual=urlsplit(state.get('url',''))
    ready=state.get('readyState')
    allowed=('interactive','complete')
    if state.get('error') or actual.scheme not in ('http','https') or ready not in allowed:return False
    if check['kind']=='web_form':return state.get('verified') is True and state.get('label')==check['label'] and state.get('action')==check['action']
    if check['kind']=='web_open':
        if ready=='interactive' and not (state.get('title') and (state.get('clickableCount',0)>0 or state.get('inputCount',0)>0)):return False
        expected=urlsplit(check['url'])
        same_host=actual.netloc.lower()==expected.netloc.lower()
        # hao123 navigation is observed to redirect its bare host to www.
        if expected.hostname=='hao123.com' and actual.hostname=='www.hao123.com' and expected.port==actual.port:same_host=True
        return same_host and (actual.path or '/').rstrip('/')==(expected.path or '/').rstrip('/') and actual.query==expected.query and actual.fragment==expected.fragment
    if check['kind']=='web_scroll':
        ratio={'顶部':0,'中间':.5,'底部':1}.get(check.get('position'))
        y,maximum=state.get('y'),state.get('maxY')
        return ratio is not None and all(type(v) in (int,float) for v in (y,maximum)) and maximum>=0 and abs(y-maximum*ratio)<=2
    queries=parse_qs(actual.query)
    terms=[queries[key] for key in ('wd','word') if key in queries]
    return actual.hostname in ('www.baidu.com','baidu.com') and actual.path=='/s' and bool(terms) and all(term==[check['query']] for term in terms)

def web_evidence(check,context):
    check=dict(check)
    for key in ('url','query','label','value'):
        if key in check:check[key]=actions.substitute_variables(context,check[key])
    deadline=time.monotonic()+15;state={}
    while True:
        if context.stop_requested:raise InterruptedError('已停止')
        state=get_bridge().execute({'id':'formLabelState' if check['kind']=='web_form' else 'pageScrollState' if check['kind']=='web_scroll' else 'diagnosePage','params':{k:check[k] for k in ('action','label','value') if k in check} if check['kind']=='web_form' else {}},context=context,timeout=10).get('result') or {}
        valid=matches(check,state)
        if valid and check['kind']=='web_search':
            try:
                bridge=get_bridge()
                query=bridge.execute({'id':'getText','params':{'selector':'textarea#chat-textarea, input[name="wd"], textarea[name="wd"]','by':'CSS选择器','varName':'_verify_query'}},context=context,timeout=10).get('result')
                results=bridge.execute({'id':'getText','params':{'selector':'#content_left','by':'CSS选择器','varName':'_verify_results'}},context=context,timeout=10).get('result')
                valid=query==check['query'] and isinstance(results,str) and bool(results.strip())
                state['search_query']=query;state['results_present']=bool(results and str(results).strip())
            except Exception as error:
                if context.stop_requested:raise InterruptedError('已停止')
                state['verification_error']=str(error);valid=False
        if valid or time.monotonic()>=deadline:break
        if not actions.wait_interruptibly(context,.25):raise InterruptedError('已停止')
    text=('实际网页：'+str(state.get('url',''))+'；标题：'+str(state.get('title','')))
    if check['kind']=='web_scroll':text+='；滚动位置：'+str(state.get('y'))+'/'+str(state.get('maxY'))+' 像素（目标：'+check['position']+'）'
    return {'verified':valid,'method':'browser_state','text':text,'expected_text':[check.get('url',check.get('query',check.get('position','')))], 'page':state,'error':'' if valid else '实际网页状态未达到目标导航、搜索或滚动位置'}
