const {app,BrowserWindow,clipboard}=require('electron');
const fs=require('fs'),os=require('os'),path=require('path'),assert=require('assert');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'ac-notice-'));app.setPath('userData',dir);
const notices=require('../integrations/yingdao/src/runtime-notices');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
app.whenReady().then(async()=>{
 let win;const old=clipboard.readText();
 try{
  win=new BrowserWindow({show:false,width:850,height:600});let reconnected=0;
  const owner=notices.attach(win,async()=>{reconnected++;});
  process.emit('uncaughtException',Object.assign(Error('read ECONNRESET'),{code:'ECONNRESET'}));
  await pause(600);
  assert.equal(win.getBrowserViews().length,1);
  const wc=win.getBrowserViews()[0].webContents;
  assert((await wc.executeJavaScript('document.body.innerText')).includes('read ECONNRESET'));
  await wc.executeJavaScript('document.getElementById("copy").click()');await pause(50);
  assert(clipboard.readText().includes('ECONNRESET'));
  await wc.executeJavaScript('document.getElementById("reconnect").click()');await pause(100);
  assert.equal(reconnected,1);assert.equal(win.getBrowserViews().length,0);
  process.emit('unhandledRejection',Error('ERR_NETWORK_CHANGED'));
  assert.equal(win.getBrowserViews().length,1);
  assert(fs.readFileSync(path.join(dir,'logs/javascript-errors.log'),'utf8').includes('ERR_NETWORK_CHANGED'));
  notices.report(Error('retry ECONNRESET'),'navigation-retry',win.webContents);await pause(50);
  assert(await wc.executeJavaScript('document.getElementById("reconnect").disabled'));
  win.webContents.emit('ac:recovery-finished');await pause(50);
  assert(!(await wc.executeJavaScript('document.getElementById("reconnect").disabled')));
  owner.hide();win.destroy();clipboard.writeText(old);
  require('fs').writeFileSync(require('path').join(__dirname,'../artifacts/validation/check_runtime_notices.cjs.passed'),'PASS');console.log('PASS uncaught/rejected network errors, bottom notification, copy, reconnect, log and process survival');app.exit(0);
 }catch(error){console.error(error);clipboard.writeText(old);if(win&&!win.isDestroyed())win.destroy();app.exit(1);}
});
