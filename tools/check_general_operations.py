import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext
from models.local_paths import known_folder
label=sys.argv[1]
def step(t,**p):return {'type_id':t,'parameters':p}
def key(k):return step('按下键盘',按键=k)
def wait(n):return step('时间等待',时长=n,单位='秒')
def folder():return step('快速文件操作',操作='打开',源路径=str((known_folder('桌面')/'新建文件夹').resolve()))
cases=[
('把桌面上的新建文件夹打开',[folder()]),
('麻烦打开桌面的新建文件夹',[folder()]),
('打开桌面的新建文件夹，然后等两秒',[folder(),wait(2)]),
('先点击桌面回收站，然后等一秒',['运行Python','时间等待']),
('帮我把桌面上的回收站打开',['运行Python']),
('在桌面上点一下回收站',['运行Python']),
('敲个回车',[key('enter')]),
('按两下回车',[step('按下键盘',按键='enter')]),
('按一下空格键',[key('space')]),
('按一下删除键',[key('delete')]),
('全选一下，然后复制，再粘贴',[key('ctrl+a'),key('ctrl+c'),key('ctrl+v')]),
('撤销一下',[key('ctrl+z')]),
('切到下一个窗口',[key('alt+tab')]),
('鼠标往下滚三格',[step('滚轮滑动',方向='向下',距离=3)]),
('在当前位置点一下右键',[step('鼠标点击',鼠标='右键',次数=1)]),
('输入“打开回收站，然后删除”，不要回车',[step('文本输入',内容='打开回收站，然后删除')]),
('输入“下周交”，不对，改成“明天交”，然后按回车',[step('文本输入',内容='明天交'),key('enter')]),
('打开hao123.com，然后搜索123123',['打开网页','输入文本']),
('打开桌面的新建文件夹，然后打开hao123.com，搜索天气',['快速文件操作','打开网页','输入文本']),
('把“通用操作测试”转成Base64',['运行Python']),
('点一下那个按钮',None),
('打开刚才那个文件',None),
('把当前窗口关掉',None),
('找到那张图点一下',None),
]
if '--unseen' in sys.argv:
 cases=[
 ('劳驾把桌面的新建文件夹打开看看',[folder()]),
 ('请先打开桌面上的“新建文件夹”，然后敲个回车',[folder(),key('enter')]),
 ('先等一秒，再把桌面的新建文件夹打开',[wait(1),folder()]),
 ('先点一下桌面的回收站，再按一下空格键',['运行Python','按下键盘']),
 ('先选中回收站，接着打开桌面的新建文件夹',['运行Python','快速文件操作']),
 ('请按三下空格键',['按下键盘']),
 ('按一下退格键，再按一下Tab',[key('backspace'),key('tab')]),
 ('先撤销一下，然后全选一下，最后复制',[key('ctrl+z'),key('ctrl+a'),key('ctrl+c')]),
 ('等待两秒，然后切换到下一个窗口',[wait(2),key('alt+tab')]),
 ('鼠标往上滚五格，然后向下滚一格',[step('滚轮滑动',方向='向上',距离=5),step('滚轮滑动',方向='向下',距离=1)]),
 ('输入“别打开网页，先点那个”，不要回车',[step('文本输入',内容='别打开网页，先点那个')]),
 ('打开hao123.com，搜索“电脑文件夹”，然后按一下Esc',['打开网页','输入文本','按下键盘']),
 ('点击那个继续按钮',None),
 ('打开这个文件',None),
 ('找到这张图片再点一下',None),
 ('帮我关闭当前窗口',None),
 ]
rows=[]
try:
 for text,expected in cases:
  ctx=ExecutionContext();row={'request':text,'expected':expected,'passed':False}
  try:
   if '--model-version' in sys.argv:
    from unittest.mock import patch
    version=sys.argv[sys.argv.index('--model-version')+1]
    config={'enabled':True,'splitter':f'anclicker-{version}-splitter-q4_0.gguf','converter':f'anclicker-{version}-converter-q4_0.gguf'}
    with patch('models.dual_model.configuration',return_value=config):r=plan_drafts(text,AgentSettings(local_profile='cpu'),ctx)
   else:r=plan_drafts(text,AgentSettings(local_profile='cpu'),ctx)
   row['response']=r
   if expected is None:row['passed']=r.get('type')=='message'
   else:
    items=r.get('arguments',{}).get('instructions',[])
    row['passed']=len(items)==len(expected) and all(a['type_id']==(b if isinstance(b,str) else b['type_id']) and (isinstance(b,str) or all(a['parameters'].get(k)==v for k,v in b['parameters'].items())) for a,b in zip(items,expected))
    if text=='按两下回车':row['passed']=row['passed'] and items[0].get('repeat_count',1)==2
    if text=='请按三下空格键':row['passed']=row['passed'] and items[0].get('repeat_count',1)==3
   if expected is not None and row['passed']:
    for item in items:
     if item['type_id']=='快速文件操作' and '桌面' in text:
      row['passed']=row['passed'] and item['parameters'].get('源路径')==folder()['parameters']['源路径']
     if item['type_id']=='运行Python' and '回收站' in text:
      row['passed']=row['passed'] and 'operate_recycle_bin' in item['parameters'].get('代码','')
   row['metadata']=ctx.metadata
  except Exception as e:row['error']=str(e)
  rows.append(row);print(json.dumps({k:row.get(k) for k in ('request','passed','error')},ensure_ascii=False),flush=True)
  (ROOT/('artifacts/debug/general-operations-fix/'+label+'.json')).write_text(json.dumps({'passed':sum(r['passed'] for r in rows),'total':len(cases),'completed':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
finally:stop_dual()
print('COMPLETE',sum(r['passed'] for r in rows),len(cases),flush=True)
