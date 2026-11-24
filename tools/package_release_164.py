"""Assemble complete 1.6.4 public v5 and private API archives, never a patch."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/release/v1.6.4'
DIST=ROOT/'artifacts/dist/v1.6.4/AnClicker'
MODEL='anclicker-planner-v5-q4_0.gguf'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    assert (DIST/'AnClicker.exe').is_file()
    files=sorted(p for p in DIST.rglob('*') if p.is_file())
    assert not any(p.suffix.lower()=='.gguf' for p in files)
    assert not (DIST/'data').exists()
    assets=[]
    notes=(ROOT/'CHANGELOG.md').read_text(encoding='utf-8').split('## v1.6.3',1)[0]
    notes+='\n这是完整程序包，请解压到新目录后运行 AnClicker.exe。公开版仅附带 v5 模型。\n\n验证：真实 Qt5 表格排序与中键平移、网页多锚点与框架、窗口置顶置底、首次便携启动及成品功能检查。构建与验证主机为 Windows 10 22H2；尚未在 Windows 10 1607 14393.2214 真机验证。\n'
    BASE.mkdir(parents=True,exist_ok=True)
    (BASE/'RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
    (BASE/'PRIVATE_RELEASE_NOTES.md').write_text(notes+'\n私密版使用本版 API 主程序，并将 [v1.6.3 私密 3B 模型包](https://github.com/714248411/AnClicker-Private-Models/releases/tag/v1.6.3) 解压到同一目录；模型权重未变更。\n',encoding='utf-8')
    with zipfile.ZipFile(ROOT/'artifacts/release/public/AnClicker-v1.6.3-win.zip') as previous:
        extras=[i for i in previous.infolist() if i.filename.startswith('AnClicker/models/') and not i.is_dir()]
        assert [i.filename for i in extras if i.filename.endswith('.gguf')]==['AnClicker/models/'+MODEL]
        current_names={'AnClicker/'+p.relative_to(DIST).as_posix() for p in files}
        for scope,name,with_model in [('public','AnClicker-v1.6.4-win.zip',True),('private','AnClicker-v1.6.4-api-win-x64.zip',False)]:
            target=BASE/scope/name;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                partial=target.with_suffix('.zip.partial')
                with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
                    for path in files:output.write(path,'AnClicker/'+path.relative_to(DIST).as_posix())
                    if with_model:
                        for entry in extras:
                            if entry.filename in current_names:continue
                            with previous.open(entry) as source,output.open(entry.filename,'w',force_zip64=True) as destination:shutil.copyfileobj(source,destination,1024*1024)
                    output.writestr('RELEASE_NOTES.md',notes)
                    output.writestr('BUILD-MANIFEST.json',json.dumps({'application':'An Clicker','package_type':'full-application','version':'v1.6.4','platform':'windows-x64','python':'3.10.11','entry':'AnClicker.exe','model':MODEL if with_model else None,'target_os_verified':False},ensure_ascii=False,indent=2))
                partial.replace(target)
            with zipfile.ZipFile(target) as archive:
                assert archive.testzip() is None
                names=archive.namelist()
                assert len(names)==len(set(names))
                assert [n for n in names if n.endswith('.gguf')]==(['AnClicker/models/'+MODEL] if with_model else [])
                assert not any('/training/' in n or '/.private' in n or n.endswith('.log') or (n.endswith('.db') and not n.startswith('AnClicker/defaults/')) for n in names)
                assert 'AnClicker/integrations/yingdao/src/anchor-locator.js' in names
            sha=digest(target)
            target.with_suffix('.zip.sha256').write_text(sha+'  '+target.name+'\n',encoding='ascii')
            assets.append({'scope':scope,'path':str(target.relative_to(BASE)).replace('\\','/'),'bytes':target.stat().st_size,'sha256':sha})
            print('PASS complete '+scope+' archive: '+name+'; SHA256 '+sha,flush=True)
    source=BASE/'public/AnClicker-v1.6.4-win-DaiMa.zip'
    if source.exists():assets.append({'scope':'public','path':'public/'+source.name,'bytes':source.stat().st_size,'sha256':digest(source)})
    manifest={'version':'1.6.4','public_repository':'714248411/AnClicker','private_repository':'714248411/AnClicker-Private-Models','published':False,'assets':assets}
    (BASE/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
