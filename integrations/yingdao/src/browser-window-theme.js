'use strict';
const {BrowserWindow,BrowserView,nativeTheme}=require('electron');
const path=require('path');
// Use the same background and surface colors as the workspace palette.
function colors(dark,focused){return {background:dark?(focused?'#09090b':'#18181b'):(focused?'#f7f7f8':'#f1f1f3'),text:dark?'#f1f1f3':'#2f2f2f'};}
function createThemedBrowserWindow(options){
  if(process.platform!=='win32')return new BrowserWindow(options);
  const visible=options.show!==false;
  const initial=colors(nativeTheme.shouldUseDarkColors,false);
  const win=new BrowserWindow({...options,show:false,titleBarStyle:'hidden',titleBarOverlay:{color:initial.background,symbolColor:initial.text,height:32},backgroundColor:initial.background,webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}});
  const shell=win.webContents;
  const page=new BrowserView({webPreferences:options.webPreferences});
  // Keep all existing automation, recording and CDP users on the remote page.
  // The local shell is private and never navigates to remote content.
  Object.defineProperty(win,'webContents',{value:page.webContents});
  win.addBrowserView(page);
  win.__acCaptionHeight=32;
  function resize(){
    if(win.isDestroyed())return;
    win.__acCaptionHeight=win.isFullScreen()?0:32;
    const [width,height]=win.getContentSize();
    page.setBounds({x:0,y:win.__acCaptionHeight,width:Math.max(1,width),height:Math.max(1,height-win.__acCaptionHeight)});
  }
  function repaint(){
    if(win.isDestroyed())return;
    const palette=colors(nativeTheme.shouldUseDarkColors,win.isFocused());
    win.setTitleBarOverlay({color:palette.background,symbolColor:palette.text,height:32});
    win.setBackgroundColor(palette.background);
    if(!shell.isDestroyed())shell.executeJavaScript('document.documentElement.style.background='+JSON.stringify(palette.background)+';document.body.style.color='+JSON.stringify(palette.text)+';document.getElementById("title").textContent='+JSON.stringify(options.title||'极速网页AC')+';').catch(()=>{});
  }
  win.on('resize',resize);
  win.on('enter-full-screen',resize);
  win.on('leave-full-screen',resize);
  win.on('focus',repaint);win.on('blur',repaint);
  nativeTheme.on('updated',repaint);
  shell.on('did-finish-load',repaint);
  shell.setWindowOpenHandler(()=>({action:'deny'}));
  shell.on('will-navigate',event=>event.preventDefault());
  win.once('closed',()=>{nativeTheme.removeListener('updated',repaint);if(!page.webContents.isDestroyed())page.webContents.destroy();});
  resize();
  shell.loadFile(path.join(__dirname,'browser-caption.html')).catch(()=>{});
  if(visible)win.show();
  return win;
}
module.exports={createThemedBrowserWindow,colors};
