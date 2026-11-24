'use strict';
const {app,BrowserView,ipcMain,clipboard}=require('electron');
const fs=require('fs'),path=require('path');
const notices=new Map();
function report(error,source='JavaScript',page=null){
 const detail=String(error&&error.stack||error&&error.message||error);
 const notice={retrying:source==='navigation-retry',message:String(error&&error.message||error),detail:new Date().toISOString()+' ['+source+']\n'+detail};
 try{process.emit('ac:runtime-error',notice);}catch(_){}
 try{
  const folder=path.join(app.getPath('userData'),'logs');fs.mkdirSync(folder,{recursive:true});
  const file=path.join(folder,'javascript-errors.log');
  if(fs.existsSync(file)&&fs.statSync(file).size>2*1024*1024)fs.renameSync(file,file+'.previous');
  fs.appendFileSync(file,notice.detail+'\n\n','utf8');
 }catch(_){/* Reporting an error must never cause another uncaught error. */}
 for(const owner of notices.values())if(!page||owner.page===page)owner.show(notice);
 return notice;
}
process.on('uncaughtException',error=>report(error,'uncaughtException'));
process.on('unhandledRejection',error=>report(error,'unhandledRejection'));
ipcMain.handle('ac:runtimeNotice',async(event,action)=>{
 const owner=notices.get(event.sender.id);
 if(!owner||event.senderFrame!==event.sender.mainFrame)return {ok:false};
 if(action==='copy'){clipboard.writeText(owner.notice?owner.notice.detail:'');return {ok:true};}
 if(action==='dismiss'){owner.hide();return {ok:true};}
 if(action==='state'){owner.publish();return {ok:true};}
 if(action==='reconnect'){
  if(owner.reconnecting||(owner.notice&&owner.notice.retrying))return {ok:true};
  owner.reconnecting=true;owner.publish();
  try{await owner.reconnect();owner.hide();return {ok:true};}
  catch(error){report(error,'reconnect');return {ok:false};}
  finally{owner.reconnecting=false;owner.publish();}
 }
 return {ok:false};
});
function attach(win,reconnect){
 const view=new BrowserView({webPreferences:{preload:path.join(__dirname,'runtime-notice-preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
 let shown=false;
 const owner={page:win.webContents,notice:null,reconnecting:false,reconnect,
  publish(){if(!view.webContents.isDestroyed())view.webContents.send('ac:runtimeNoticeState',{...(this.notice||{}),reconnecting:this.reconnecting||!!(this.notice&&this.notice.retrying)});},
  show(notice){if(win.isDestroyed())return;this.notice=notice;if(!shown){win.addBrowserView(view);shown=true;}resize();this.publish();},
  hide(){if(shown&&!win.isDestroyed())win.removeBrowserView(view);shown=false;this.notice=null;}
 };
 function resize(){if(!shown||win.isDestroyed())return;const [width,height]=win.getContentSize();const h=Math.min(height,width<650?94:62);view.setBounds({x:0,y:Math.max(0,height-h),width:Math.max(1,width),height:h});}
 function recovered(){if(owner.notice){owner.notice.retrying=false;owner.publish();}}
 owner.page.on('ac:recovery-finished',recovered);
 notices.set(view.webContents.id,owner);win.on('resize',resize);
 const id=view.webContents.id;
 win.once('closed',()=>{owner.page.removeListener('ac:recovery-finished',recovered);notices.delete(id);if(!view.webContents.isDestroyed())view.webContents.destroy();});
 view.webContents.setWindowOpenHandler(()=>({action:'deny'}));
 view.webContents.on('will-navigate',event=>event.preventDefault());
 view.webContents.on('did-finish-load',()=>owner.publish());
 view.webContents.loadFile(path.join(__dirname,'runtime-notice.html')).catch(error=>{
  try{fs.appendFileSync(path.join(app.getPath('userData'),'engine-startup.log'),String(error)+'\n');}catch(_){}
 });
 return owner;
}
module.exports={report,attach};
