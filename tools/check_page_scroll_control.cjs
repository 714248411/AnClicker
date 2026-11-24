const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const ctx={window:{yingdao:{browser:{}}},setTimeout};vm.runInNewContext(fs.readFileSync('integrations/yingdao/src/engine.js','utf8'),ctx);
const e=ctx.window.Engine;
const elem={scrollTop:0,scrollLeft:0,scrollHeight:3000,clientHeight:600,scrollTo(p){this.scrollTop=p.top}};
const page={document:{scrollingElement:elem,readyState:'complete',title:'fixture'},location:{href:'https://example.test'}};
e.execJS=async s=>vm.runInNewContext(s,page);e.sleepInterruptible=async()=>{};
(async()=>{
 for(const [position,ratio] of [['顶部',0],['中间',.5],['底部',1]]){
  const s=await e.runCommand({id:'scrollPageToPosition',params:{position}});
  assert.equal(elem.scrollTop,(elem.scrollHeight-elem.clientHeight)*ratio);
 }
 let ticks=0;e.sleepInterruptible=async()=>{if(++ticks===2)elem.scrollHeight=5000};
 await e.scrollPageToPosition({position:'中间'});assert.equal(elem.scrollTop,2200);
 elem.scrollHeight=600;await e.scrollPageToPosition({position:'底部'});assert.equal(elem.scrollTop,0);
 await assert.rejects(e.scrollPageToPosition({position:'unknown'}));
 e.cancel();await assert.rejects(e.scrollPageToPosition({position:'中间'}),/RPA_STOP/);
 console.log('PASS page destinations, dynamic height, short page, invalid position, cancellation');
})().catch(e=>{console.error(e);process.exitCode=1});
