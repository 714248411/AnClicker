const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const calls=[],waits=[];
const ctx={window:{yingdao:{browser:{backgroundInput:async(k,s)=>calls.push(s)}}}};
vm.runInNewContext(fs.readFileSync('integrations/yingdao/src/engine.js','utf8'),ctx);
const engine=ctx.window.Engine;
engine.sleepInterruptible=async n=>waits.push(n);
const run=p=>engine.runCommand({id:'backgroundKey',params:{browserWindow:{remote:true},key:'自定义',...p}});
(async()=>{
 await run({customKey:'aaaaa'});assert.equal(calls.map(s=>s.key).join(''),'aaaaa');assert.deepEqual(waits,[.1,.1,.1,.1]);
 calls.length=waits.length=0;await run({customKey:'ab',times:2,interval:0});assert.equal(calls.map(s=>s.key).join(''),'abab');assert.deepEqual(waits,[0,0,0]);
 calls.length=waits.length=0;await run({customKey:'Ctrl+Shift+A'});assert.equal(calls.length,1);assert.equal(calls[0].modifiers.join(','),'control,shift');assert.equal(waits.length,0);
 calls.length=0;await run({customKey:'F5'});assert.equal(calls.length,1);assert.equal(calls[0].key,'F5');
 await assert.rejects(run({customKey:'abc',interval:-1}),/间隔/);
 for(const times of [0,-1,21,1.5,Infinity])await assert.rejects(run({customKey:'a',times}),/按几次/);
 for(const text of ['+','a+b',' a ','😀']){calls.length=waits.length=0;await run({customKey:text});assert.equal(calls.map(s=>s.key).join(''),text);assert.equal(calls.length,Array.from(text).length);}
 for(const [text,key] of [['f5','F5'],['enter','Enter'],['Return','Enter'],['ESC','Escape']]){calls.length=0;await run({customKey:text});assert.equal(calls.length,1);assert.equal(calls[0].key,key);}
 calls.length=0;await run({customKey:'Ctrl++'});assert.equal(calls[0].key,'+');assert.equal(calls[0].modifiers[0],'control');
 await assert.rejects(run({customKey:'Ctrl+'}),/组合键/);await assert.rejects(run({customKey:''}),/字符/);
 calls.length=0;await run({key:undefined});assert.equal(calls[0].key,'Enter');
 calls.length=0;engine.sleepInterruptible=async()=>engine.cancel();await assert.rejects(run({customKey:'abc'}),/RPA_STOP/);assert.equal(calls.length,1);
 console.log('PASS sequence order, default/custom intervals, repeated sequences, shortcuts, function keys and cancellation');
})().catch(e=>{console.error(e);process.exitCode=1});
