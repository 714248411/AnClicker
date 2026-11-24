"""Export the verified local BGE model; never fetch remote weights."""
import sys,json,hashlib
from pathlib import Path
import torch
from transformers import AutoModel,AutoTokenizer
ROOT=Path(__file__).resolve().parents[1]
modeldir=ROOT/'models/embeddings/bge-small-zh-v1.5'
class Encoder(torch.nn.Module):
 def __init__(self):
  super().__init__();self.model=AutoModel.from_pretrained(modeldir,local_files_only=True,trust_remote_code=False,attn_implementation='eager').eval()
 def forward(self,input_ids,attention_mask,token_type_ids):
  hidden=self.model(input_ids=input_ids,attention_mask=attention_mask,token_type_ids=token_type_ids).last_hidden_state[:,0]
  return torch.nn.functional.normalize(hidden,p=2,dim=1)
if __name__=='__main__':
 # Export-only dependencies: torch/transformers from the training runtime, onnx==1.19.1.
 provenance=json.loads((modeldir/'source.json').read_text(encoding='utf8'))
 for item in provenance['files']:
  actual=hashlib.sha256((modeldir/item['file']).read_bytes()).hexdigest()
  if actual!=item['sha256']:raise RuntimeError('Unverified model input: '+item['file'])
 torch.set_num_threads(2)
 model=Encoder().eval();tok=AutoTokenizer.from_pretrained(modeldir,local_files_only=True)
 batch=tok(['打开百度搜索热点','往下翻一点'],padding=True,return_tensors='pt')
 target=modeldir/'model.onnx';partial=modeldir/'model.partial.onnx'
 torch.onnx.export(model,tuple(batch[k] for k in ('input_ids','attention_mask','token_type_ids')),str(partial),input_names=['input_ids','attention_mask','token_type_ids'],output_names=['embeddings'],dynamic_axes={**{k:{0:'batch',1:'sequence'} for k in batch},'embeddings':{0:'batch'}},opset_version=17,dynamo=False)
 partial.replace(target)
 import numpy as np
 evidence=ROOT/'artifacts/debug/v173-optimize';evidence.mkdir(parents=True,exist_ok=True)
 texts=['为这个句子生成表示以用于检索相关文章：'+x for x in ['往下翻一点','把网页上的结果放回表格','敲一下Escape键','打开hao123.com','输入“不要关窗口”','帮我把当前工作簿存好','识别图片上的文字','把表里的内容挨个填上','读取剪贴板内容','按住鼠标拖过去']]
 sample=tok(texts,padding=True,truncation=True,max_length=256,return_tensors='pt')
 with torch.inference_mode():expected=model(**sample).numpy()
 np.savez(evidence/'embedding-parity.npz',**{k:v.numpy() for k,v in sample.items()},expected=expected)
 (evidence/'embedding-parity-texts.json').write_text(json.dumps(texts,ensure_ascii=False),encoding='utf8')
 print('EXPORTED',target,target.stat().st_size,flush=True)
