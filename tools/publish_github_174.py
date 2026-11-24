"""Publish the verified public 1.7.4 assets; authenticate outside the source tree."""
import json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.publish_github_171 import authenticate,api,digest
BASE=ROOT/'artifacts/release/v1.7.4'
REPO='714248411/AnClicker'
VERSION='v1.7.4'
def main():
 subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/verify_release_174_artifacts.py')],cwd=ROOT,check=True)
 language=json.loads((ROOT/'artifacts/validation/v1.7.4/candidate-language.json').read_text(encoding='utf8'))
 assert language['version']=='v1.7.4' and language['passed']==language['total']==48 and not language['fallbacks']
 manifest=json.loads((BASE/'release-manifest.json').read_text(encoding='utf8'))
 assert manifest['version']=='1.7.4'
 assert json.loads((ROOT/'artifacts/validation/v1.7.4/smoke-passed.json').read_text())['passed']
 files=[]
 for item in manifest['assets']:
  path=(BASE/item['path']).resolve()
  assert path.is_relative_to(BASE.resolve()) and digest(path)==item['sha256']
  files.extend([path,path.with_suffix('.zip.sha256')])
 client=authenticate()
 metadata=api(client,'GET','/repos/'+REPO)
 assert metadata['private'] is False and metadata.get('permissions',{}).get('push')
 releases=api(client,'GET',f'/repos/{REPO}/releases?per_page=100')
 release=next((r for r in releases if r['tag_name']==VERSION),None)
 if release is None:
  versions=[tuple(map(int,r['tag_name'].lstrip('v').split('.'))) for r in releases if not r['draft'] and r['tag_name'].lstrip('v').replace('.','').isdigit()]
  assert not versions or max(versions)<(1,7,4),'A newer public release already exists'
  release=api(client,'POST',f'/repos/{REPO}/releases',json={'tag_name':VERSION,'name':'AnClicker 1.7.4','body':(BASE/'RELEASE_NOTES.md').read_text(encoding='utf8'),'draft':True})
 existing=api(client,'GET',f"/repos/{REPO}/releases/{release['id']}/assets?per_page=100")
 for path in files:
  sha=digest(path);old=next((a for a in existing if a['name']==path.name),None)
  if old:
   assert old.get('digest')=='sha256:'+sha,'Existing release asset differs; no overwrite'
   continue
  with path.open('rb') as stream:
   response=client.post(release['upload_url'].split('{')[0],params={'name':path.name},data=stream,headers={'Content-Type':'application/octet-stream'},timeout=(15,1800))
  assert response.status_code==201,f'Upload failed: HTTP {response.status_code}'
  asset=response.json()
  assert asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+sha
  print('Verified upload '+path.name,flush=True)
 release=api(client,'PATCH',f"/repos/{REPO}/releases/{release['id']}",json={'draft':False,'make_latest':'true'})
 verified=api(client,'GET',f'/repos/{REPO}/releases/tags/{VERSION}')
 assert not verified['draft'] and verified['tag_name']==VERSION
 assert {a['name'] for a in verified['assets']}=={f.name for f in files}
 for item in verified['assets']:
  local=next(f for f in files if f.name==item['name'])
  assert item['size']==local.stat().st_size and item.get('digest')=='sha256:'+digest(local)
 manifest.update(published=True,release_url=release['html_url'],github_digest_verified=True)
 (BASE/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
 print(release['html_url'])
if __name__=='__main__':main()
