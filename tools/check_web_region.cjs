const {app,BrowserWindow}=require('electron');
const http=require('http');const path=require('path');
const {execute}=require(path.join(process.argv[2],'integrations/yingdao/src/ac-region.js'));
const assert=require('assert');let server,win;
app.whenReady().then(async()=>{
 try{
  server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<html><title>选区测试</title><body style="margin:0;height:1600px;font:20px Arial"><div id="target" style="position:absolute;left:30px;top:30px">TARGET 中文</div><div style="position:absolute;left:500px;top:30px">OUTSIDE</div><a href="/link" style="position:absolute;left:30px;top:80px">选区链接</a><input type="password" value="secret" style="position:absolute;left:30px;top:130px"><div style="position:absolute;left:30px;top:200px">BOTTOM</div></body></html>');});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  win=new BrowserWindow({show:false,width:900,height:700,webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});
  await win.loadURL('http://127.0.0.1:'+server.address().port);
  const picking=execute(win.webContents,{action:'select'});
  await new Promise(resolve=>setTimeout(resolve,150));
  win.webContents.sendInputEvent({type:'mouseDown',button:'left',clickCount:1,x:20,y:20});
  win.webContents.sendInputEvent({type:'mouseMove',x:270,y:170});
  win.webContents.sendInputEvent({type:'mouseUp',button:'left',clickCount:1,x:270,y:170});
  const picked=await Promise.race([picking,new Promise((_,reject)=>setTimeout(()=>reject(new Error('picker timed out')),3000))]);
  assert.equal(picked.x,20);assert.equal(picked.w,250);assert.equal(picked.h,150);
  const cancelling=assert.rejects(execute(win.webContents,{action:'select'}),/取消/);
  await new Promise(resolve=>setTimeout(resolve,150));
  win.webContents.sendInputEvent({type:'keyDown',keyCode:'ESC'});
  await Promise.race([cancelling,new Promise((_,reject)=>setTimeout(()=>reject(new Error('cancel timed out')),3000))]);
  const geometry=await execute(win.webContents,{action:'geometry'});
  const region={...geometry,x:20,y:20,w:250,h:150};
  const result=await execute(win.webContents,{action:'extract',region,maxChars:20000});
  assert(result.layout.items.some(item=>item.text.includes('TARGET 中文')&&Math.abs(item.x-10)<1));assert.equal(result.layout.width,250);assert(result.text.includes('TARGET 中文'));assert(!result.text.includes('OUTSIDE'));assert(!result.text.includes('BOTTOM'));assert(!result.text.includes('secret'));assert.equal(result.links.length,1);
  await win.webContents.executeJavaScript(`const table=document.createElement('table');table.style='position:absolute;left:20px;top:270px;width:400px;table-layout:fixed;border-collapse:collapse';table.innerHTML='<tr><th>名称</th><th>内容</th></tr><tr><td rowspan="2">合并</td><td>第一行</td></tr><tr><td>第二行</td></tr>';document.body.append(table)`);
  const tabular=await execute(win.webContents,{action:'extract',region:{...geometry,x:0,y:260,w:460,h:180},maxChars:20000});
  assert.equal(tabular.tables.length,1);assert.equal(tabular.tables[0].rows.length,2);
  assert.equal(tabular.tables[0].layout.columns.length,2);assert(tabular.tables[0].layout.cells.some(cell=>cell.rowspan===2));
  assert.deepEqual(tabular.tables[0].rows,[['合并','第一行'],['合并','第二行']]);
  await assert.rejects(execute(win.webContents,{action:'extract',region:{...region,width:region.width+2},maxChars:20000}),/变化/);
  await win.webContents.executeJavaScript('window.scrollTo(0,200)');
  await assert.rejects(execute(win.webContents,{action:'extract',region,maxChars:20000}),/变化/);
  await win.webContents.executeJavaScript('window.scrollTo(0,0);let f=document.createElement("iframe");f.style="position:absolute;left:20px;top:20px;width:100px;height:100px";document.body.append(f)');
  await assert.rejects(execute(win.webContents,{action:'extract',region,maxChars:20000}),/无法可靠/);
  console.log('PASS bundled browser region bounds, Chinese text, links, hidden inputs, resize/scroll guards and iframe warning');
 }catch(e){console.error(e);process.exitCode=1;}
 finally{if(win&&!win.isDestroyed())win.destroy();if(server)server.close();app.quit();}
});
