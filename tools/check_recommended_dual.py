import json,tempfile
from pathlib import Path
from contextlib import contextmanager
from models.model_library import ModelLibrary
class Manager:
 def __init__(self,root):self.root=root
 @contextmanager
 def _exclusive(self,blocking=False):yield True
 def stop(self):pass
with tempfile.TemporaryDirectory() as d:
 root=Path(d);lib=ModelLibrary(Manager(root))
 assert lib.recommended_dual() is None
 for n in ['old-s.gguf','old-c.gguf','new-s.gguf','new-c.gguf']:(root/n).write_bytes(b'GGUF')
 current={'enabled':True,'splitter':'old-s.gguf','converter':'old-c.gguf'}
 (root/'dual_model.json').write_text(json.dumps(current))
 recommended={'verified':True,'splitter':'new-s.gguf','converter':'new-c.gguf'}
 (root/'recommended_dual_model.json').write_text(json.dumps(recommended))
 lib.apply('dual',True);assert lib.dual_config()['splitter']=='new-s.gguf'
 (root/'dual_model.json').write_text(json.dumps(current))
 recommended['verified']=False;(root/'recommended_dual_model.json').write_text(json.dumps(recommended))
 assert lib.recommended_dual()['splitter']=='old-s.gguf'
 recommended.update(verified=True,splitter='../escape.gguf');(root/'recommended_dual_model.json').write_text(json.dumps(recommended))
 assert lib.recommended_dual()['splitter']=='old-s.gguf'

 recommended.update(verified=True,splitter='new-s.gguf',splitter_mode='pairwise',serial_models=True,embedding_enabled=True,correction_memory_enabled=True)
 (root/'recommended_dual_model.json').write_text(json.dumps(recommended))
 lib.apply('dual',True)
 assert lib.dual_config()['splitter_mode']=='pairwise'
 assert lib.dual_config()['embedding_enabled'] is True
 (root/'dual_model.json').write_text(json.dumps(current))
 recommended['splitter_mode']='unsupported';(root/'recommended_dual_model.json').write_text(json.dumps(recommended))
 assert lib.recommended_dual()['splitter']=='old-s.gguf'
print('PASS verified recommended model selection, no unverified upgrade, path isolation and current selection fallback')
