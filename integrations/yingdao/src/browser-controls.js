'use strict';
const {BrowserView,ipcMain}=require('electron');
const path=require('path');
const owners=new Map();
ipcMain.handle('ac:browserControls',async(event,action,value)=>{
  const owner=owners.get(event.sender.id);
  if(!owner || event.senderFrame!==event.sender.mainFrame)return {ok:false,error:'浏览器控制栏已关闭'};
  try{return {ok:true,result:await owner.action(action,value)};}
  catch(error){return {ok:false,error:String(error.message||error)};}
});
module.exports=function attachControls(win,{normalizeUrl,navigate,markNavigation}){
  const page=win.webContents;
  const view=new BrowserView({webPreferences:{preload:path.join(__dirname,'browser-controls-preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  view.setBackgroundColor('#00000000');
  win.setBrowserView(view);
  let expanded=false, disposed=false;
  const state={url:'',requestedUrl:'',loading:false,error:'',zoom:100,canBack:false,canForward:false};
  function resize(){
    if(disposed||win.isDestroyed())return;
    const [width,height]=win.getContentSize();
    const w=expanded?Math.max(1,width-12):Math.min(32,Math.max(1,width-12));
    view.setBounds({x:Math.max(0,width-w-6),y:6,width:w,height:Math.min(34,Math.max(1,height-6))});
  }
  function publish(){
    if(disposed||page.isDestroyed())return;
    state.zoom=Math.round(page.getZoomFactor()*100);
    state.canBack=page.canGoBack();state.canForward=page.canGoForward();
    if(!view.webContents.isDestroyed())view.webContents.send('ac:browserState',{...state});
  }
  function showError(error,url){
    state.loading=false;state.error=String(error.message||error);state.requestedUrl=url||state.requestedUrl;
    publish();
  }
  async function open(value){
    const url=normalizeUrl(String(value||''));
    if(url==='about:blank')throw Error('请填写网页地址');
    markNavigation(page);
    return navigate(page,url);
  }
  const owner={async action(action,value){
    if(disposed)throw Error('浏览器窗口已关闭');
    if(action==='state'){publish();return {...state};}
    if(action==='expand'){expanded=!!value;resize();return;}
    if(action==='open'){try{return await open(value);}catch(error){if(error.code!=='NAVIGATION_REPLACED')showError(error,String(value||''));throw error;}}
    if(action==='back'){if(page.canGoBack()){markNavigation(page);page.goBack();}return;}
    if(action==='forward'){if(page.canGoForward()){markNavigation(page);page.goForward();}return;}
    if(action==='reload')return open(state.url||state.requestedUrl);
    if(action==='stop'){page.stop();state.loading=false;publish();return;}
    if(action==='zoom'){page.setZoomLevel(Math.max(-3,Math.min(4,page.getZoomLevel()+(Number(value)||0))));publish();return;}
    throw Error('未知浏览器操作');
  }};
  owners.set(view.webContents.id,owner);
  const listeners=[];
  function listen(name,fn){page.on(name,fn);listeners.push([name,fn]);}
  listen('ac:navigation-state',change=>{
    Object.assign(state,change);
    publish();
  });
  listen('did-start-navigation',(_e,url,inPlace,isMain)=>{
    if(!isMain||inPlace)return;
    Object.assign(state,{requestedUrl:url,loading:true,error:''});publish();
  });
  listen('did-navigate',(_e,url)=>{state.url=url;publish();});
  listen('did-navigate-in-page',(_e,url,isMain)=>{if(isMain){state.url=url;publish();}});
  listen('did-stop-loading',()=>{state.loading=false;publish();});
  listen('did-fail-load',(_e,code,description,url,isMain)=>{
    if(isMain&&code!==-3)showError(description+' ('+code+')',url);
  });
  page.setWindowOpenHandler(({url})=>{
    open(url).catch(error=>showError(error,url));
    return {action:'deny'};
  });
  win.on('resize',resize);
  view.webContents.on('did-finish-load',publish);
  view.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  view.webContents.on('will-navigate',e=>e.preventDefault());
  const viewId=view.webContents.id;
  win.once('closed',()=>{
    disposed=true;owners.delete(viewId);
    for(const [name,fn] of listeners)page.removeListener(name,fn);
    if(!view.webContents.isDestroyed())view.webContents.destroy();
  });
  resize();
  view.webContents.loadFile(path.join(__dirname,'browser-controls.html')).catch(()=>{
    if(!win.isDestroyed())win.setTitle('极速网页AC（地址栏加载失败，请重新打开窗口）');
  });
};
