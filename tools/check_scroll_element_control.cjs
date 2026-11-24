const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const ctx={window:{yingdao:{browser:{}}},setTimeout};vm.runInNewContext(fs.readFileSync('integrations/yingdao/src/engine.js','utf8'),ctx);
const e=ctx.window.Engine, calls=[];let count=0;
e.locatorSnippet=()=> 'null';e.execJSAny=async code=>{calls.push(code);return {x:200,y:250,width:100,height:100,viewportWidth:600,viewportHeight:600}};
(async()=>{
 for (const p of [{selector:''},{selector:'a',timeout:-1},{selector:'a',timeout:Infinity},{selector:'a',settle:31},{selector:'a',behavior:'bogus'},{selector:'a',by:'坐标定位'},{selector:'a',by:'锚点定位'}])await assert.rejects(e.scrollElementToCenter(p));
 e.sleepInterruptible=async()=>{e.cancel();throw new Error('RPA_STOP')};
 await assert.rejects(e.scrollElementToCenter({selector:'a',by:'文本内容'}),/RPA_STOP/);
 assert(calls.some(x=>x.includes('behavior:"instant"')&&x.includes('scrollLeft')),'cancellation freezes animation');
 e.resetCancel();e.sleepInterruptible=async()=>{};calls.length=0;
 await e.runCommand({id:'scrollElementToCenter',params:{selector:'a',by:'文本内容',settle:0}});
 assert(!calls.some(x=>x.includes('.click(')));
 console.log('PASS invalid settings, cancellation freezes animation, dispatch and no click side effects');
})().catch(x=>{console.error(x);process.exitCode=1});
