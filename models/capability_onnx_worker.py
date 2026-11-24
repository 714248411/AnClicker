"""Portable offline BGE inference; usable before Qt startup in frozen builds."""
import hashlib,json,os,tempfile
from pathlib import Path

def rank(modeldir,data,cache_root=None):
 import numpy as np
 import onnxruntime as ort
 from tokenizers import Tokenizer
 modeldir=Path(modeldir)
 tokenizer=Tokenizer.from_file(str(modeldir/'tokenizer.json'))
 tokenizer.enable_truncation(max_length=256)
 tokenizer.enable_padding(pad_id=0,pad_token='[PAD]')
 options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
 session=ort.InferenceSession(str(modeldir/'model.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
 def encode(texts):
  batches=[]
  for start in range(0,len(texts),16):
   encoded=tokenizer.encode_batch(texts[start:start+16])
   inputs={'input_ids':np.asarray([e.ids for e in encoded],dtype=np.int64),'attention_mask':np.asarray([e.attention_mask for e in encoded],dtype=np.int64),'token_type_ids':np.asarray([e.type_ids for e in encoded],dtype=np.int64)}
   batches.append(session.run(None,inputs)[0])
  return np.concatenate(batches)
 docs=data['documents']
 if not isinstance(docs,list) or not docs:raise ValueError('empty documents')
 identity=[(f.name,f.stat().st_size,f.stat().st_mtime_ns) for f in (modeldir/'model.onnx',modeldir/'tokenizer.json')]
 fingerprint=hashlib.sha256(json.dumps([docs,identity],ensure_ascii=False).encode()).hexdigest()
 cache_root=Path(cache_root or Path(tempfile.gettempdir())/'AnClicker-embedding-cache');cache_root.mkdir(parents=True,exist_ok=True)
 cache=cache_root/(fingerprint+'.npy');vectors=None
 try:
  vectors=np.load(cache,allow_pickle=False)
  if vectors.shape!=(len(docs),session.get_outputs()[0].shape[1]) or not np.isfinite(vectors).all():vectors=None
 except (OSError,ValueError):pass
 if vectors is None:
  vectors=encode([d['text'] for d in docs])
  with tempfile.NamedTemporaryFile(dir=cache_root,suffix='.tmp',delete=False) as handle:
   temporary=Path(handle.name);np.save(handle,vectors,allow_pickle=False)
  try:os.replace(temporary,cache)
  finally:temporary.unlink(missing_ok=True)
 query=encode(['为这个句子生成表示以用于检索相关文章：'+data['query']])
 order=(query@vectors.T)[0].argsort()[::-1].tolist()
 return [docs[i]['type_id'] for i in order[:12]]

def main(args=None):
 import sys
 args=list(sys.argv[1:] if args is None else args)
 modeldir,request,result=args
 data=json.loads(Path(request).read_text(encoding='utf8'))
 ranked=rank(modeldir,data)
 Path(result).write_text(json.dumps(ranked,ensure_ascii=False),encoding='utf8')
 return 0

if __name__=='__main__':raise SystemExit(main())
