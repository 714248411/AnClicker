'use strict';
const { app, BrowserWindow } = require('electron');
const path = require('path');
app.setPath('userData', path.resolve(process.argv[2]));
app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1');
app.commandLine.appendSwitch('remote-debugging-port', '0');
let window;
app.whenReady().then(() => {
  window = new BrowserWindow({ show: false, webPreferences: {
    nodeIntegration: false, contextIsolation: true, sandbox: true
  }});
  window.loadURL('about:blank');
});
app.on('window-all-closed', () => app.quit());
