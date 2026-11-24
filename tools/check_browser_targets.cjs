const assert=require('assert/strict');
const {listTargets}=require('../integrations/yingdao/src/browser-targets');
const win=(id,closed=false)=>({id,win:{isDestroyed:()=>closed,webContents:{isDestroyed:()=>false,getURL:()=> 'https://test/'+id,getTitle:()=>id}}});
(async()=>{
 const ext={isRunning:()=>true,info:()=>({kind:'Edge'}),listPages:async()=>[{id:'e1',title:'external',url:'https://external'}]};
 let r=await listTargets([win('b1'),win('closed',true),win('popup')],ext,'session');
 assert.deepEqual(r.pages.map(p=>p.id),['b1','popup','e1']);
 assert.deepEqual(r.pages.map(p=>p.engine),['内置','内置','Edge']);
 ext.listPages=async()=>{throw Error('disconnected')};
 r=await listTargets([win('b1')],ext,'session');assert.equal(r.pages.length,1);assert.match(r.warning,/disconnected/);
 ext.isRunning=()=>false;r=await listTargets([win('b1')],ext,'session');assert.equal(r.warning,'');
 console.log('PASS all engines, popup targets, closed removal, partial connection failure');
})().catch(e=>{console.error(e);process.exitCode=1});
