'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('runtimeNotice',{call:action=>ipcRenderer.invoke('ac:runtimeNotice',action),onState:callback=>ipcRenderer.on('ac:runtimeNoticeState',(_event,state)=>callback(state))});
