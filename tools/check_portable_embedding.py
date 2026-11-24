import sys,json,tempfile
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/debug/v173-optimize';model=ROOT/'models/embeddings/bge-small-zh-v1.5'
reference=np.load(OUT/'embedding-parity.npz');texts=json.loads((OUT/'embedding-parity-texts.json').read_text(encoding='utf8'))
tokenizer=Tokenizer.from_file(str(model/'tokenizer.json'));tokenizer.enable_truncation(max_length=256);tokenizer.enable_padding(pad_id=0,pad_token='[PAD]')
enc=tokenizer.encode_batch(texts)
inputs={'input_ids':np.array([x.ids for x in enc],dtype=np.int64),'attention_mask':np.array([x.attention_mask for x in enc],dtype=np.int64),'token_type_ids':np.array([x.type_ids for x in enc],dtype=np.int64)}
for name,array in inputs.items():assert np.array_equal(array,reference[name]),name
session=ort.InferenceSession(str(model/'model.onnx'),providers=['CPUExecutionProvider']);actual=session.run(None,inputs)[0]
error=float(np.max(np.abs(actual-reference['expected'])));assert error<1e-5,error
from models.capability_onnx_worker import rank
with tempfile.TemporaryDirectory() as folder:
 data={'query':'往下翻一点','documents':[{'type_id':'滚轮滑动','text':'鼠标滚轮，向下翻页面'},{'type_id':'保存Excel','text':'保存Excel工作簿'}]}
 first=rank(model,data,folder);assert first[0]=='滚轮滑动',first
 for cache in Path(folder).glob('*.npy'):cache.write_bytes(b'corrupt cache')
 assert rank(model,data,folder)==first
report={'passed':True,'sentences':len(texts),'tokenization_identical':True,'max_absolute_error':error,'corrupt_cache_rebuilt':True}
(OUT/'embedding-parity.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)
