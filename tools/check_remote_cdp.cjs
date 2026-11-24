const assert=require('assert/strict'),fs=require('fs'),path=require('path'),os=require('os'),http=require('http'),{spawn}=require('child_process');
const remote=require('../integrations/yingdao/src/remote-cdp'),input=require('../integrations/yingdao/src/background-input');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'ac-remote-cdp-'));
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<title>External CDP Fixture</title><input id="field" style="position:absolute;left:20px;top:20px;width:200px;height:40px"><button id="button" style="position:absolute;left:20px;top:100px;width:200px;height:40px">click</button><script>window.keyTimes=[];document.addEventListener("keydown",e=>{if(e.key==="a"&&!e.ctrlKey)window.keyTimes.push(performance.now())});window.clicks=0;document.querySelector("#button").onclick=e=>{window.clicks++;window.trusted=e.isTrusted}</script>');});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port;
 const child=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=new','--remote-debugging-port=0','--user-data-dir='+folder,'--no-first-run','--no-default-browser-check',base+'/one'],{windowsHide:true,stdio:'ignore'});
 let client;
 try{
  let port;
  for(let i=0;i<100;i++){try{port=Number(fs.readFileSync(path.join(folder,'DevToolsActivePort'),'utf8').split('\n')[0]);if(port)break;}catch(_){}await delay(100);}
  assert(port,'fixture browser failed to start');
  const endpoint='http://127.0.0.1:'+port;
  let pages=await remote.list([{endpoint,browser:'Chrome'}]);assert.equal(pages.length,1);
  const one=pages[0];client=await remote.connect(one);
  await client.send('Target.createTarget',{url:base+'/two'});
  pages=await remote.list([{endpoint},{endpoint}]);assert.equal(pages.length,2,'deduplicate endpoints');
  await client.evaluate('document.readyState');
  const result=await new Promise(resolve=>{
   const py=spawn(path.resolve('.venv-build/Scripts/python.exe'),['-B','-X','utf8','tools/check_external_bridge.py',endpoint],{windowsHide:true});let out='';py.stdout.on('data',d=>out+=d);py.stderr.on('data',d=>out+=d);py.on('close',code=>resolve({code,out}));
  });assert.equal(result.code,0,result.out);console.log(result.out.trim());
  assert.equal(await client.evaluate('document.querySelector("#field").value'),'aaaaa');
  const keyTimes=await client.evaluate('window.keyTimes');assert.equal(keyTimes.length,5);
  for(let i=1;i<keyTimes.length;i++)assert(keyTimes[i]-keyTimes[i-1]>=90,'0.1 second key interval');
  console.log('PASS aaaaa sends five separate keys with 0.1 second intervals');
  assert.equal(await client.evaluate('window.clicks'),2);assert.equal(await client.evaluate('window.trusted'),true);
  const two=pages.find(p=>p.url.endsWith('/two'));
  assert.equal(await remote.withTarget(two,c=>c.evaluate('document.querySelector("#field").value')),'');
  await assert.rejects(remote.connect({...one,id:'missing',url:'http://missing.invalid'}),/关闭|唯一/);
  assert.throws(()=>remote.endpointUrl('http://example.com:9222'),/本机/);
  await client.send('Target.closeTarget',{targetId:two.id});
  assert.equal((await remote.list([{endpoint}])).length,1);
  console.log('PASS independent external browser discovery, multi-tab isolation, real input, missing target and closed-tab refresh');
 }finally{
  if(client){await client.send('Browser.close').catch(()=>{});client.close();}
  if(child.exitCode===null)await Promise.race([new Promise(r=>child.once('exit',r)),delay(3000)]);
  if(child.exitCode===null)child.kill();server.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1});
