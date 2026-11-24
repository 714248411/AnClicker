from models.dual_model import conversion_schema,validate_conversion
from models.draft_planner import candidate_types
from models.conversational_contracts import clarification,no_enter,duration
for t in ['输入“等待十秒”','写上“复制文件”','输入“如果下雨”']:
 assert candidate_types(t)==['文本输入'],(t,candidate_types(t))
assert clarification('输入“如果下雨就不去了”') is None
assert duration('等八秒，不对，改为四秒')=={'时长':4,'单位':'秒'}
for t in ['先别按回车','不要敲回车','不提交']:
 assert no_enter(t)
 try:validate_conversion(t,{'type_id':'按下键盘','parameters':{'按键':'Enter'}})
 except ValueError:pass
 else:raise AssertionError('negative instruction accepted')
s=conversion_schema('把“E:/原件.txt”拷一份到“E:/副本.txt”', ['快速文件操作'])['oneOf'][0]['properties']['parameters']
assert '目标路径' in s['required'] and s['properties']['目标路径']['const']=='E:/副本.txt'
assert clarification('点右边那个按钮') and clarification('把这个发给他')
print('PASS quoted payload isolation, correction values, negation veto, copy destination and missing context')

from models.conversational_contracts import edit_requests,normalize_edit,validate_model_output
from models.workflow_edit import edit_schema
from models.workflow_ast import from_drafts
from anclicker.domain.agent_protocol import make_draft
assert edit_requests('第2步改成7秒，然后删除第3步')==['第2步改成7秒','删除第3步']
assert len(edit_requests('把第2步文字改成“然后删除第3步”'))==1
assert normalize_edit('第三步不要了，去掉吧')=='删除第3步'
ast=from_drafts([make_draft('时间等待',{'时长':2}),make_draft('文本输入',{'内容':'保留'})],8)
schema=edit_schema(ast,['时间等待'],'把第1步改成7秒')
for bad in [{'base_revision':8,'operations':[{'op':'delete','target':'n1'}]},{'base_revision':8,'operations':[{'op':'update','target':'n1','parameters':{'时长':7}},{'op':'delete','target':'n1'}]},{'base_revision':8,'operations':[{'op':'update','target':'n1','parameters':{'时长':8}}]}]:
 try:validate_model_output(bad,schema)
 except ValueError:pass
 else:raise AssertionError('unrequested edit accepted')
validate_model_output({'base_revision':8,'operations':[{'op':'update','target':'n1','parameters':{'时长':7}}]},schema)
print('PASS literal-preserving edit normalization, explicit edit splitting and no extra operations')
