'use strict';
const assert=require('assert/strict');
const {app,BrowserWindow,nativeTheme,webContents}=require('electron');
const {createThemedBrowserWindow}=require('../integrations/yingdao/src/browser-window-theme');
const attach=require('../integrations/yingdao/src/browser-controls');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
app.whenReady().then(async()=>{let win,other;try{
 win=createThemedBrowserWindow({width:800,height:600,title:'极速网页AC1',webPreferences:{sandbox:true,contextIsolation:true}});
 await win.webContents.loadURL('data:text/html,<button id="hit" style="position:fixed;left:0;top:0" onclick="this.textContent=123">hit</button>');
 attach(win,{normalizeUrl:x=>x,navigate:async()=>{},markNavigation:()=>{}});
 other=new BrowserWindow({width:200,height:150,show:false});
 await pause(200);
 const shell=webContents.getAllWebContents().find(w=>w.getURL().endsWith('/browser-caption.html')&&BrowserWindow.fromWebContents(w)===win);
 assert(shell);assert.notEqual(shell.id,win.webContents.id);
 for(const mode of ['light','dark']){
  nativeTheme.themeSource=mode;
  for(const focused of [false,true,false,true]){
   (focused?win:other).show();(focused?win:other).focus();await pause(150);
   assert.equal(win.isFocused(),focused);
   const actual=await shell.executeJavaScript('getComputedStyle(document.documentElement).backgroundColor');
   assert.equal(actual,mode==='dark'?(focused?'rgb(9, 9, 11)':'rgb(24, 24, 27)'):(focused?'rgb(247, 247, 248)':'rgb(241, 241, 243)'));
  }
 }
 win.setSize(950,700);await pause(150);
 const page=win.getBrowserViews().find(v=>v.webContents===win.webContents);
 const controls=win.getBrowserViews().find(v=>v!==page);
 assert.equal(page.getBounds().y,32);assert.equal(controls.getBounds().y,38);
 const viewport=await win.webContents.executeJavaScript('({w:innerWidth,h:innerHeight})');
 assert.equal(viewport.h,win.getContentSize()[1]-32);assert.equal(viewport.w,win.getContentSize()[0]);
 win.webContents.sendInputEvent({type:'mouseDown',x:10,y:10,button:'left',clickCount:1});
 win.webContents.sendInputEvent({type:'mouseUp',x:10,y:10,button:'left',clickCount:1});await pause(50);
 assert.equal(await win.webContents.executeJavaScript('document.getElementById("hit").textContent'),'123');
 const pageContents=win.webContents;
 win.destroy();await pause(150);assert(pageContents.isDestroyed());other.destroy();
 console.log('PASS real light/dark focus transitions, exact theme colors, resize, control offset, page-coordinate click and cleanup');app.exit(0);
}catch(e){console.error(e);if(win&&!win.isDestroyed())win.destroy();if(other&&!other.isDestroyed())other.destroy();app.exit(1);}});
