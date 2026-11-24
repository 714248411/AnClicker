import sys,json,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.packaging.ai_bundle import identity,verify
candidate=ROOT/'artifacts/dist/v1.7.3-ai-candidate/AnClicker'
verify(ROOT,candidate)
with tempfile.TemporaryDirectory(dir=ROOT/'artifacts/debug/v173-optimize') as temporary:
 target=Path(temporary);manifest=identity(ROOT)
 for name in manifest['resources']:
  destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);os.link(ROOT/name,destination)
 path=target/'ai-build-manifest.json';path.write_text(json.dumps(manifest),encoding='utf8');verify(ROOT,target)
 manifest['sources']['main.py']='stale';path.write_text(json.dumps(manifest),encoding='utf8')
 try:verify(ROOT,target)
 except RuntimeError:pass
 else:raise AssertionError('stale build accepted')
 path.write_text(json.dumps(identity(ROOT)),encoding='utf8');(target/'models/correction_cases.json').unlink()
 try:verify(ROOT,target)
 except RuntimeError:pass
 else:raise AssertionError('missing correction data accepted')
print('PASS candidate identity, stale build rejection, missing correction data rejection')

import tools.package_release_173 as release
with tempfile.TemporaryDirectory() as temporary:
 release.DIST=candidate;release.VALIDATION=Path(temporary)
 (release.VALIDATION/'smoke-passed.json').write_text(json.dumps({'passed':True,'version':'1.7.3'}),encoding='utf8')
 try:release.package()
 except RuntimeError as error:assert 'Smoke proof' in str(error)
 else:raise AssertionError('unbound old smoke proof accepted')
print('PASS old smoke proof rejected before packaging')
