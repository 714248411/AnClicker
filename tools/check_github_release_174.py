import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.publish_github_171 import authenticate,api
try:
 client=authenticate();data=api(client,'GET','/repos/714248411/AnClicker');releases=api(client,'GET','/repos/714248411/AnClicker/releases?per_page=10')
 print(json.dumps({'push':data.get('permissions',{}).get('push'),'private':data['private'],'releases':[{'tag':r['tag_name'],'draft':r['draft']} for r in releases]}))
except Exception as error:print(type(error).__name__+': '+str(error));sys.exit(1)
