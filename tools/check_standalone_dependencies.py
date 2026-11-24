"""Dependency selection must reduce desktop exports without pruning dynamic projects."""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from anclicker.app.standalone_dependencies import runtime_profile
from anclicker.app.standalone_export import copy_runtime
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);data=root/'Data';data.mkdir()
 def project(path,kinds):
  b=Workbook();s=b.active;s.title='命令';s.append(['ID','类型标识','参数JSON'])
  for i,k in enumerate(kinds):s.append([i+1,k,'{}'])
  b.save(path);b.close()
 project(data/'project.xlsx',['时间等待','图像点击','OCR识别'])
 profile=runtime_profile(data);assert profile['mode']=='desktop',profile
 runtime=root/'runtime';runtime.mkdir();(runtime/'AnClicker.exe').write_bytes(b'probe')
 for name in ['runtime','models','ocr_models','cv2','PySide2']:
  (runtime/name).mkdir();(runtime/name/'resource').write_bytes(b'fixture')
 out=root/'out';out.mkdir();copy_runtime(runtime,out,lambda _:None,profile)
 assert not (out/'runtime').exists() and not (out/'models').exists()
 for name in ['ocr_models','cv2','PySide2']:assert (out/name/'resource').is_file()
 for kind in ['运行Python','运行项目','打开网页','Crawl4AI网页抓取','future-unknown']:
  project(data/'project.xlsx',[kind]);assert runtime_profile(data)['mode']=='full',kind
 project(data/'project.xlsx',['时间等待']);(data/'resources').mkdir()
 project(data/'resources/child.xlsx',['运行Python'])
 assert runtime_profile(data)['mode']=='full'
 (data/'resources/child.xlsx').unlink()
 (data/'resources/broken.xlsx').write_bytes(b'broken')
 assert runtime_profile(data)['mode']=='full'
 print('PASS desktop reduction, vision retention, nested/dynamic/unknown/corrupt fallback')
