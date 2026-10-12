const {app,BrowserWindow}=require('electron');
const http=require('http');
const assert=require('assert');
const attach=require('../integrations/yingdao/src/browser-controls');
const navigate=require('../integrations/yingdao/src/browser-navigation');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){const end=Date.now()+8000;while(Date.now()<end){if(await fn())return;await pause(50);}throw Error('condition timed out');}
let win,server;
app.whenReady().then(async()=>{
 try{
 server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<div id="result">'+req.url+'</div>');});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port;
 win=new BrowserWindow({width:900,height:600,webPreferences:{contextIsolation:true}});
 attach(win,{normalizeUrl(value){const u=new URL(value);if(!['http:','https:'].includes(u.protocol))throw Error('仅支持 http 或 https');return u.href;},navigate,markNavigation(){}});
 await navigate(win.webContents,base+'/first');
 const bar=win.getBrowserView().webContents;
 await until(()=>bar.executeJavaScript('!!document.getElementById("trigger")').catch(()=>false));
 await bar.executeJavaScript('document.getElementById("trigger").click()');
 await until(()=>bar.executeJavaScript('!document.getElementById("panel").hidden'));
 async function enter(url){await bar.executeJavaScript('document.getElementById("address").value='+JSON.stringify(url)+';document.getElementById("address").focus()');win.focus();bar.focus();await pause(100);bar.sendInputEvent({type:'keyDown',keyCode:'Return'});bar.sendInputEvent({type:'char',keyCode:'\r'});bar.sendInputEvent({type:'keyUp',keyCode:'Return'});}
 await enter(base+'/second');await until(()=>win.webContents.getURL()===base+'/second');
 assert.equal(await win.webContents.executeJavaScript('document.getElementById("result").textContent'),'/second');
 await enter('file:///bad');await until(()=>bar.executeJavaScript('document.getElementById("status").textContent.includes("http")'));
 assert.equal(win.webContents.getURL(),base+'/second');
 await enter(base+'/recovered');await until(()=>win.webContents.getURL()===base+'/recovered');
 const closed=http.createServer();await new Promise(r=>closed.listen(0,'127.0.0.1',r));const port=closed.address().port;await new Promise(r=>closed.close(r));
 await enter('http://127.0.0.1:'+port);await until(()=>bar.executeJavaScript('document.getElementById("status").textContent.includes("ERR_CONNECTION_REFUSED")'));
 await enter(base+'/retry');await until(()=>win.webContents.getURL()===base+'/retry');
 await bar.executeJavaScript('document.getElementById("trigger").click()');
 await until(()=>bar.executeJavaScript('document.getElementById("panel").hidden'));
 console.log('Native address Enter, invalid scheme, connection failure, recovery, toggle: passed');
 win.destroy();server.close();app.exit(0);
 }catch(e){require('fs').writeFileSync(require('path').join(__dirname,'../validation/v150-address-error.txt'),String(e.stack));console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();if(server)server.close();app.exit(1);}
});
