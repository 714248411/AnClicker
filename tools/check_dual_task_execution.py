import sys,json,tempfile,copy,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.training.dual_task_tuning import C,plan,instruction,execute_request
cases=[]
for n in [1,3,10,20]:
 lab=Path(tempfile.mkdtemp(prefix='executor-check-',dir=C/'labs')) if (C/'labs').exists() else None
 if lab is None:
  (C/'labs').mkdir();lab=Path(tempfile.mkdtemp(prefix='executor-check-',dir=C/'labs'))
 a=plan('新建文件夹',n,'记录','中文内容');request={'expected':a,'instruction':instruction(a),'desktop':str(lab/'Desktop')}
 result=execute_request(request);assert result['file_count']==n
 before={str(x):x.read_bytes() for x in (lab/'Desktop'/'新建文件夹').iterdir()}
 try:execute_request(request)
 except FileExistsError:pass
 else:raise AssertionError('Repeated execution should not overwrite')
 assert before=={str(x):x.read_bytes() for x in (lab/'Desktop'/'新建文件夹').iterdir()}
 bad=copy.deepcopy(request);bad['desktop']=str(lab/'BadDesktop');bad['instruction']=instruction(plan('新建文件夹',n+1,'记录','中文内容'))
 try:execute_request(bad)
 except AssertionError:pass
 else:raise AssertionError('Wrong count accepted')
 assert not Path(bad['desktop']).exists()
 cases.append(result)
(C/'executor-selfcheck.json').write_text(json.dumps({'passed':True,'counts':[1,3,10,20],'negative_count_blocked':True,'overwrite_blocked':True,'model_generated':False,'cases':cases},ensure_ascii=False,indent=2),encoding='utf8')
print('PASS actual registered executor, exact file counts/content, wrong-count rejection, no overwrite. These are harness checks, not model scores.')
