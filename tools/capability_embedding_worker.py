"""Short-lived CPU-only, offline BGE retrieval. JSON stdin/stdout; no remote code."""
import os,sys,json,hashlib
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
from transformers import AutoTokenizer,AutoModel
torch.set_num_threads(2)
root=Path(sys.argv[1]);data=json.load(sys.stdin)
tokenizer=AutoTokenizer.from_pretrained(root,local_files_only=True,trust_remote_code=False)
model=AutoModel.from_pretrained(root,local_files_only=True,trust_remote_code=False,use_safetensors=True).eval().cpu()
def encode(texts):
    values=[]
    with torch.inference_mode():
        for i in range(0,len(texts),16):
            batch=tokenizer(texts[i:i+16],padding=True,truncation=True,max_length=256,return_tensors='pt')
            values.append(torch.nn.functional.normalize(model(**batch).last_hidden_state[:,0],p=2,dim=1))
    return torch.cat(values)
docs=data['documents']
identity=[(f.name,f.stat().st_size,f.stat().st_mtime_ns) for f in sorted(root.iterdir()) if f.suffix in ('.json','.safetensors','.txt')]
fingerprint=hashlib.sha256(json.dumps([docs,identity],ensure_ascii=False).encode()).hexdigest()
cache=root/('index-'+fingerprint+'.pt')
if cache.is_file():vectors=torch.load(cache,map_location='cpu',weights_only=True)
else:
    vectors=encode([d['text'] for d in docs]);temp=cache.with_suffix('.'+str(os.getpid())+'.tmp');torch.save(vectors,temp);temp.replace(cache)
query=encode(['为这个句子生成表示以用于检索相关文章：'+data['query']])
order=(query@vectors.T)[0].argsort(descending=True).tolist()
print(json.dumps([docs[i]['type_id'] for i in order[:12]],ensure_ascii=False))
