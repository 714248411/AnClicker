// 独立浏览器窗口的 preload：提供工具栏动作桥 + 缩放 + 录制事件读取
const { contextBridge, ipcRenderer } = require('electron');

// 工具栏动作桥：悬浮工具栏通过它通知主进程
contextBridge.exposeInMainWorld('__rpaSendToMain', (action) => {
  ipcRenderer.send('browser:toolbarAction', action);
});

// 主进程读取录制事件：暴露读取函数
contextBridge.exposeInMainWorld('__rpaReadEvents', () => {
  return ipcRenderer.invoke('browser:consumeEventsFrom', 'self');
});

// Ctrl+滚轮缩放
window.addEventListener('wheel', (e) => {
  if (!e.ctrlKey) return;
  e.preventDefault();
  const delta = e.deltaY < 0 ? 0.5 : -0.5; // 向上滚放大，向下滚缩小
  ipcRenderer.send('browser:zoomBy', delta);
}, { passive: false });

// Capture only during an explicit host recording session; no DOM-injected API.
let acRecording=false;
ipcRenderer.on('ac:recordEnabled',(_e,value)=>{acRecording=!!value;});
ipcRenderer.invoke('ac:recordEnabled').then(value=>{acRecording=!!value;});
function acSelector(el){
  if(el.id && document.querySelectorAll('#'+CSS.escape(el.id)).length===1)return '#'+CSS.escape(el.id);
  const parts=[];
  while(el && el.nodeType===1){
    const tag=el.tagName.toLowerCase();
    const siblings=el.parentElement?Array.from(el.parentElement.children).filter(n=>n.tagName===el.tagName):[el];
    parts.unshift(tag+':nth-of-type('+(siblings.indexOf(el)+1)+')');
    if(tag==='html')break;
    el=el.parentElement;
  }
  return parts.join(' > ');
}
function acCapture(e,type){
  if(!acRecording||!e.isTrusted)return;
  const el=e.target;
  if(!el || !el.tagName || el.closest('[id^="__rpa"]') || el.type==='password')return;
  if(type==='input' && !(el.tagName==='TEXTAREA'||(el.tagName==='INPUT'&&!['checkbox','radio','file'].includes(el.type))))return;
  if(type==='key' && !['Enter','Tab'].includes(e.key))return;
  if(type==='click' && e.detail===0)return; // Enter already records this activation.
  ipcRenderer.send('ac:recordEvent',{type,selector:acSelector(el),text:type==='input'?el.value:'',key:e.key});
}
document.addEventListener('click',e=>acCapture(e,'click'),true);
document.addEventListener('input',e=>acCapture(e,'input'),true);
document.addEventListener('keydown',e=>acCapture(e,'key'),true);

contextBridge.exposeInMainWorld('__rpaOnZoom', cb => ipcRenderer.on('ac:zoomLevel', (_e,value)=>cb(value)));
