import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.dual_model import plan,stop_dual,configuration
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
from models.training.evaluate_v6 import equivalent,step
wait=lambda n:step('时间等待',时长=n,单位='秒')
web=lambda u:step('打开网页',url=u)
type_text=lambda s:step('文本输入',内容=s)
search=lambda s:step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text=s,pressEnter='是',clear='是')
cases=[
('先帮我打开网页，，hao123.com；等两秒，然后在里面搜索123123，最后等三秒',[web('https://hao123.com'),wait(2),search('123123'),wait(3)]),
('我想先上hao123.com，接下来搜一下天气预报，完了等两秒',[web('https://hao123.com'),search('天气预报'),wait(2)]),
('打开网页，地址是hao123.com，然后搜索，123123',[web('https://hao123.com'),search('123123')]),
('hao123.com\n其中搜索\n123123\n等待2秒',[web('https://hao123.com'),search('123123'),wait(2)]),
('打开hao123.com。搜索“先检查，再继续”；等待三秒',[web('https://hao123.com'),search('先检查，再继续'),wait(3)]),
('打开hao123.com，然后在搜索框里输入“123123”，不要提交',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='123123',pressEnter='否',clear='是')]),
('先打开网页，hao123.com，等一下，两秒，再搜索123123',[web('https://hao123.com'),wait(2),search('123123')]),
('帮我等待，三秒，然后输入，“会议改到周五，下午三点”，不要回车',[wait(3),type_text('会议改到周五，下午三点')]),
('输入“今天的材料已经整理好了”，先别提交；等两秒；再按一下回车',[type_text('今天的材料已经整理好了'),wait(2),step('按下键盘',按键='Enter')]),
('先等九秒，不对，改成两秒。接下来输入“收到，谢谢”，不用回车',[wait(2),type_text('收到，谢谢')]),
('帮我打开 example.org；接下来等三秒；随后打开 example.net',[web('https://example.org'),wait(3),web('https://example.net')]),
('先输入“然后等三秒，别删”；再等四秒；接着输入“完成”',[type_text('然后等三秒，别删'),wait(4),type_text('完成')]),
('打开 https://example.org/a?x=1&y=2，然后等三秒',[web('https://example.org/a?x=1&y=2'),wait(3)]),
('先等待2秒！！然后等待3秒？？最后等待1秒',[wait(2),wait(3),wait(1)]),
('请帮我输入“张三：材料已齐；明天再发”，这整句都照着写，然后等一秒',[type_text('张三：材料已齐；明天再发'),wait(1)]),
('复制，“E:/资料/原件.txt”，到，“E:/资料/副本.txt”，原件保留，然后等两秒',[step('快速文件操作',操作='复制',源路径='E:/资料/原件.txt',目标路径='E:/资料/副本.txt'),wait(2)]),
('请打开网页，然后在里面搜索123123',None),
('打开example.org，然后点右边那个按钮',None),
('打开hao123.com，搜索',None),
('先等两秒，输入“你好”，然后等三秒，输入“再见”，最后等一秒',[wait(2),type_text('你好'),wait(3),type_text('再见'),wait(1)])]
if '--additional' in sys.argv:
 cases=[
 ('麻烦先打开网站，网址是www.hao123.com；等一会儿，四秒；在网页中搜索“下周 上海天气”',[web('https://www.hao123.com'),wait(4),search('下周 上海天气')]),
 ('输入，“你好，世界！然后再说”；别回车；等一下，五秒',[type_text('你好，世界！然后再说'),wait(5)]),
 ('hao123.com；搜索，春天；最后暂停两秒',[web('https://hao123.com'),search('春天'),wait(2)]),
 ('打开hao123.com，接下来在搜索框里输入“天气”，先别提交；随后等待四秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='天气',pressEnter='否',clear='是'),wait(4)]),
 ('请先等六秒。随后输入“好了”。最后等待两秒',[wait(6),type_text('好了'),wait(2)]),
 ('打开网页，example.net；暂停，五秒；输入，“下一步，然后继续”',[web('https://example.net'),wait(5),type_text('下一步，然后继续')]),
 ('拷贝，“E:/练习/a.txt”，到，“E:/练习/b.txt”；别动原文件；等一秒',[step('快速文件操作',操作='复制',源路径='E:/练习/a.txt',目标路径='E:/练习/b.txt'),wait(1)]),
 ('先等待三秒，刚说错了，改成一秒；然后打开网页，example.com',[wait(1),web('https://example.com')]),
 ('打开hao123.com；搜索；然后等两秒',None),
 ('先打开example.com；然后点左边那个保存按钮',None)]
if '--plain' in sys.argv:
 cases=[
 ('输入，你好，谢谢，然后等两秒',[type_text('你好，谢谢'),wait(2)]),
 ('等两秒，输入已完成，先不要回车',[wait(2),type_text('已完成')]),
 ('等一下，三秒，再输入，明天交稿，别提交，最后等一秒',[wait(3),type_text('明天交稿'),wait(1)]),
 ('输入：会议改期了；等两秒',[type_text('会议改期了'),wait(2)]),
 ('打开 https://example.org/a!b?q=然后再继续，等待三秒',[web('https://example.org/a!b?q=然后再继续'),wait(3)])]
config={'enabled':True,'splitter':'anclicker-v6_4-splitter-q4_0.gguf','converter':'anclicker-v6_4-converter-q4_0.gguf'} if '--candidate' in sys.argv else None
rows=[];label=sys.argv[1] if len(sys.argv)>1 else 'baseline'
try:
 for text,expected in cases:
  ctx=ExecutionContext();row={'request':text,'expected':expected,'passed':False}
  try:
   response=plan(text,AgentSettings(local_profile='cpu'),ctx,config=config);row['response']=response
   row['passed']=response.get('type')=='message' if expected is None else equivalent(response.get('arguments',{}).get('instructions',[]),expected)
  except Exception as e:row['error']=str(e)
  row['metadata']=ctx.metadata;rows.append(row);print(json.dumps({k:row.get(k) for k in ['request','passed','error']},ensure_ascii=False),flush=True)
  (ROOT/('artifacts/debug/long-sentence-'+label+'.json')).write_text(json.dumps({'config':config or configuration(),'passed':sum(x['passed'] for x in rows),'total':len(cases),'completed':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
finally:stop_dual()
print('COMPLETE',sum(x['passed'] for x in rows),len(rows),flush=True)

if label!='baseline':assert all(x['passed'] for x in rows),'Long sentence regression failed'
