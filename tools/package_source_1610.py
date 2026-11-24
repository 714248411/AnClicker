"""Create the reviewed build source archive, excluding local data and model weights."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/release/v1.6.10/public'
EXCLUDED={'__pycache__','training','.trash','.private','.git','node_modules','data','.local','artifacts','.venv-build','.venv'}


def main():
    BASE.mkdir(parents=True,exist_ok=True)
    files=set()
    with zipfile.ZipFile(ROOT/'artifacts/release/v1.6.9/public/AnClicker-v1.6.9-win-DaiMa.zip') as old:
        for name in old.namelist():
            relative=Path(*Path(name).parts[1:]);path=ROOT/relative
            if path.is_file():files.add(path)
    for folder in ('anclicker','tools','models','resources/ui','integrations/yingdao/src'):
        for path in (ROOT/folder).rglob('*'):
            if path.is_file() and path.suffix in {'.py','.ui','.spec','.md','.json','.toml','.ps1','.txt','.js','.html','.css'}:files.add(path)
    filtered=[]
    for path in sorted(files):
        relative=path.relative_to(ROOT)
        if relative.parts[0]=='models':
            public_code=(len(relative.parts)==2 and (path.suffix=='.py' or path.name.startswith('LICENSE-')))
            knowledge=(len(relative.parts)==3 and relative.parts[1]=='knowledge' and path.suffix=='.json')
            if not (public_code or knowledge):continue
        if any(part in EXCLUDED or part.startswith('.private') for part in relative.parts):continue
        if path.suffix.lower() in {'.gguf','.db','.sqlite','.sqlite3','.log','.pyc','.pyo','.env','.dll','.exe','.pyd'}:continue
        if any(part.casefold() in {'credentials','secrets'} for part in relative.parts):continue
        filtered.append(path)
    target=BASE/'AnClicker-v1.6.10-win-DaiMa.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for path in filtered:output.write(path,'AnClicker-v1.6.10/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert b'v1.6.10' in archive.read('AnClicker-v1.6.10/info.py')
        for file in ('anclicker/ui/compact_position.py','anclicker/ui/information_dialogs.py','tools/check_ui_167.py'):
            assert archive.read('AnClicker-v1.6.10/'+file)==(ROOT/file).read_bytes()
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
    print(json.dumps({'source_files':len(filtered),'bytes':target.stat().st_size,'sha256':digest}))

if __name__=='__main__':main()
