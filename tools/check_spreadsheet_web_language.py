import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
P='E:/测试数据.xlsx';Q='E:/返回结果.xlsx'
source=f'表格“{P}”工作表“数据”的A1:B2';target=f'表格“{Q}”工作表“结果”的C3'
cases=[]
for verb in ['复制到','填入','粘贴到','写入','放到','拷到','粘到']:
 cases.append((f'把{source}{verb}网页 https://example.org 的 CSS #input',['打开网页','打开Excel','读取区域','输入文本']))
for verb in ['写入','写回','存入']:
 cases.append((f'提取当前网页 CSS #answer 的文字{verb}{target}',['提取文本到表格']))
cases.extend([
(f'把{source}复制到网页 https://example.org 的 CSS #input，然后提取网页 CSS #answer 的文字写回同一个表格工作表“结果”的C3',['打开网页','打开Excel','读取区域','输入文本','提取文本到表格']),
(f'把{source}复制到当前网页 CSS “textarea[data-id=entry]”，不要回车',['打开Excel','读取区域','输入文本']),
('把表格复制到网页某处',None),
(f'把表格“{P}”的A1复制到当前网页 CSS #input',None),
(f'把表格“{P}”工作表“数据”的内容复制到当前网页 CSS #input',None),
(f'把{source}复制到网页输入框',['打开Excel','表格填入网页']),
(f'把{source}复制到网页 CSS #input',None),
(f'提取当前网页 CSS #answer 的文字写入表格“{Q}”工作表“结果”的XFE1',None),
(f'把{source}复制到网页 https://example.org CSS #input，然后不要覆盖原表格',None),
(f'把{source}复制到网页 https://example.org CSS #input，然后删除文件',None),
])
rows=[]
for text,expected in cases:
 ctx=ExecutionContext();r=plan_drafts(text,AgentSettings(),ctx);items=r.get('arguments',{}).get('instructions',[])
 passed=(r.get('type')=='message') if expected is None else [i['type_id'] for i in items]==expected
 if expected and items[-1]['type_id']=='输入文本':
  passed=passed and items[-1]['parameters']['pressEnter']=='否' and items[-2]['parameters']['format']=='制表符文本'
 if expected and items[-1]['type_id']=='提取文本到表格':
  passed=passed and items[-1]['parameters']['toCell']=='C3' and items[-1]['parameters']['toSheet']=='结果'
 rows.append({'request':text,'passed':passed,'response':r});print(passed,text)
report={'passed':sum(r['passed'] for r in rows),'total':len(rows),'cases':rows}
(ROOT/'artifacts/debug/spreadsheet-web/language-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
assert all(r['passed'] for r in rows),report
print('LANGUAGE_PASS',len(rows))
