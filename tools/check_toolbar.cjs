require('fs').mkdirSync(require('path').join(__dirname,'../artifacts/validation'),{recursive:true});
const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path');
const install=require('../integrations/yingdao/src/ac-toolbar');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
app.whenReady().then(async()=>{
 let win;
 try{
  win=new BrowserWindow({width:1000,height:650,webPreferences:{contextIsolation:true}});
  await win.loadURL('data:text/html,<body><h1>Toolbar hover validation</h1></body>');
  const js=code=>win.webContents.executeJavaScript(code,true);
  await js('('+install.toString()+')(0)');
  const state=()=>js('({hidden:document.querySelector("#__rpa_toolbar_panel").hidden,top:document.querySelector("#__rpa_toolbar").getBoundingClientRect().top,right:innerWidth-document.querySelector("#__rpa_toolbar").getBoundingClientRect().right})');
  const event=name=>js('document.querySelector("#__rpa_toolbar").dispatchEvent(new MouseEvent('+JSON.stringify(name)+'))');
  if(!(await state()).hidden)throw Error('Initially visible');
  await event('mouseenter');await pause(400);await event('mouseleave');await pause(2100);
  if(!(await state()).hidden)throw Error('Short hover should cancel');
  await event('mouseenter');await pause(1800);
  if(!(await state()).hidden)throw Error('Opened before 2 seconds');
  await pause(300);
  const visible=await state();if(visible.hidden||visible.top!==6||visible.right!==6)throw Error('Wrong position/state');
  fs.writeFileSync(path.join(__dirname,'../artifacts/validation/toolbar-expanded.png'),(await win.webContents.capturePage()).toPNG());
  await event('mouseleave');await pause(400);if(!(await state()).hidden)throw Error('Did not hide');
  fs.writeFileSync(path.join(__dirname,'../artifacts/validation/toolbar-hidden.png'),(await win.webContents.capturePage()).toPNG());
  fs.writeFileSync(path.join(__dirname,'../artifacts/validation/toolbar-report.json'),JSON.stringify({hoverDelay:2000,cancelledShortHover:true,hiddenOnLeave:true,position:visible}));
  win.close();app.exit(0);
 }catch(e){fs.writeFileSync(path.join(__dirname,'../artifacts/validation/toolbar-error.txt'),String(e.stack));if(win)win.close();app.exit(1);}
});
