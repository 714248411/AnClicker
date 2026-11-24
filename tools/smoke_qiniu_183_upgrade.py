"""Exercise the exact release Full via an isolated lower-version metadata fixture."""
import os,sys,json,zipfile,tempfile,subprocess,time,uuid,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/release/v1.8.3-qiniu'
assert (OUT/'validation-publish.json').is_file()
sandbox=Path(tempfile.mkdtemp(prefix='ac-qiniu-upgrade-'));portable=sandbox/'portable'
with zipfile.ZipFile(OUT/'AnClicker-win-x64-Portable.zip') as z:z.extractall(portable)
metadata=portable/'current/sq.version';tree=ET.parse(metadata)
versions=[e for e in tree.iter() if e.tag.split('}')[-1]=='version'];assert len(versions)==1 and versions[0].text=='1.8.3'
versions[0].text='1.8.2';tree.write(metadata,encoding='utf-8',xml_declaration=True)
env=dict(os.environ,ANCLICKER_SMOKE_FEED=str(OUT),ANCLICKER_SINGLETON_KEY='qiniu-probe-'+uuid.uuid4().hex,PYTHONDONTWRITEBYTECODE='1')
env.pop('ANCLICKER_DATA_DIR',None)
process=subprocess.Popen([str(portable/'An Clicker.exe'),'--velopack-local-smoke'],cwd=sandbox,env=env)
process.wait(timeout=180)
result=portable/'Data/velopack-smoke-result.json';deadline=time.monotonic()+360
while not result.is_file() and time.monotonic()<deadline:time.sleep(1)
assert result.is_file(),str(sandbox)
report=json.loads(result.read_text(encoding='utf8'))
assert report=={'from':'1.8.2','downloaded':True,'to':'1.8.3','restarted':True,'data_preserved':True},report
assert not (portable/'current/Data').exists()
proof={'passed':True,'fixture':'current release executable with lower sq.version metadata','feed':'exact production Full package, local transport','sandbox':str(sandbox),'result':report}
(ROOT/'artifacts/validation/v1.8.3/upgrade.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
print('PASS exact release download, manual confirmation, install/restart, database and image preservation')
print(result)
