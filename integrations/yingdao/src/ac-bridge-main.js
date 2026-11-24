'use strict';
const {app, ipcMain, nativeTheme} = require('electron');
function applyTheme(value){if(value==='dark'||value==='light')nativeTheme.themeSource=value;}
applyTheme(process.env.ANCLICKER_UI_THEME);
const net = require('net');
const readline = require('readline');
let owner;
const port = Number(process.env.ANCLICKER_RPA_PORT);
if (!port || !process.env.ANCLICKER_RPA_TOKEN) throw new Error('请从 AnClicker 启动自动化引擎');
const socket = net.connect({host:'127.0.0.1',port});
const respond = data => { if(!socket.destroyed&&socket.writable)socket.write(JSON.stringify(data) + '\n'); };
let chromeConnected=false;
const refreshChrome=()=>{if(chromeConnected)respond({event:'browser_chrome'});};
app.on('browser-window-created',(_event,win)=>{
  setImmediate(refreshChrome);
  win.on('show',refreshChrome);
  win.on('focus',refreshChrome);
  win.on('blur',refreshChrome);
});
nativeTheme.on('updated',refreshChrome);
process.on('ac:runtime-error',notice=>respond({event:'runtime_notice',logs:[notice.detail]}));
socket.on('connect', () => {respond({token:process.env.ANCLICKER_RPA_TOKEN});chromeConnected=true;refreshChrome();});
socket.on('error', () => app.quit());
socket.on('close', () => app.quit());
module.exports.attach = win => { owner = win; };
ipcMain.on('ac:ready', e => { if (owner && e.sender === owner.webContents) respond({ready:true}); });
ipcMain.on('ac:response', (e, msg) => { if (owner && e.sender === owner.webContents) respond(msg); });
readline.createInterface({input:socket}).on('line', line => {
  try {
    const msg = JSON.parse(line);
    applyTheme(msg.theme);
    if (msg.operation === 'theme') return;
    if (msg.operation === 'shutdown') { app.quit(); return; }
    if (!owner || owner.isDestroyed()) throw new Error('执行引擎尚未就绪');
    owner.webContents.send('ac:request', msg);
  } catch (e) { respond({error:e.message}); }
});
