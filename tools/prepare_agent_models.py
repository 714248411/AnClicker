"""Download pinned official CPU runtime/model candidates; never start inference."""
import argparse,hashlib,json,subprocess,zipfile,os,shutil,struct
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'.agent-runtime'
ASSETS=[
 ('llama-cpu.zip','https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-cpu-x64.zip','1283323272b04cd07905816a597a0da810918102de958f4ff6f7bbaa70ed2efe'),
 ('qwen2.5-0.5b-instruct-q4_0.gguf','https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf','7671c0c304e6ce5a7fc577bcb12aba01e2c155cc2efd29b2213c95b18edaf6ed'),
 ('functiongemma-270m.gguf','https://registry.ollama.ai/v2/library/functiongemma/blobs/sha256:415f8f959d807bd4d4da891f01225d7b330416947fb011a8473080ae4fd07885','415f8f959d807bd4d4da891f01225d7b330416947fb011a8473080ae4fd07885')]

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def download(asset):
 name,url,expected=asset;target=DEST/name;partial=DEST/(name+'.part')
 if not target.exists() or digest(target)!=expected:
  print('Downloading '+name,flush=True)
  subprocess.run(['curl.exe','-fL','--retry','3','--connect-timeout','20','--max-time','1800','-C','-','-o',str(partial),url],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if digest(partial)!=expected:raise ValueError(name+' SHA256 mismatch')
  partial.replace(target)
 print('Verified '+name+' '+str(target.stat().st_size)+' bytes',flush=True)
 if name.endswith('.zip'):
  folder=DEST/Path(name).stem;folder.mkdir(exist_ok=True)
  with zipfile.ZipFile(target) as archive:
   for item in archive.infolist():
    resolved=(folder/item.filename).resolve()
    if not resolved.is_relative_to(folder.resolve()):raise ValueError('Unsafe archive path')
   for item in archive.infolist():
    resolved=folder/item.filename
    if item.is_dir():resolved.mkdir(parents=True,exist_ok=True);continue
    contents=archive.read(item)
    if not resolved.exists() or resolved.read_bytes()!=contents:
     resolved.parent.mkdir(parents=True,exist_ok=True);resolved.write_bytes(contents)
 return {'file':name,'bytes':target.stat().st_size,'sha256':expected,'source':url}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--functiongemma',action='store_true');parser.add_argument('--gpu',action='store_true');args=parser.parse_args()
 DEST.mkdir(exist_ok=True)
 assets=list(ASSETS if args.functiongemma else ASSETS[:2])
 if args.gpu:assets.append(('llama-vulkan.zip','https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-vulkan-x64.zip','1bfe78ad9168b79fa02bf67f6af9f5e17a966d824d77238517f7bef12ac73b36'))
 with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(download,assets))
 (DEST/'verified-assets.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 licenses=[('LICENSE-Qwen.txt','https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/LICENSE'),('LICENSE-llama.cpp.txt','https://raw.githubusercontent.com/ggml-org/llama.cpp/b11429/LICENSE')]
 if args.functiongemma:licenses.append(('LICENSE-FunctionGemma.txt','https://registry.ollama.ai/v2/library/functiongemma/blobs/sha256:64c834d5c134577dc3e6b29bc8df5cd75f0e07bf8b9b03ee20a6e43dcc3808a0'))
 for name,url in licenses:
  subprocess.run(['curl.exe','-fLsS','--retry','2','--connect-timeout','15','--max-time','60','-o',str(DEST/name),url],check=True)
 # Use app-local VC runtime DLLs so copied bundles also run on PCs with older system runtimes.
 binary=DEST/'llama-cpu/llama-server.exe'
 check=subprocess.run([str(binary),'--version'],capture_output=True,timeout=15)
 repaired=False
 if check.returncode in (3221225477,-1073741819,3221225781,-1073741515):
  installer=DEST/'vc_redist.x64.exe'
  subprocess.run(['curl.exe','-fLsS','--retry','2','--max-time','180','-o',str(installer),'https://aka.ms/vc14/vc_redist.x64.exe'],check=True)
  installed=subprocess.run([str(installer),'/install','/quiet','/norestart','/log',str(DEST/'vc-install.log')],timeout=120)
  if installed.returncode not in (0,3010):raise RuntimeError('Visual C++ runtime install failed: '+str(installed.returncode))
  repaired=True
 system=Path(os.environ.get('WINDIR','C:/Windows'))/('Sysnative' if struct.calcsize('P')==4 else 'System32')
 names=['msvcp140.dll','msvcp140_1.dll','msvcp140_2.dll','msvcp140_atomic_wait.dll','msvcp140_codecvt_ids.dll','vcruntime140.dll','vcruntime140_1.dll','concrt140.dll']
 for folder in [DEST/'llama-cpu',DEST/'llama-vulkan']:
  if not folder.exists():continue
  for name in names:
   source=system/name;target=folder/name
   if source.is_file() and (repaired or not target.exists()):shutil.copy2(source,target)
 subprocess.run([str(binary),'--version'],check=True,timeout=15)
 print('Files ready. This preparation script did not start inference.',flush=True)
