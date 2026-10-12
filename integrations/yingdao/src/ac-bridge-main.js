'use strict';
const {app, ipcMain} = require('electron');
const net = require('net');
const readline = require('readline');
let owner;
const port = Number(process.env.ANCLICKER_RPA_PORT);
if (!port || !process.env.ANCLICKER_RPA_TOKEN) throw new Error('请从 AnClicker 启动自动化引擎');
const socket = net.connect({host:'127.0.0.1',port});
const respond = data => socket.write(JSON.stringify(data) + '\n');
socket.on('connect', () => respond({token:process.env.ANCLICKER_RPA_TOKEN}));
socket.on('error', () => app.quit());
socket.on('close', () => app.quit());
module.exports.attach = win => { owner = win; };
ipcMain.on('ac:ready', e => { if (owner && e.sender === owner.webContents) respond({ready:true}); });
ipcMain.on('ac:response', (e, msg) => { if (owner && e.sender === owner.webContents) respond(msg); });
readline.createInterface({input:socket}).on('line', line => {
  try {
    const msg = JSON.parse(line);
    if (msg.operation === 'shutdown') { app.quit(); return; }
    if (!owner || owner.isDestroyed()) throw new Error('执行引擎尚未就绪');
    owner.webContents.send('ac:request', msg);
  } catch (e) { respond({error:e.message}); }
});
