import os
import subprocess
from pathlib import Path


def test_navigation_timeout_and_replacement(tmp_path):
    root=Path(__file__).resolve().parents[1]
    helper=root/'integrations/yingdao/src/browser-navigation.js'
    script=tmp_path/'navigation.cjs'
    script.write_text("const navigate=require("+repr(str(helper).replace('\\','/'))+");"+r'''
const assert=require('node:assert/strict');
(async()=>{
  const {proxyConfig}=require(process.env.AC_PROXY_MODULE);
  assert.equal(proxyConfig({}),null);
  assert.equal(proxyConfig({HTTPS_PROXY:'http://user:secret@proxy.test:8080'}),null);
  assert.deepEqual(proxyConfig({HTTPS_PROXY:'socks5h://127.0.0.1:1080',NO_PROXY:'localhost,127.0.0.1'}),{proxyRules:'socks5://127.0.0.1:1080',proxyBypassRules:'localhost;127.0.0.1'});
  let stopped=0;
  const wc=Object.assign(new (require('node:events').EventEmitter)(),{loadURL:()=>new Promise(()=>{}),isDestroyed:()=>false,stop:()=>stopped++,send:()=>{},getURL:()=> 'https://new.test/'});
  await assert.rejects(navigate(wc,'https://timeout.test/',20),/超时/);
  assert.equal(stopped,1);
  assert.match(wc.__acNavigationStatus.error,/超时/);
  const first=navigate(wc,'https://old.test/',30).catch(e=>e);
  wc.loadURL=()=>Promise.resolve();
  assert.equal(await navigate(wc,'https://new.test/',100),'https://new.test/');
  await first;
  assert.equal(stopped,1);
  assert.deepEqual(wc.__acNavigationStatus,{requestedUrl:'https://new.test/',url:'https://new.test/',loading:false,error:''});
})().catch(e=>{console.error(e);process.exitCode=1;});
''',encoding='utf-8')
    env=dict(os.environ,ELECTRON_RUN_AS_NODE='1',AC_PROXY_MODULE=str(helper.with_name('browser-proxy.js')))
    subprocess.run([str(root/'runtime/electron/electron.exe'),str(script)],env=env,check=True,timeout=10)
