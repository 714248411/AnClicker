"""Download fixed BGE revision through alternate routes and verify repository hashes."""
import json,hashlib,shutil,time
from pathlib import Path
from urllib.parse import quote
import requests
ROOT=Path(__file__).resolve().parents[1];target=ROOT/'models/embeddings/bge-small-zh-v1.5';target.mkdir(parents=True,exist_ok=True)
repo='BAAI/bge-small-zh-v1.5'
revision='7999e1d3359715c523056ef9478215996d62a620'
base='https://hf-mirror.com'
r=requests.get(base+'/api/models/'+repo+'/revision/'+revision+'?blobs=true',timeout=20);r.raise_for_status();metadata=r.json()
assert metadata['sha']==revision
wanted={'config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','model.safetensors','README.md'}
files=[f for f in metadata['siblings'] if f['rfilename'] in wanted]
assert {f['rfilename'] for f in files}==wanted
usage=shutil.disk_usage(ROOT)
assert usage.free-sum(f['size'] for f in files)>usage.total*.02,'剩余空间不足2%'
def verify(path,info):
 if not path.is_file() or path.stat().st_size!=info['size']:return False
 raw=path.read_bytes()
 return hashlib.sha256(raw).hexdigest()==info['lfs']['sha256'] if info.get('lfs') else hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==info['blobId']
manifest=[]
for info in files:
 name=info['rfilename'];dest=target/name;source='existing verified file'
 if not verify(dest,info):
  urls=[base+'/'+repo+'/resolve/'+revision+'/'+name,'https://modelscope.cn/models/'+repo+'/resolve/master/'+name,'https://huggingface.co/'+repo+'/resolve/'+revision+'/'+name]
  ok=False
  for attempt in range(3):
   for url in urls:
    print('DOWNLOAD',name,'route',url.split('/')[2],'attempt',attempt+1,flush=True)
    partial=dest.with_suffix(dest.suffix+'.part')
    try:
     with requests.get(url,stream=True,timeout=(12,30)) as response:
      response.raise_for_status()
      with partial.open('wb') as stream:
       for chunk in response.iter_content(1024*1024):stream.write(chunk)
     if not verify(partial,info):raise ValueError('size/hash mismatch')
     partial.replace(dest);source=url;ok=True;break
    except Exception as error:print('RETRY',type(error).__name__,str(error)[:180],flush=True)
   if ok:break
  if not ok:raise RuntimeError('所有线路失败: '+name)
 manifest.append({'file':name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source':source})
 print('VERIFIED',name,flush=True)
(target/'source.json').write_text(json.dumps({'repo':repo,'revision':revision,'license':'MIT','files':manifest},ensure_ascii=False,indent=2),encoding='utf8')
print('EMBEDDING_READY',flush=True)
