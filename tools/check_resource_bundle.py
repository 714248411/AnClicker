"""Exercise asset restoration independently of the user's live Data."""
import sys, tempfile, json, zipfile, subprocess, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.app import resource_bundle as bundle
from tools.packaging.resource_archive import pack_resources

def fixture(root):
 (root/'resource-bootstrap-v1').write_text('1')
 for name in ('models/test.gguf','models/llama-cpu/ggml.dll','ocr_models/model.onnx','resources/background/dll/Go.dll','runtime/electron/electron.exe'):
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((name*500).encode())
 for name in ('python310.dll','vcruntime140.dll','Data/user.txt','models/dual_model.json','models/active_model.json'):
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'keep')
 return pack_resources(root)

with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);summary=fixture(root)
 assert summary['files']==5 and not (root/'models/test.gguf').exists()
 for name in ('python310.dll','vcruntime140.dll','Data/user.txt'):assert (root/name).read_bytes()==b'keep'
 assert bundle.ensure_resources(root)['restored']==5
 expected={n:bundle.digest(root/n) for n in json.loads((root/bundle.MANIFEST).read_text())['files']}
 # No model hashing/decompression on a warm start.
 with patch.object(bundle,'digest',side_effect=AssertionError('unnecessary model hash')):
  assert bundle.ensure_resources(root)['restored']==0
 (root/'models/test.gguf').unlink()
 assert bundle.ensure_resources(root)['restored']==1
 (root/'models/llama-cpu/ggml.dll').write_bytes(b'corrupted')
 assert bundle.ensure_resources(root)['restored']==1
 assert all(bundle.digest(root/n)==sha for n,sha in expected.items())
 # An interrupted state write is recoverable from the original archive.
 (root/bundle.STATE).write_text('{')
 assert bundle.ensure_resources(root)['restored']==0
 # Multiple processes launch against a cold directory safely.
 for n in expected:(root/n).unlink()
 code='from anclicker.app.resource_bundle import ensure_resources;import sys;print(ensure_resources(sys.argv[1]))'
 children=[subprocess.Popen([sys.executable,'-c',code,str(root)],cwd=str(Path(__file__).resolve().parents[1]),stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(3)]
 for child in children:
  output,error=child.communicate(timeout=30)
  assert child.returncode==0,(output,error)
 assert bundle.ensure_resources(root,verify=True)['restored']==0
 # Invalid paths must fail before writing outside the program directory.
 manifest=json.loads((root/bundle.MANIFEST).read_text());manifest['files']['models/../../escape.dll']={'size':1,'sha256':'0'*64}
 (root/bundle.MANIFEST).write_text(json.dumps(manifest))
 try:bundle.ensure_resources(root)
 except ValueError:pass
 else:raise AssertionError('unsafe path accepted')
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);fixture(root)
 # Corrupt archive never publishes partially verified resources.
 with zipfile.ZipFile(root/bundle.ARCHIVE,'a') as z:z.writestr('models/injected.dll',b'bad')
 try:bundle.ensure_resources(root)
 except ValueError:pass
 else:raise AssertionError('unexpected archive member accepted')
 assert not (root/'models/test.gguf').exists()
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory);fixture(root);(root/bundle.ARCHIVE).unlink()
 try:bundle.ensure_resources(root)
 except RuntimeError:pass
 else:raise AssertionError('missing archive silently accepted')
print('PASS cold/warm startup, original paths, missing/corrupt repair, crash recovery, concurrent launches, archive integrity, path safety, Data/bootstrap preservation')
