import sys,os,tempfile,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from instructions.common.rpa_bridge import RpaBridge
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='ac-web-check-')
b=RpaBridge()
try:
 for url in ['https://www.baidu.com','https://example.com']:
  try:
   result=b.execute({'id':'openUrl','params':{'url':url,'target':'新窗口','waitType':'加载完成'}},timeout=45)
   print(json.dumps({'url':url,'open':result,'inspect':b.execute({'id':'acInspect'})},ensure_ascii=False),flush=True)
   print(json.dumps(b.execute({'id':'getText','params':{'selector':'body','by':'CSS选择器','varName':'body'}}),ensure_ascii=False)[:1000],flush=True)
  except Exception as e:print(type(e).__name__,str(e),flush=True)
finally:b.close()
