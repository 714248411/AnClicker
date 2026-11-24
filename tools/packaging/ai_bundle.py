"""Build identity and required AI assets shared by spec/staging checks."""
import hashlib,json
from pathlib import Path

def digest(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def resources(root):
 root=Path(root)
 names=['models/correction_cases.json']
 names += ['models/embeddings/bge-small-zh-v1.5/'+n for n in ('model.onnx','tokenizer.json','config.json','source.json','README.md')]
 for name in names:
  if not (root/name).is_file():raise RuntimeError('Missing portable AI resource: '+name)
 return names

def identity(root):
 root=Path(root)
 files=['main.py','info.py']+[p.relative_to(root).as_posix() for p in sorted((root/'models').glob('*.py'))]
 return {'schema':1,'sources':{n:digest(root/n) for n in files},'resources':{n:digest(root/n) for n in resources(root)}}

def verify(root,dist):
 root=Path(root);dist=Path(dist)
 actual=json.loads((dist/'ai-build-manifest.json').read_text(encoding='utf8'))
 expected=identity(root)
 if actual!=expected:raise RuntimeError('AI source changed since build; rebuild before staging')
 for name,sha in expected['resources'].items():
  if not (dist/name).is_file() or digest(dist/name)!=sha:raise RuntimeError('AI resource missing or stale: '+name)
 return expected

def smoke_identity(dist):
 dist=Path(dist)
 names=['AnClicker.exe','ai-build-manifest.json','models/dual_model.json']
 manifest=json.loads((dist/'ai-build-manifest.json').read_text(encoding='utf8'))
 names+=list(manifest['resources'])
 return {name:digest(dist/name) for name in names}
