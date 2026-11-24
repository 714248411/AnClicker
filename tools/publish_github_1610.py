"""Publish 1.6.10 packages to public/private GitHub releases after manifest validation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import requests

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def authenticate():
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        try:
            result=subprocess.run(['gh','auth','token'],capture_output=True,text=True,timeout=15)
            if result.returncode==0:token=result.stdout.strip()
        except (OSError,subprocess.TimeoutExpired):pass
    if not token:
        result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,timeout=20,env=dict(os.environ,GCM_INTERACTIVE='never',GIT_TERMINAL_PROMPT='0'))
        if result.returncode==0:
            token=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line).get('password')
    if not token:raise RuntimeError('GitHub authentication unavailable. Sign in using gh auth login or GH_TOKEN.')
    client=requests.Session()
    client.headers.update(Authorization='Bearer '+token,Accept='application/vnd.github+json')
    return client

def api(client,method,path,**kwargs):
    response=client.request(method,'https://api.github.com'+path,timeout=60,**kwargs)
    if not response.ok:raise RuntimeError(f'GitHub {method} {path}: HTTP {response.status_code}')
    return response.json()

def publish(client,repo,private,assets,notes):
    metadata=api(client,'GET','/repos/'+repo)
    if bool(metadata['private'])!=private:raise RuntimeError('Repository visibility mismatch: '+repo)
    if not metadata.get('permissions',{}).get('push'):raise RuntimeError('Missing repository write permission')
    releases=api(client,'GET','/repos/'+repo+'/releases?per_page=100')
    release=next((r for r in releases if r['tag_name']=='v1.6.10'),None)
    if release is None:
        release=api(client,'POST','/repos/'+repo+'/releases',json={'tag_name':'v1.6.10','name':'AnClicker 1.6.10'+(' Private 3B' if private else ''),'body':notes,'draft':True})
    existing=api(client,'GET',f"/repos/{repo}/releases/{release['id']}/assets?per_page=100")
    for file in assets:
        sha=digest(file)
        old=next((a for a in existing if a['name']==file.name),None)
        if old:
            if old.get('digest')!='sha256:'+sha:raise RuntimeError('Existing asset differs; no overwrite: '+file.name)
            continue
        with file.open('rb') as stream:
            response=client.post(release['upload_url'].split('{')[0],params={'name':file.name},data=stream,headers={'Content-Type':'application/octet-stream'},timeout=(15,1800))
        if response.status_code!=201:raise RuntimeError('Upload failed: '+file.name+' HTTP '+str(response.status_code))
        asset=response.json()
        if asset['size']!=file.stat().st_size or (asset.get('digest') and asset['digest']!='sha256:'+sha):raise RuntimeError('Uploaded asset integrity mismatch')
        print('Uploaded '+file.name,flush=True)
    release=api(client,'PATCH',f"/repos/{repo}/releases/{release['id']}",json={'draft':False,'body':notes})
    print(release['html_url'],flush=True)
    return release['html_url']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--private-repo',default='AnClicker-Private-Models');args=parser.parse_args()
    base=ROOT/'artifacts/release/v1.6.10'
    manifest=json.loads((base/'release-manifest.json').read_text(encoding='utf-8'))
    assets={scope:[] for scope in ('public','private')}
    for item in manifest['assets']:
        path=base/item['path']
        if not path.resolve().is_relative_to(base.resolve()) or digest(path)!=item['sha256']:raise RuntimeError('Local artifact integrity mismatch')
        assets[item['scope']].append(path)
    client=authenticate()
    user=api(client,'GET','/user')['login']
    if user!='714248411':raise RuntimeError('Expected account 714248411; actual account '+user)
    private_repo=user+'/'+args.private_repo
    response=client.get('https://api.github.com/repos/'+private_repo,timeout=30)
    if response.status_code==404:
        created=api(client,'POST','/user/repos',json={'name':args.private_repo,'private':True,'auto_init':True,'description':'Private AnClicker large-model release packages'})
        if not created['private']:raise RuntimeError('New repository is not private')
    elif response.status_code!=200:raise RuntimeError('Unable to verify private repository')
    notes=(base/'RELEASE_NOTES.md').read_text(encoding='utf-8')
    public_url=publish(client,'714248411/AnClicker',False,assets['public'],notes)
    manifest.update(public_published=True,public_release_url=public_url)
    (base/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    private_url=publish(client,private_repo,True,assets['private'],(base/'PRIVATE_RELEASE_NOTES.md').read_text(encoding='utf-8'))
    manifest.update(published=True,private_release_url=private_url)
    (base/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
