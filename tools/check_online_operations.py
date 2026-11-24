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
img=(ROOT/'resources/animations/startup-fallback.png').as_posix()
key=lambda k:step('按下键盘',按键=k)
cases=[
('打开hao123.com，然后在搜索框里输入“自动化测试”，不要提交，等一秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='自动化测试',pressEnter='否',clear='是'),wait(1)]),
('打开 https://www.selenium.dev/selenium/web/web-form.html，等待两秒',[web('https://www.selenium.dev/selenium/web/web-form.html'),wait(2)]),
('点击网页元素 CSS #submit，然后等两秒',[step('点击元素',selector='#submit',by='CSS选择器'),wait(2)]),
('在网页 CSS #search 输入“测试一下”，不要回车',[step('输入文本',selector='#search',by='CSS选择器',text='测试一下',pressEnter='否')]),
('按一下Ctrl+A，再按Ctrl+C，等两秒，最后按Ctrl+V',[key('ctrl+a'),key('ctrl+c'),wait(2),key('ctrl+v')]),
('先全选，再复制，最后粘贴',[key('ctrl+a'),key('ctrl+c'),key('ctrl+v')]),
('先按Tab，然后敲一下回车，再等两秒',[key('tab'),key('enter'),wait(2)]),
('按一下Esc，等一秒，再按Ctrl+Z',[key('esc'),wait(1),key('ctrl+z')]),
('在鼠标当前位置点一下右键，然后等两秒',[step('鼠标点击',鼠标='右键',次数=1),wait(2)]),
('鼠标当前位置双击左键，再等一秒',[step('鼠标点击',鼠标='左键',次数=2),wait(1)]),
('鼠标点击坐标（100，200），然后等两秒',[step('坐标点击',坐标='100-200',动作='左键单击'),wait(2)]),
('鼠标滚轮向下滚三格，然后向上滚两格',[step('滚轮滑动',方向='向下',距离=3),step('滚轮滑动',方向='向上',距离=2)]),
('输入再见，然后等两秒',[type_text('再见'),wait(2)]),
('输入并列第一，再等一秒',[type_text('并列第一'),wait(1)]),
('输入“第一行；第二行，然后再说”，不要回车，再等一秒',[type_text('第一行；第二行，然后再说'),wait(1)]),
('输入周五，哦不，改成周六，然后等两秒',[type_text('周六'),wait(2)]),
(f'在屏幕上找到图片“{img}”并单击，然后等两秒',[step('图像点击',图像路径=img,动作='左键单击'),wait(2)]),
(f'找到图片“{img}”后双击左键，最后等一秒',[step('图像点击',图像路径=img,动作='左键双击'),wait(1)]),
(f'按图片“{img}”定位并右键单击，再等一秒',[step('图像点击',图像路径=img,动作='右键单击'),wait(1)]),
('找到那个图片然后点一下',None)]
if '--unseen' in sys.argv:
 cases=[
 ('麻烦点一下网页上的 CSS #confirm，随后等四秒',[step('点击元素',selector='#confirm',by='CSS选择器'),wait(4)]),
 ('在网页 CSS #q 填入“请再试一次”，先别回车',[step('输入文本',selector='#q',by='CSS选择器',text='请再试一次',pressEnter='否')]),
 ('打开hao123.com，然后搜索“上海 周末天气”，别提交，最后等四秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='上海 周末天气',pressEnter='否',clear='是'),wait(4)]),
 ('先用键盘按 Ctrl + Shift + S，然后等四秒',[key('ctrl+shift+s'),wait(4)]),
 ('按下Alt+Tab，等待一秒，再按Esc',[key('alt+tab'),wait(1),key('esc')]),
 ('在当前位置用鼠标右键点一下，随后暂停四秒',[step('鼠标点击',鼠标='右键',次数=1),wait(4)]),
 ('双击坐标（318，246），接下来等一秒',[step('坐标点击',坐标='318-246',动作='左键双击'),wait(1)]),
 ('鼠标滚轮向上滚四格，然后向下滚一格',[step('滚轮滑动',方向='向上',距离=4),step('滚轮滑动',方向='向下',距离=1)]),
 ('写上任务结束后再联系，别提交，等三秒',[type_text('任务结束后再联系'),wait(3)]),
 ('输入“周一交稿”，说错了，改成“周三交稿”，然后等两秒',[type_text('周三交稿'),wait(2)]),
 (f'匹配图片“{img}”后右键单击，然后等三秒',[step('图像点击',图像路径=img,动作='右键单击'),wait(3)]),
 (f'照着图片“{img}”定位后双击，接下来等四秒',[step('图像点击',图像路径=img,动作='左键双击'),wait(4)])]
version=sys.argv[sys.argv.index('--model-version')+1] if '--model-version' in sys.argv else 'v6_4'
config={'enabled':True,'splitter':f'anclicker-{version}-splitter-q4_0.gguf','converter':f'anclicker-{version}-converter-q4_0.gguf'} if '--candidate' in sys.argv else None
rows=[];label=sys.argv[1] if len(sys.argv)>1 else 'baseline'
try:
 for text,expected in cases:
  ctx=ExecutionContext();row={'request':text,'expected':expected,'passed':False}
  try:
   response=plan(text,AgentSettings(local_profile='cpu'),ctx,config=config);row['response']=response
   row['passed']=response.get('type')=='message' if expected is None else equivalent(response.get('arguments',{}).get('instructions',[]),expected)
  except Exception as e:row['error']=str(e)
  row['metadata']=ctx.metadata;rows.append(row);print(json.dumps({k:row.get(k) for k in ['request','passed','error']},ensure_ascii=False),flush=True)
  (ROOT/('artifacts/debug/online-operations-'+label+'.json')).write_text(json.dumps({'config':config or configuration(),'passed':sum(x['passed'] for x in rows),'total':len(cases),'completed':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
finally:stop_dual()
print('COMPLETE',sum(x['passed'] for x in rows),len(rows),flush=True)

if label!='baseline':assert all(x['passed'] for x in rows),'Long sentence regression failed'
