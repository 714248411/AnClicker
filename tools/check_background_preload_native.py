"""Load the bundled DLL without binding or sending input to user windows."""
import sys,tempfile,time,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from anclicker.platform import background_preload as preload, background_component_auto as auto
from anclicker.domain.instructions import ExecutionContext
with tempfile.TemporaryDirectory() as folder:
 with patch.dict(os.environ,{'ANCLICKER_DM_CONFIG':str(Path(folder)/'config.json')}),patch.object(auto,'managed_directory',return_value=Path(folder)/'dll'):
  preload.close_preload();start=time.monotonic();preload.start_preload()
  transport=None
  try:
   context=ExecutionContext();transport=preload.take_preloaded(context)
   version=transport.version;pid=transport.process.pid;cold=time.monotonic()-start
   preload.offer_preloaded(transport);transport=None
   start=time.monotonic();reused=preload.take_preloaded(ExecutionContext());warm=time.monotonic()-start
   transport=reused
   assert reused.version==version and reused.process.pid==pid and reused.process.poll() is None
   assert warm<0.5
   print(json.dumps({'passed':True,'version':version,'first_load_seconds':round(cold,3),'reuse_seconds':round(warm,5),'offline':True},ensure_ascii=False))
  finally:
   if transport:transport.close()
   preload.close_preload()
