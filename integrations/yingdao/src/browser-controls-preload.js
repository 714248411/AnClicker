'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('browserControls',{
  call:(action,value)=>ipcRenderer.invoke('ac:browserControls',action,value),
  onState:callback=>ipcRenderer.on('ac:browserState',(_event,state)=>callback(state))
});
