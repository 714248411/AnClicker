"""Assemble v1.7.1 only after CUDA training and exact real-inference acceptance."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/release/v1.7.1'
DIST=ROOT/'artifacts/dist/v1.7.1/AnClicker'
MODELS={role:'anclicker-v6-'+role+'-q4_0.gguf' for role in ('splitter','converter')}
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 evaluation=json.loads((ROOT/'models/anclicker-v6/evaluation.json').read_text(encoding='utf8'))
 assert evaluation['passed']==evaluation['total'] and evaluation['total']>=15,'Real inference acceptance is incomplete'
 model_records={}
 for role,name in MODELS.items():
  report=json.loads((ROOT/('models/anclicker-v6-'+role)/'training-report.json').read_text(encoding='utf8'))
  assert report['device']=='cuda' and report['after_loss']<report['before_loss'],'GPU training not accepted'
  path=ROOT/'models'/name
  with path.open('rb') as stream:assert stream.read(4)==b'GGUF'
  assert evaluation['model_sha256'][role]==digest(path),'Evaluated weights differ from packaged weights'
  model_records[role]={'file':name,'sha256':digest(path),'steps':report['steps'],'before_loss':report['before_loss'],'after_loss':report['after_loss'],'device':report['device']}
 assert (DIST/'AnClicker.exe').is_file() and not (DIST/'data').exists()
 files=sorted(p for p in DIST.rglob('*') if p.is_file())
 assert not any(p.suffix=='.gguf' for p in files)
 notes=(ROOT/'CHANGELOG.md').read_text(encoding='utf8').split('## v1.7.0',1)[0]
 notes+='\n完整程序包，请完整解压后运行 AnClicker.exe。公开版附带 v6 拆句与指令转换两个小模型。\n'
 notes+=f"\n真实模型推理验收：{evaluation['passed']}/{evaluation['total']}，检查指令类型、参数与 AST 编辑结果；该评分不代表所有自然语言任务或桌面执行均已验证。\n"
 BASE.mkdir(parents=True,exist_ok=True)
 (BASE/'RELEASE_NOTES.md').write_text(notes,encoding='utf8')
 (BASE/'PRIVATE_RELEASE_NOTES.md').write_text(notes+'\nAPI 主程序包不附带模型，可连接外部接口或添加已有 GGUF。\n',encoding='utf8')
 assets=[]
 with zipfile.ZipFile(ROOT/'artifacts/release/public/AnClicker-v1.6.3-win.zip') as previous:
  extras=[i for i in previous.infolist() if not i.is_dir() and (i.filename.startswith(('AnClicker/models/llama-cpu/','AnClicker/models/llama-vulkan/','AnClicker/models/LICENSE-')))]
  for scope,name,with_models in [('public','AnClicker-v1.7.1-win.zip',True),('private','AnClicker-v1.7.1-api-win-x64.zip',False)]:
   target=BASE/scope/name;target.parent.mkdir(parents=True,exist_ok=True)
   assert not target.exists(),'Existing artifact is preserved; choose a new staging directory to rebuild'
   partial=target.with_suffix('.zip.partial')
   with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
    for path in files:output.write(path,'AnClicker/'+path.relative_to(DIST).as_posix())
    for entry in extras:
     with previous.open(entry) as source,output.open(entry.filename,'w',force_zip64=True) as destination:shutil.copyfileobj(source,destination,1024*1024)
    if with_models:
     for model in MODELS.values():output.write(ROOT/'models'/model,'AnClicker/models/'+model)
     output.writestr('AnClicker/models/active_model.json',json.dumps({'file':MODELS['converter'],'name':'AnClicker v6 指令模型'},ensure_ascii=False))
    output.writestr('AnClicker/models/dual_model.json',json.dumps({'enabled':with_models,**MODELS}))
    output.writestr('AnClicker/models/bundle-manifest.json',json.dumps({'version':'v1.7.1','models':model_records if with_models else {}},indent=2))
    output.writestr('MODEL-VALIDATION.json',json.dumps({'passed':evaluation['passed'],'total':evaluation['total'],'scope':evaluation['scope'],'models':model_records},ensure_ascii=False,indent=2))
    output.writestr('RELEASE_NOTES.md',notes)
    output.writestr('BUILD-MANIFEST.json',json.dumps({'application':'AnClicker','package_type':'full-application','version':'v1.7.1','entry':'AnClicker.exe','models':list(MODELS.values()) if with_models else []}))
   with zipfile.ZipFile(partial) as archive:
    assert archive.testzip() is None
    names=archive.namelist();assert len(names)==len(set(names))
    assert sorted(n for n in names if n.endswith('.gguf'))==sorted(['AnClicker/models/'+n for n in MODELS.values()] if with_models else [])
    assert not any('/training/' in n or '/.private' in n or n.endswith('.log') or (n.endswith('.db') and not n.startswith('AnClicker/defaults/')) for n in names)
   partial.rename(target)
   sha=digest(target);target.with_suffix('.zip.sha256').write_text(sha+'  '+target.name+'\n',encoding='ascii')
   assets.append({'scope':scope,'path':target.relative_to(BASE).as_posix(),'bytes':target.stat().st_size,'sha256':sha})
   print('PASS complete archive: '+name,flush=True)
 source=BASE/'public/AnClicker-v1.7.1-win-DaiMa.zip'
 assert source.is_file(),'Source artifact missing'
 assets.append({'scope':'public','path':source.relative_to(BASE).as_posix(),'bytes':source.stat().st_size,'sha256':digest(source)})
 (BASE/'release-manifest.json').write_text(json.dumps({'version':'1.7.1','public_repository':'714248411/AnClicker','private_repository':'714248411/AnClicker-Private-Models','published':False,'assets':assets},indent=2),encoding='utf8')
if __name__=='__main__':main()
