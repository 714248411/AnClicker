import sys
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.chinese_planner import split_numbered_steps,primitive_step
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.agent_runtime import AgentSession

def main():
    for text in ('1. 等两秒\n2. 等待三秒\n3. 按回车\n4. 等待0.5秒\n5. 等待一百毫秒','一、等两秒；二、等三秒；三、按回车；四、等待0.5秒；五、等待一百毫秒','第一步：等两秒\n第二步：等待三秒\n第三步：按回车\n第四步：等待0.5秒\n第五步：等待一百毫秒'):
        result=plan_drafts(text,AgentSettings(),ExecutionContext());items=result['arguments']['instructions']
        assert len(items)==5 and items[0]['parameters']['时长']==2 and items[3]['parameters']['时长']==.5
        assert items[4]['parameters']['单位']=='毫秒'
    result=plan_drafts('1. 打开文件“C:/Work/report.txt”\n2. 复制刚才打开的文件到“C:/Backup/report.txt”',AgentSettings(),ExecutionContext())
    assert result['arguments']['instructions'][1]['parameters']['源路径']=='C:/Work/report.txt'
    assert split_numbered_steps('打开 https://example.com/v1.2.3，等待1.5秒') is None
    for text in ('1. 等待1秒\n3. 等待2秒','1. 等待1秒\n1. 等待2秒','1. 等待1秒\n2.'):
        try:split_numbered_steps(text)
        except ValueError:pass
        else:raise AssertionError('Invalid numbered list accepted')
    s=AgentSession()
    with patch('models.draft_planner._plan_single',side_effect=[{'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':[{'type_id':'时间等待','parameters':{'时长':1}}]}},{'type':'message','content':'需要路径'}]):
        s.run('1. 等待1秒\n2. 打开那个文件',AgentSettings(),ExecutionContext(),lambda *a:None)
        assert s.drafts==[],'partial plan leaked'
    s.close()
    print('PASS numbered Chinese/Arabic lists, five ordered steps, durations, decimal/URL exclusion, invalid labels and no partial writes')
if __name__=='__main__':main()
