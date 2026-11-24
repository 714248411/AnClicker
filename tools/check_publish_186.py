import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['PATH']=str(ROOT/'artifacts/tools/github-cli/bin')+os.pathsep+os.environ.get('PATH','')
from tools.publish_github_171 import authenticate,api
from tools.publishing_credentials import publishing_environment
from info import UPDATE_CONFIG
publishing_environment(sys.argv[1],os.environ,UPDATE_CONFIG)
print('PASS Qiniu credential configuration (values withheld)',flush=True)
client=authenticate()
repo=api(client,'GET','/repos/714248411/AnClicker')
assert repo.get('permissions',{}).get('push')
releases=api(client,'GET','/repos/714248411/AnClicker/releases?per_page=10')
print(json.dumps([{'tag':r['tag_name'],'draft':r['draft']} for r in releases]))
