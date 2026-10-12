'use strict';
const {ipcMain} = require('electron');
let state = {active:false,events:[],elapsed:0,full:false};
let started = 0, owner, manualNavigation=false;
const elapsed = () => Math.max(0, performance.now() - started);
function push(event) {
  if (!state.active) return;
  if (state.events.length >= 10000) { state.full=true; state.elapsed=elapsed(); state.active=false; return; }
  state.events.push({...event,at:elapsed()});
}
function attach(wc) {
  wc.on('dom-ready',()=>{if(owner===wc && state.active)wc.send('ac:recordEnabled',true);});
  wc.on('did-start-navigation', (_e,url,inPlace,isMainFrame) => {
    if (owner===wc && state.active && isMainFrame && !inPlace) { push({type:manualNavigation?'directNavigation':'navigation',url});manualNavigation=false; }
  });
  wc.setWindowOpenHandler(({url}) => {
    if (owner===wc && state.active) { wc.loadURL(url).catch(()=>{}); return {action:'deny'}; }
    return {action:'allow'};
  });
  wc.on('destroyed',()=>{if(owner===wc){state.elapsed=elapsed();state.active=false;owner=null;}});
}
ipcMain.on('ac:recordEvent', (e,event) => {
  if(e.sender!==owner || !state.active || !event || !['click','input','key'].includes(event.type)) return;
  if(typeof event.selector!=='string' || event.selector.length>4096) return;
  if(event.type==='key' && !['Enter','Tab'].includes(event.key)) return;
  push({type:event.type,selector:event.selector,text:String(event.text||'').slice(0,100000),key:event.key});
});
ipcMain.handle('ac:recordEnabled', e => e.sender===owner && state.active);
function start(wc) {
  if(!wc || wc.isDestroyed()) throw new Error('请先打开录制网页');
  owner=wc;started=performance.now();state={active:true,events:[],elapsed:0,full:false};
  wc.send('ac:recordEnabled',true);
  return {url:wc.getURL(),active:true};
}
function status(){return {active:state.active,count:state.events.length,elapsed:state.active?elapsed():state.elapsed,full:state.full,events:state.events.slice()};}
function stop(){if(state.active)state.elapsed=elapsed();state.active=false;if(owner&&!owner.isDestroyed())owner.send('ac:recordEnabled',false);return {...status(),events:state.events.slice()};}
module.exports={attach,start,status,stop,markNavigation(wc){if(owner===wc)manualNavigation=true;}};
