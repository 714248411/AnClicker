import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/release/v1.8.7-qiniu'
source=OUT/'AnClicker-win-x64-Portable.zip';dest=OUT/'delivery/AnClicker-v1.8.7-win.zip'
assert source.is_file() and not dest.exists()
dest.parent.mkdir(exist_ok=True);partial=dest.with_suffix('.zip.partial');assert not partial.exists()
shutil.copy2(source,partial)
with zipfile.ZipFile(partial,'a',compression=zipfile.ZIP_DEFLATED) as z:
 z.writestr('Data/',b'')
 z.writestr('使用说明.txt','请完整解压到新目录，双击根目录 AnClicker.exe。不要单独移动 current 文件夹或程序。\n旧普通 ZIP 用户：退出旧程序后，备份并复制原 Data 文件夹到本包根目录 Data。\n启动检查只提示一次，20 秒超时静默结束；仅手动检查并确认后下载更新。\n')
with zipfile.ZipFile(partial) as z:
 assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names))
 assert {'.portable','Update.exe','AnClicker.exe','current/AnClicker.exe','current/sq.version','Data/'}.issubset(names)
 assert len([n for n in names if n.endswith('.gguf')])==2
 assert not any(n.startswith('Data/') and n!='Data/' for n in names)
 assert not any(n.startswith('current/Data/') for n in names)
 for part in ('current/ocr_models/rapidocr/','current/runtime/electron/','current/runtime/crawl4ai/','current/models/llama-cpu/','current/models/llama-vulkan/'):
  assert any(n.startswith(part) for n in names),part
partial.rename(dest)
h=hashlib.sha256()
with dest.open('rb') as f:
 for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
dest.with_suffix('.zip.sha256').write_text(h.hexdigest()+'  '+dest.name+'\n')
(OUT/'delivery-manifest.json').write_text(json.dumps({'version':'1.8.7','file':dest.name,'bytes':dest.stat().st_size,'sha256':h.hexdigest(),'entry':'AnClicker.exe','full_models':True},indent=2))
print('PASS complete managed portable delivery:',dest)
