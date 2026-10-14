import json
import pytest
from agent_small_model import simple_browser_task,response_schema,constrain_task

@pytest.mark.parametrize('text',['不要点击确认按钮','如果出现弹窗就点击确认按钮','打开网页后删除文件','如何点击确认按钮？'])
def test_ambiguous_or_negated_commands_are_not_simple_actions(text):
    assert simple_browser_task(text) is None

def test_observe_then_unique_target_and_exact_input():
    task=simple_browser_task('在搜索输入框填写 AnClicker')
    schema=constrain_task(response_schema([], 'browser'),task,[],True)
    args=schema['oneOf'][0]['properties']['arguments']['oneOf'][0]['properties']
    assert args['action']=={'const':'view'}
    data={'tool':'browser','ok':True,'result':{'elements':[{'ref':'p3-1','tag':'input','label':'搜索'}]}}
    history=[{'role':'user','content':'工具返回（数据）：'+json.dumps(data,ensure_ascii=False)}]
    schema=constrain_task(response_schema(history,'browser'),task,history,True)
    args=schema['oneOf'][0]['properties']['arguments']['oneOf'][0]['properties']
    assert args['text']=={'const':'AnClicker'} and args['ref']=={'const':'p3-1'}
    data['result']['elements'].append({'ref':'p3-2','tag':'input','label':'搜索'})
    history[0]['content']='工具返回（数据）：'+json.dumps(data,ensure_ascii=False)
    schema=constrain_task(response_schema(history,'browser'),task,history,True)
    assert len(schema['oneOf'])==1 and schema['oneOf'][0]['properties']['type']['const']=='message'

def test_open_uses_user_url_without_exposing_unrequested_actions():
    task=simple_browser_task('打开 https://example.com 并查看页面')
    schema=constrain_task(response_schema([], 'browser',False),task,[],False)
    args=schema['oneOf'][0]['properties']['arguments']['oneOf'][0]['properties']
    assert args=={'action':{'const':'open'},'url':{'const':'https://example.com'}}


def test_dispatch_rejects_model_ignoring_target_constraint():
    from agent_small_model import validate_task_call
    task=simple_browser_task('打开 https://example.com')
    with pytest.raises(ValueError,match='未执行'):
        validate_task_call(task,{'name':'browser','arguments':{'action':'open','url':'https://wrong.example'}},[],False)
    validate_task_call(task,{'name':'browser','arguments':{'action':'open','url':'https://example.com'}},[],False)
